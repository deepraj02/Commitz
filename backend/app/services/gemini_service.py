import google.generativeai as genai
from typing import List, Dict, Optional, Any, Tuple
import json
import asyncio
from functools import lru_cache
import hashlib
from collections import defaultdict
import aiohttp
import redis
from datetime import timedelta
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
import asyncio.exceptions
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self, api_key: str, redis_url: str = "redis://localhost:6379"):
        logger.info("Initializing GeminiService")
        genai.configure(api_key=api_key)
        try:
            preferred_models = [
                'gemini-1.5-flash', # Prioritize faster model first
                'gemini-1.5-pro',
                'gemini-pro', 
            ]
            available_models = {model.name: model for model in genai.list_models()}
            logger.info(f"Available models: {list(available_models.keys())}")
            model_name = None
            for preferred in preferred_models:
                for available in available_models:
                    if preferred in available.lower():
                        model_name = available
                        break
                if (model_name):
                    break
                    
            if not model_name:
                raise ValueError("No suitable Gemini model found")
                
            self.model = genai.GenerativeModel(model_name=model_name)
            logger.info(f"Successfully initialized model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise

        # Optimize generation config for faster responses
        self.generation_config = {
            "temperature": 0.6,  # Lower temperature for more focused responses
            "top_p": 0.95,
            "top_k": 20,
            "max_output_tokens": 1024,  # Reduced token count
        }
        
        # Ultra fast model configuration for emergency fallback
        self.fast_generation_config = {
            "temperature": 0.4,  # Even more focused
            "top_p": 0.85,
            "top_k": 10,
            "max_output_tokens": 512,  # Significantly reduced for speed
        }
        
        try:
            logger.info(f"Connecting to Redis at {redis_url}")
            self.redis_client = redis.from_url(redis_url)
            # Test Redis connection
            self.redis_client.ping()
            logger.info("Redis connection successful")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}", exc_info=True)
            # Create a fallback to allow the service to work without Redis
            self.redis_client = None
            logger.warning("Operating without Redis cache")
            
        # Aggressive concurrency settings
        self.chunk_semaphore = asyncio.Semaphore(5)  # Increased to 5 concurrent requests
        self.retry_semaphore = asyncio.Semaphore(3)  # More parallel retries
        self.thread_pool = ThreadPoolExecutor(max_workers=10)  # Increased thread pool
        self.cache_ttl = timedelta(days=7)  # Cache videos for 7 days
        self.request_interval = 0.5  # Reduced interval between requests
        self.last_request_time = 0
        self.max_retries = 2  # Reduced retry count for faster failure
        self.base_wait = 1
        self.max_wait = 5  # Reduced wait time
        self.rate_limited = False  # Track rate limit state
        self.adaptable_chunk_size = 250  # Smaller chunks for faster processing
        self.request_timeout = 8  # Much shorter timeout
        self.max_processing_time = 40  # Max time for full processing before returning partial results
        self.min_issues_to_return = 3  # Return results if we have at least this many issues
        logger.info("GeminiService initialized successfully")
        
    def _cache_key(self, text: str) -> str:
        return f"gemini:{hashlib.md5(text.encode()).hexdigest()}"

    def _video_cache_key(self, video_id: str) -> str:
        return f"video:{video_id}:issues"
    
    def _video_partial_cache_key(self, video_id: str) -> str:
        return f"video:{video_id}:partial_issues"
        
    async def get_cached_video_issues(self, video_id: str) -> Optional[dict]:
        if not self.redis_client:
            return None
            
        try:
            cached = self.redis_client.get(self._video_cache_key(video_id))
            if cached:
                logger.info(f"Cache hit for video {video_id}")
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Redis error reading video cache: {str(e)}")
        return None
    
    async def get_partial_cached_issues(self, video_id: str) -> Optional[dict]:
        """Get partially completed issues for a video"""
        if not self.redis_client:
            return None
            
        try:
            cached = self.redis_client.get(self._video_partial_cache_key(video_id))
            if cached:
                logger.info(f"Partial cache hit for video {video_id}")
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Redis error reading partial cache: {str(e)}")
        return None
        
    async def cache_video_issues(self, video_id: str, issues: dict):
        if not self.redis_client:
            return
            
        try:
            self.redis_client.setex(
                self._video_cache_key(video_id),
                self.cache_ttl,
                json.dumps(issues)
            )
            logger.info(f"Cached issues for video {video_id}")
        except Exception as e:
            logger.error(f"Redis error caching video: {str(e)}")
    
    async def cache_partial_issues(self, video_id: str, issues: dict, ttl: int = 1800):
        """Cache partially processed issues with shorter TTL"""
        if not self.redis_client:
            return
            
        try:
            self.redis_client.setex(
                self._video_partial_cache_key(video_id),
                ttl,  # 30 minutes default
                json.dumps(issues)
            )
            logger.info(f"Cached partial results for video {video_id}")
        except Exception as e:
            logger.error(f"Redis error caching partial results: {str(e)}")

    def _chunk_transcript(self, transcript: str) -> List[str]:
        """Create smaller chunks for faster processing"""
        logger.info(f"Chunking transcript of length {len(transcript)}")
        words = transcript.split()
        total_words = len(words)
        if total_words < 1000:
            chunk_size = 150  # Very small chunks for short transcripts
        elif total_words < 3000:
            chunk_size = 200  # Small chunks
        else:
            chunk_size = self.adaptable_chunk_size
            
        overlap = max(20, chunk_size // 15)  # Reduced overlap
        
        chunks = []
        # Create smaller chunks with less overlap
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
            
        # Take a strategic sample if there are too many chunks
        if len(chunks) > 8:
            sampled_chunks = []
            # Take first chunk
            sampled_chunks.append(chunks[0])
            
            # Take last chunk
            sampled_chunks.append(chunks[-1])
            
            # Take middle chunk
            middle = len(chunks) // 2
            sampled_chunks.append(chunks[middle])
            
            # Take quarter points
            quarter = len(chunks) // 4
            sampled_chunks.append(chunks[quarter])
            sampled_chunks.append(chunks[3*quarter])
            
            # Take a few random samples from the rest
            import random
            remaining_indices = [i for i in range(len(chunks)) if i not in [0, middle, -1, quarter, 3*quarter]]
            random.shuffle(remaining_indices)
            for idx in remaining_indices[:3]:  # Take 3 random chunks
                sampled_chunks.append(chunks[idx])
                
            chunks = sampled_chunks
            
        logger.info(f"Transcript split into {len(chunks)} chunks with size {chunk_size}")
        return chunks

    async def _wait_for_rate_limit(self):
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.request_interval:
            await asyncio.sleep(self.request_interval - elapsed)
        self.last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(2),  # Maximum 2 retries
        wait=wait_exponential(multiplier=1, min=1, max=3),  # Much faster retry intervals
        retry=retry_if_exception_type((Exception,)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _call_gemini_api(self, prompt: str, fast_mode: bool = False):
        async with self.retry_semaphore:
            await self._wait_for_rate_limit()
            try:
                config = self.fast_generation_config if fast_mode else self.generation_config
                # Use timeout to prevent long-running requests
                response_future = asyncio.create_task(asyncio.to_thread(
                    lambda: self.model.generate_content(
                        prompt,
                        safety_settings=[
                            {
                                "category": "HARM_CATEGORY_HARASSMENT",
                                "threshold": "BLOCK_NONE"
                            },
                            {
                                "category": "HARM_CATEGORY_HATE_SPEECH",
                                "threshold": "BLOCK_NONE"
                            },
                            {
                                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                                "threshold": "BLOCK_NONE"
                            },
                            {
                                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                                "threshold": "BLOCK_NONE"
                            },
                        ],
                        generation_config=config
                    )
                ))
                
                # Add timeout to prevent hanging
                try:
                    response = await asyncio.wait_for(response_future, timeout=self.request_timeout)
                except asyncio.TimeoutError:
                    logger.warning(f"API request timed out after {self.request_timeout}s")
                    self.rate_limited = True
                    raise TimeoutError(f"API request timed out after {self.request_timeout}s")
                    
                if not response or not response.text:
                    raise ValueError("Empty response from Gemini API")
                return response
            except Exception as e:
                if "429" in str(e) or "ResourceExhausted" in str(e) or "quota" in str(e).lower():
                    logger.warning(f"Rate limit hit, increasing wait time")
                    self.rate_limited = True
                    self.request_interval = min(self.request_interval * 1.5, 10.0)
                    await asyncio.sleep(self.request_interval)
                raise

    async def _process_chunk(self, chunk: str, session: aiohttp.ClientSession, fast_mode: bool = False) -> List[dict]:
        cache_key = self._cache_key(chunk)
        cached_result = None
        if self.redis_client:
            try:
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    logger.info(f"Cache hit for key: {cache_key[:10]}...")
                    return json.loads(cached_result)
                logger.info(f"Cache miss for key: {cache_key[:10]}...")
            except Exception as e:
                logger.error(f"Redis error during cache lookup: {str(e)}")
        
        async with self.chunk_semaphore:
            logger.info(f"Processing chunk of size {len(chunk)} characters")
            try:
                # Use the simplified prompt for faster processing
                prompt = self._get_simplified_prompt() if fast_mode else self._get_prompt()
                prompt += chunk
                logger.info("Sending request to Gemini API")
                
                try:
                    response = await self._call_gemini_api(prompt, fast_mode=fast_mode)
                    
                    if not response.text:
                        logger.error("Empty response from Gemini API")
                        return []
                        
                    logger.info("Received response from Gemini API")
                    response_text = self._clean_response(response.text)
                    try:
                        issues = self._parse_response(response_text)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON parsing error: {str(e)}\nResponse: {response_text[:200]}...")
                        # Try to salvage partial response
                        issues = self._salvage_partial_response(response_text)
                    
                except Exception as api_error:
                    logger.error(f"API error: {str(api_error)}")
                    return []
                
                # Cache result if Redis is available
                if issues and self.redis_client:
                    try:
                        self.redis_client.setex(
                            cache_key,
                            timedelta(hours=24),
                            json.dumps(issues)
                        )
                        logger.info(f"Cached {len(issues)} issues for key: {cache_key[:10]}...")
                    except Exception as e:
                        logger.error(f"Redis error during caching: {str(e)}")
                
                return issues
                
            except Exception as e:
                logger.error(f"Chunk processing error: {str(e)}", exc_info=True)
                return []

    def _get_prompt(self) -> str:
        logger.debug("Generating prompt template")
        return """
        You are an expert software development instructor creating PRACTICAL GitHub issues from a video tutorial transcript. Your goal is to create hands-on learning tasks that directly apply concepts from the video.

        For each specific technique or concept in the transcript:
        1. Focus on HANDS-ON tasks that learners can immediately implement
        2. Include EXACT code examples, commands, and steps shown in the video
        3. Make each issue ACTIONABLE with measurable completion criteria
        4. Provide PRECISE implementation steps that follow the exact sequence shown in the video
        5. Include any tool versions, prerequisites, or setup instructions mentioned
        6. Focus on the most PRACTICAL aspects that help build real skills
        7. Make sure issues are directly tied to VIDEO CONTENT, not generic concepts
        8. Include debugging tips and common errors mentioned in the video
        
        Format each issue exactly like this JSON:
        {
            "issues": [
                {
                    "title": "[Specific Implementation Task from Video]",
                    "body": {
                        "description": "Practical context explaining this specific task as shown in the video",
                        "learning_objectives": [
                            "- Specific skill you will gain from completing this task",
                            "- Specific problem this solves in the real world",
                            "- How this connects to the broader project shown in the video"
                        ],
                        "implementation_steps": [
                            "1. Exact setup command from video: `npm install xyz`",
                            "2. Precise code to write (with line numbers if shown)",
                            "3. How to verify each step is working",
                            "4. How to test the implementation",
                            "5. Common errors mentioned and how to fix them"
                        ],
                        "expected_outcome": "Specific working feature or component you'll have when complete",
                        "prerequisites": [
                            "Previous video steps that must be completed first",
                            "Exact versions of tools needed as mentioned in video",
                            "Any starting code or setup required"
                        ],
                        "best_practices": [
                            "Specific best practices mentioned in the video",
                            "Why these practices matter according to the instructor"
                        ],
                        "additional_resources": [
                            "Resources explicitly mentioned in the video",
                            "Documentation directly referenced by the instructor"
                        ]
                    },
                    "difficulty": "beginner/intermediate/advanced based on concepts shown",
                    "labels": ["implementation", "hands-on", "video-task"],
                    "related_issues": ["Other task titles in chronological order from video"]
                }
            ]
        }

        CRITICAL GUIDELINES:
        - Issues MUST be tasks that can be implemented by following the video
        - Include EXACT code examples, terminal commands, and file paths from the video
        - Make titles ACTIONABLE: "Implement X" or "Build Y feature" not "Understanding X"
        - Create separate issues for EACH specific implementation task shown
        - Follow the SAME ORDER as the video presents tasks
        - Include EXACT error messages or debugging tips mentioned
        - Focus on PRACTICAL skills not theoretical concepts
        - Ensure issues follow a logical SEQUENCE to build the complete project
        - Make each issue INDEPENDENTLY verifiable upon completion

        Analyze this transcript segment and create practical, hands-on learning issues:
        """

    def _get_simplified_prompt(self) -> str:
        """Return a simplified prompt for faster processing that still focuses on practical tasks"""
        return """
        As a coding instructor, create practical GitHub issues from this video tutorial transcript.
        Focus on:
        1. Hands-on tasks shown in the video
        2. Exact code examples and commands used
        3. Steps that build working features
        4. Practical implementation, not theory
        
        Format as JSON:
        {
            "issues": [
                {
                    "title": "[Specific Implementation Task]",
                    "body": {
                        "description": "What you'll build",
                        "learning_objectives": ["Practical skill gained"],
                        "implementation_steps": ["1. Exact step with code", "2. Next step"],
                        "expected_outcome": "Working feature you'll have",
                        "prerequisites": ["Required previous steps"]
                    },
                    "difficulty": "beginner/intermediate/advanced",
                    "labels": ["implementation"],
                    "related_issues": []
                }
            ]
        }
        
        Extract practical tasks from this transcript:
        """

    def _clean_response(self, response_text: str) -> str:
        logger.debug(f"Cleaning response of length {len(response_text)}")
        if '```json' in response_text:
            logger.debug("Found JSON code block, extracting content")
            response_text = response_text.split('```json')[1].split('```')[0]
        return response_text.strip()

    def _parse_response(self, response_text: str) -> List[dict]:
        logger.debug(f"Parsing JSON response of length {len(response_text)}")
        try:
            parsed = json.loads(response_text)
            issues = parsed.get('issues', [])
            logger.debug(f"Successfully parsed {len(issues)} issues")
            return issues
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.debug(f"Response text that failed to parse: {response_text[:100]}...")
            return []

    def _salvage_partial_response(self, text: str) -> List[dict]:
        """Attempt to salvage partial JSON responses"""
        try:
            # Find complete issue objects
            issues = []
            current_issue = ""
            brace_count = 0
            
            for char in text:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                
                current_issue += char
                
                if brace_count == 0 and current_issue.strip():
                    try:
                        issue = json.loads(current_issue)
                        if isinstance(issue, dict) and 'title' in issue:
                            issues.append(issue)
                    except:
                        pass
                    current_issue = ""
            
            return issues
        except:
            return []

    async def process_transcript(self, transcript: str, video_id: str = None) -> dict:
        logger.info(f"Processing transcript of length {len(transcript)}")
        
        # Try to get cached result first
        if video_id:
            cached_result = await self.get_cached_video_issues(video_id)
            if cached_result and cached_result.get('issues'):
                # Ensure cached results only contain title and description
                cleaned_issues = []
                for issue in cached_result['issues']:
                    cleaned_issues.append({
                        "title": issue.get('title', ''),
                        "description": issue.get('description', '')
                    })
                logger.info(f"Found {len(cleaned_issues)} cached issues")
                return {
                    "issues": cleaned_issues,
                    "total_count": len(cleaned_issues),
                    "cached": True
                }
                
            # Check for partial cached results
            partial_cached = await self.get_partial_cached_issues(video_id)
            if partial_cached and partial_cached.get('issues') and len(partial_cached.get('issues', [])) >= self.min_issues_to_return:
                # Ensure partial cached results only contain title and description
                cleaned_issues = []
                for issue in partial_cached['issues']:
                    cleaned_issues.append({
                        "title": issue.get('title', ''),
                        "description": issue.get('description', '')
                    })
                logger.info(f"Found {len(cleaned_issues)} partially cached issues")
                return {
                    "issues": cleaned_issues,
                    "total_count": len(cleaned_issues),
                    "partial": True,
                    "cached": True
                }

        chunks = self._chunk_transcript(transcript)
        all_issues = []
        processed_chunks = 0
        
        # Use a timeout to ensure we return in under a minute
        start_time = time.time()
        timeout_hit = False
        
        # Process more chunks in parallel for speed
        tasks = []
        
        async with aiohttp.ClientSession() as session:
            # First try with regular processing
            fast_mode = False
            
            # Process chunks in parallel
            for chunk in chunks:
                # Create a task for each chunk
                task = asyncio.create_task(self._process_chunk(chunk, session, fast_mode))
                tasks.append(task)
            
            # Wait for all tasks to complete or until timeout
            pending = set(tasks)
            while pending and not timeout_hit:
                # Check if we're approaching the time limit
                elapsed = time.time() - start_time
                if elapsed > self.max_processing_time:
                    logger.warning(f"Approaching timeout after {elapsed:.2f}s, returning partial results")
                    timeout_hit = True
                    break
                    
                # Wait for some tasks to complete with a short timeout
                remaining_time = max(1, self.max_processing_time - elapsed)
                done, pending = await asyncio.wait(
                    pending, 
                    timeout=min(2.0, remaining_time),  # Short wait time
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process completed tasks
                for task in done:
                    try:
                        result = task.result()
                        if result:
                            all_issues.extend(result)
                            processed_chunks += 1
                            
                            # Cache partial results early if we have enough issues
                            if video_id and len(all_issues) >= self.min_issues_to_return:
                                unique_issues = self._deduplicate_issues(all_issues)
                                partial_result = {
                                    "issues": list(unique_issues.values()),
                                    "total_count": len(unique_issues),
                                    "cached": False,
                                    "partial": True,
                                    "processed_chunks": processed_chunks,
                                    "total_chunks": len(chunks)
                                }
                                await self.cache_partial_issues(video_id, partial_result)
                    except Exception as e:
                        logger.error(f"Error processing task result: {str(e)}")
                        
                # Check if we have enough issues to return early
                if len(all_issues) >= self.min_issues_to_return * 3:  # If we have plenty of issues
                    logger.info(f"Got enough issues ({len(all_issues)}), returning early")
                    break
            
            # Cancel pending tasks if timeout hit
            if pending and timeout_hit:
                logger.warning(f"Timeout hit, cancelling {len(pending)} pending tasks")
                for task in pending:
                    task.cancel()

        logger.info(f"Total issues before deduplication: {len(all_issues)}")
        
        # If we have too few issues and hit timeout, try faster mode on remaining chunks
        if len(all_issues) < self.min_issues_to_return and timeout_hit and video_id:
            # Try to get partial cached results as a fallback
            partial_cached = await self.get_partial_cached_issues(video_id)
            if partial_cached and partial_cached.get('issues') and len(partial_cached.get('issues', [])) >= self.min_issues_to_return:
                # Ensure partial cached results only contain title and description
                cleaned_issues = []
                for issue in partial_cached['issues']:
                    cleaned_issues.append({
                        "title": issue.get('title', ''),
                        "description": issue.get('description', '')
                    })
                logger.info(f"Using {len(cleaned_issues)} partially cached issues as fallback")
                return {
                    "issues": cleaned_issues,
                    "total_count": len(cleaned_issues),
                    "partial": True,
                    "cached": True
                }
                
            logger.warning("Too few issues and timeout hit, trying emergency mode")
            unique_issues = self._generate_emergency_issues(transcript)
            result = {
                "issues": list(unique_issues.values()),
                "total_count": len(unique_issues),
                "cached": False,
                "emergency": True
            }
            
            # Cache these emergency results
            if result["issues"]:
                await self.cache_partial_issues(video_id, result)
                
            return result
        
        if not all_issues:
            logger.warning("No issues were generated from the transcript")
            return {"issues": [], "total_count": 0, "cached": False}

        unique_issues = self._deduplicate_issues(all_issues)
        
        # Enhance the completeness of issues
        try:
            from services.issue_completeness import IssueCompletenessService
            completeness_service = IssueCompletenessService()
            
            # Get the current issues list
            issues_list = list(unique_issues.values())
            
            # Ensure all required technical categories are covered
            enhanced_issues = completeness_service.ensure_required_categories(issues_list, transcript)
            
            # Calculate coverage metrics
            coverage_analysis = completeness_service.analyze_topic_coverage(transcript, enhanced_issues)
            
            # If still missing important topics, try to fill the gaps
            if coverage_analysis["coverage_score"] < 85.0:  # Less than 85% coverage
                logger.info(f"Improving coverage from {coverage_analysis['coverage_score']:.1f}%")
                enhanced_issues = completeness_service.enhance_issues_list(
                    enhanced_issues, 
                    coverage_analysis["missing_topics"], 
                    transcript
                )
            
            # Rebuild the unique_issues dictionary
            unique_issues = {issue["title"]: issue for issue in enhanced_issues}
            
            logger.info(f"Enhanced issues list from {len(issues_list)} to {len(unique_issues)} items")
        except Exception as e:
            logger.error(f"Error enhancing issue completeness: {str(e)}")
        
        # Build the final simplified result
        final_issues = []
        for title, issue in unique_issues.items():
            final_issues.append({
                "title": title,
                "description": issue.get("description", "")
            })
        
        result = {
            "issues": final_issues,
            "total_count": len(final_issues),
            "cached": False,
            "partial": timeout_hit,
            "processed_chunks": processed_chunks,
            "total_chunks": len(chunks)
        }

        # Cache results
        if video_id and result["issues"]:
            if timeout_hit:
                await self.cache_partial_issues(video_id, result)
                logger.info(f"Cached {len(result['issues'])} partial issues for video {video_id}")
            else:
                await self.cache_video_issues(video_id, result)
                logger.info(f"Cached {len(result['issues'])} complete issues for video {video_id}")

        return result
    
    def _generate_emergency_issues(self, transcript: str) -> Dict[str, dict]:
        """Generate practical issues when other methods fail"""
        logger.info("Generating emergency issues from transcript")
        
        try:
            # Extract potential topics by looking for keywords and patterns
            unique_issues = {}
            
            # Extract potential code blocks (content between backticks or indented blocks)
            import re
            code_blocks = re.findall(r'```[\s\S]*?```|`[\s\S]*?`', transcript)
            code_examples = [block.strip('`').strip() for block in code_blocks]
            
            # Find common implementation terms
            implementation_terms = [
                "implement", "create", "build", "setup", "install", "configure",
                "deploy", "develop", "code", "program", "write", "add", "define",
                "initialize", "start", "run", "execute", "test", "debug", "fix"
            ]
            
            # Extract sentences containing implementation instructions
            sentences = re.split(r'[.!?]', transcript)
            implementation_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and any(term.lower() in sentence.lower() for term in implementation_terms):
                    implementation_sentences.append(sentence)
            
            # Create issues from code examples
            if code_examples:
                for i, code in enumerate(code_examples[:3]):  # Limit to first 3 code examples
                    title = f"Implement code feature {i+1} from the video"
                    unique_issues[title] = {
                        "title": title,
                        "description": f"""
## Implementation
```
{code[:200]}...
```

Implement this specific code example shown in the tutorial video.

### Learning Objectives
- Implement this exact code pattern from the video

### Implementation Steps
1. Create the necessary file structure
2. Copy and implement this exact code as shown in the video
3. Test that it works as demonstrated in the tutorial

### Difficulty
intermediate

### Labels
implementation, hands-on
"""
                    }
            
            # Create issues from implementation sentences
            topics = set()
            for sentence in implementation_sentences[:5]:  # Limit to first 5 implementation sentences
                words = sentence.split()
                if len(words) > 3:
                    potential_title = "Implement: " + " ".join(words[:4]) + "..."
                    topics.add(potential_title)
            
            # Add implementation-based issues
            for topic in topics:
                relevant_sentence = next((s for s in implementation_sentences if topic[11:20] in s), implementation_sentences[0])
                unique_issues[topic] = {
                    "title": topic,
                    "description": f"""
## Practical Task
Implement this specific feature from the tutorial:

> {relevant_sentence}

Follow the video instructions exactly to complete this task.

### Learning Objectives
- Build this specific feature as shown in the video

### Implementation Steps
1. Follow the step-by-step instructions in the video
2. Implement the feature exactly as demonstrated
3. Test to make sure it works as shown

### Difficulty
intermediate

### Labels
implementation, hands-on
"""
                }
                
            # Create a project-based issue if we have nothing else
            if not unique_issues:
                unique_issues["Build the project shown in the tutorial"] = {
                    "title": "Build the project shown in the tutorial",
                    "description": """
## Complete Project Implementation
Follow the tutorial to build the complete working project as demonstrated in the video.

### Learning Objectives
- Build a fully functional version of the project shown

### Implementation Steps
1. Watch the full tutorial
2. Follow each implementation step in sequence
3. Test your implementation against the expected outcome

### Difficulty
intermediate

### Labels
project, implementation
"""
                }
                
            return unique_issues
            
        except Exception as e:
            logger.error(f"Error generating emergency issues: {str(e)}")
            # Return at least one practical issue as absolute fallback
            return {
                "Implement the tutorial project": {
                    "title": "Implement the tutorial project",
                    "description": """
## Hands-On Implementation
Build the project demonstrated in the tutorial video by following each step shown.

### Learning Objectives
- Complete a working implementation of the project

### Implementation Steps
- Follow the video step-by-step
- Test each component as you build it

### Difficulty
intermediate

### Labels
implementation, hands-on
"""
                }
            }

    def _deduplicate_issues(self, issues: List[dict]) -> Dict[str, dict]:
        unique_issues = {}
        for issue in issues:
            title = issue.get('title', '')
            if title and title not in unique_issues:
                # Include only title and description fields
                unique_issues[title] = {
                    "title": title,
                    "description": self._format_description(issue)
                }
        return unique_issues

    def _format_description(self, issue: dict) -> str:
        logger.debug(f"Formatting description for issue: {issue.get('title', 'Untitled')}")
        body = issue.get('body', {})
        
        # Create a comprehensive markdown description that includes all information
        description = f"""
## Overview
{body.get('description', '')}

### Learning Objectives
{chr(10).join(body.get('learning_objectives', []))}

### Implementation Steps
{chr(10).join(body.get('implementation_steps', []))}

### Expected Outcome
{body.get('expected_outcome', '')}

### Difficulty
{issue.get('difficulty', 'intermediate')}

### Prerequisites
{chr(10).join(body.get('prerequisites', []))}

### Best Practices
{chr(10).join(body.get('best_practices', []))}

### Additional Resources
{chr(10).join(body.get('additional_resources', []))}

### Labels
{', '.join(issue.get('labels', ["learning"]))}
        """.strip()
        
        return description