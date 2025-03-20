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

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self, api_key: str):
        configure(api_key=api_key)
        self.model = self._initialize_model()
        self.completeness_service = IssueCompletenessService()
        self.semaphore = asyncio.Semaphore(5)
        self.cache_ttl = 60480

    def _initialize_model(self) -> GenerativeModel:
        self.model = GenerativeModel('gemini-2.0-flash')
        self.generation_config = {
            "temperature": 0.5,  
            "top_p": 0.95,
            "top_k": 20,
            "max_output_tokens": 1024,
        }
        return self.model

    # def _initialize_redis(self, redis_url: str) -> Optional[redis.Redis]:
    #     try:
    #         client = redis.from_url(redis_url)
    #         asyncio.run(client.ping())
    #         logger.info("Redis connected")
    #         return client
    #     except Exception as e:
    #         logger.warning(f"Redis connection failed: {e}, proceeding without cache")
    #         return None

    # async def get_cached_result(self, video_id: str) -> Optional[Dict]:
    #     if not self.redis_client:
    #         return None
    #     cache_key = f"video:{video_id}"
    #     try:
    #         cached = await self.redis_client.get(cache_key)
    #         if cached:
    #             logger.info(f"Cache hit for {video_id}")
    #             return json.loads(cached)
    #     except Exception as e:
    #         logger.error(f"Cache retrieval error: {e}")
    #     return None

    # async def cache_result(self, video_id: str, result: Dict):
    #     if self.redis_client:
    #         cache_key = f"video:{video_id}"
    #         try:
    #             await self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(result))
    #             logger.info(f"Cached result for {video_id}")
    #         except Exception as e:
    #             logger.error(f"Cache store error: {e}")

    def _chunk_transcript(self, transcript: str) -> List[str]:
        words = transcript.split()
        chunk_size = 250 if len(words) > 3000 else 200 if len(words) > 1000 else 150
        chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size - 20)]
        logger.info(f"Split into {len(chunks)} chunks")
        return chunks

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5), retry=retry_if_exception_type(Exception))
    async def _call_gemini(self, prompt: str) -> GenerateContentResponse:
        async with self.semaphore:
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    prompt,
                    safety_settings=[{"category": category, "threshold": "BLOCK_NONE"} for category in [
                        "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
                        "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"
                    ]]
                )
                if not response.text:
                    raise ValueError("Empty response")
                return response
            except Exception as e:
                logger.error(f"Gemini API error: {e}")
                raise

    async def _process_chunk(self, chunk: str, session: aiohttp.ClientSession) -> List[Dict]:
        prompt = self._get_issue_prompt() + chunk
        try:
            response = await self._call_gemini(prompt)
            issues = json.loads(response.text.split('```json')[1].split('```')[0])["issues"]
            return [self._standardize_issue(issue) for issue in issues]
        except Exception as e:
            logger.error(f"Chunk processing error: {e}")
            return []

    def _get_issue_prompt(self) -> str:
        return """
        Create practical GitHub issues from this transcript segment:
        - Focus on hands-on tasks with exact code/commands from the video.
        - Ensure each issue is actionable and verifiable.
        - Format as JSON:
        {
            "issues": [
                {
                    "title": "Implement [Task]",
                    "description": "Details in Markdown\\n\\n## Steps\\n1. [Step]\\n2. [Step]\\n\\n**Difficulty**: [level]\\n**Labels**: [label1, label2]"
                }
            ]
        }
        """

    def _standardize_issue(self, issue: Dict) -> Dict:

        body = issue.get("body", {}) if isinstance(issue.get("body"), dict) else {}
        base_description = body.get("description", issue.get("description", "No description provided"))

        difficulty = issue.get("difficulty", "intermediate")
        labels = ", ".join(issue.get("labels", ["implementation"]))
        steps = "\n".join([f"{i+1}. {step}" for i, step in enumerate(body.get("implementation_steps", []))]) if body.get("implementation_steps") else "No steps provided"

        full_description = f"{base_description}\n\n## Steps\n{steps}\n\n**Difficulty**: {difficulty}\n**Labels**: [{labels}]"

        return {
            "title": issue.get("title", "Unnamed Task"),
            "description": full_description.strip()
        }

    async def process_transcript(self, transcript: str, video_id: str) -> Dict:
        # cached = await self.get_cached_result(video_id)
        # if cached:
        #     return cached

        chunks = self._chunk_transcript(transcript)
        async with aiohttp.ClientSession() as session:
            tasks = [self._process_chunk(chunk, session) for chunk in chunks]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        all_issues = []
        for result in results:
            if isinstance(result, list):
                all_issues.extend(result)

        unique_issues = {issue["title"]: issue for issue in all_issues}
        enhanced_issues = self.completeness_service.ensure_completeness(list(unique_issues.values()), transcript)
        result = {"issues": enhanced_issues, "total_count": len(enhanced_issues)}

        # await self.cache_result(video_id, result)
        return result