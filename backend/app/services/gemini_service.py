import json
import logging
import asyncio
import aiohttp
from typing import List, Dict, Optional
from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel
from google.generativeai.types import GenerateContentResponse
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from services.issue_completeness import IssueCompletenessService
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self, api_key: str, redis_url: str = "redis://localhost:6379"):
        configure(api_key=api_key)
        self.model = self._initialize_model()
        self.completeness_service = IssueCompletenessService()
        self.semaphore = asyncio.Semaphore(5)
        self.cache_ttl = 60480
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)

    def _initialize_model(self) -> GenerativeModel:
        self.model = GenerativeModel('gemini-2.0-flash')
        self.generation_config = {
            "temperature": 0.3,  
            "top_p": 0.85,       
            "top_k": 40,         
            "max_output_tokens": 4000,  
        }
        return self.model

    def _chunk_transcript(self, transcript: str) -> List[str]:
        words = transcript.split()
        chunk_size = 600 if len(words) > 3000 else 400 if len(words) > 1000 else 200  
        chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size - 100)]
        logger.info(f"Split into {len(chunks)} chunks")
        return chunks

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(min=2, max=30),retry=  retry_if_exception_type(Exception))
    async def _call_gemini(self, prompt: str) -> GenerateContentResponse:
        async with self.semaphore:
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    prompt,
                    safety_settings=[{"category": category, "threshold": "BLOCK_NONE"} for category in [
                        "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
                        "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"
                    ]],
                )
                if not response.text:
                    raise ValueError("Empty response")
                logger.debug(f"Raw Gemini response: {response.text[:200]}...")  
                return response
            except Exception as e:
                logger.error(f"Gemini API error: {e}")
                raise

    async def _process_chunk(self, chunk: str, session: aiohttp.ClientSession) -> List[Dict]:
        prompt = self._get_issue_prompt() + chunk
        all_issues = []
        
        for attempt in range(3):  
            try:
                response = await self._call_gemini(prompt)
                text = response.text.strip()
                logger.debug(f"Attempt {attempt + 1} response: {text[:200]}...")

                if '```json' not in text or '```' not in text.split('```json')[1]:
                    logger.warning(f"Invalid JSON format in attempt {attempt + 1}")
                    prompt += f"\n\nAttempt {attempt + 1} failed due to missing JSON markers. Provide valid JSON wrapped in ```json``` markers."
                    continue

                json_str = text.split('```json')[1].split('```')[0].strip()
                try:
                    data = json.loads(json_str)
                    issues = data.get("issues", [])
                    if not issues:
                        logger.warning(f"No issues found in attempt {attempt + 1}")
                    all_issues.extend([self._standardize_issue(issue) for issue in issues if issue])
                    if all_issues:
                        break 
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing failed in attempt {attempt + 1}: {e}. Raw: {json_str[:200]}...")
                    
                    partial_issues = self._fix_partial_json(json_str, chunk)
                    if partial_issues:
                        all_issues.extend(partial_issues)
                        break
                    prompt += f"\n\nPrevious response had JSON error: {str(e)}. Ensure complete, valid JSON with all objects closed."
                    continue
            except Exception as e:
                logger.error(f"Chunk processing error in attempt {attempt + 1}: {e}")
                prompt += f"\n\nAttempt {attempt + 1} failed: {str(e)}. Retry with valid JSON."
        if not all_issues:
            logger.warning(f"All attempts failed for chunk: {chunk[:100]}...")
           

        return all_issues

    def _fix_partial_json(self, json_str: str, chunk: str) -> List[Dict]:
        """Attempt to extract partial issues from malformed JSON."""
        issues = []
        try:
            
            lines = json_str.split('\n')
            current_issue = {}
            for line in lines:
                line = line.strip()
                if line.startswith('{"title":'):
                    if current_issue:
                        issues.append(self._standardize_issue(current_issue))
                    current_issue = {}
                if '"title":' in line:
                    current_issue["title"] = line.split('"title":')[1].split('"')[1]
                elif '"description":' in line:
                    current_issue["description"] = line.split('"description":')[1].split('"')[1]
                elif '"difficulty":' in line:
                    current_issue["difficulty"] = line.split('"difficulty":')[1].split('"')[1]
                elif '"labels":' in line:
                    labels = line.split('"labels":')[1].strip('[]').split(',')
                    current_issue["labels"] = [label.strip().strip('"') for label in labels]
            if current_issue:
                issues.append(self._standardize_issue(current_issue))
        except Exception as e:
            logger.error(f"Salvage attempt failed: {e}")
        if not issues:
            logger.info("No partial issues salvaged, falling back to chunk-based issue")
            
        return issues


    def _get_issue_prompt(self) -> str:
        return """
        Analyze this transcript segment and create detailed, practical GitHub issues:
        - Identify specific, hands-on tasks with exact code/commands from the transcript.
        - Ensure each issue is actionable, verifiable, and includes clear, detailed steps.
        - Avoid generic or vague issues; use concrete examples and context from the transcript.
        - Provide complete, well-formed JSON objects with no truncated content.
        - Only include valid, relevant issues for programming tasks or concepts.
        - Format as valid JSON wrapped in ```json``` markers:
        ```json
        {
            "issues": [
                {
                    "title": "Implement [Specific Task]",
                    "description": "Detailed description in Markdown\\n\\n## Steps\\n1. [Specific Step]\\n2. [Specific Step]\\n\\n**Difficulty**: [beginner/intermediate/advanced]\\n**Labels**: [label1, label2]"
                }
            ]
        }
        ```
        """

    def _standardize_issue(self, issue: Dict) -> Dict:
        body = issue.get("body", {}) if isinstance(issue.get("body"), dict) else {}
        base_description = body.get("description", issue.get("description", "No description provided"))
        
        difficulty = issue.get("difficulty", "intermediate")
        labels = ", ".join(issue.get("labels", ["implementation"]))
        steps = body.get("implementation_steps", []) or issue.get("description", "No steps provided")
        if isinstance(steps, str):
            steps = [steps]
        steps_md = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)]) if steps else "No steps provided"

        full_description = f"{base_description}\n\n## Steps\n{steps_md}\n\n**Difficulty**: {difficulty}\n**Labels**: [{labels}]"
        return {
            "title": issue.get("title", "Unnamed Task"),
            "description": full_description.strip()
        }

    async def process_transcript(self, transcript: str, video_id: str) -> Dict:
        cache_key = f"gemini:video:{video_id}"
        cached_result = await self.redis.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for video_id: {video_id}")
            return json.loads(cached_result)

        chunks = self._chunk_transcript(transcript)
        async with aiohttp.ClientSession() as session:
            tasks = [self._process_chunk(chunk, session) for chunk in chunks]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        all_issues = []
        for i, result in enumerate(results):
            if isinstance(result, list):
                all_issues.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Task {i} failed with exception: {result}")
                

        unique_issues = {issue["title"]: issue for issue in all_issues if issue.get("title")}
        enhanced_issues = self.completeness_service.ensure_completeness(list(unique_issues.values()), transcript)
        result = {"issues": enhanced_issues, "total_count": len(enhanced_issues)}

        try:
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(result))
            logger.info(f"Cached result for video_id: {video_id}")
        except Exception as e:
            logger.error(f"Failed to cache result for video_id: {video_id}: {e}")

        return result

    async def get_cached_result(self, video_id: str) -> Optional[Dict]:
        cache_key = f"gemini:video:{video_id}"
        cached_result = await self.redis.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for video_id: {video_id}")
            return json.loads(cached_result)
        return None

    async def is_redis_connected(self) -> bool:
        try:
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis connection check failed: {e}")
            return False

    async def close(self):
        await self.redis.close()