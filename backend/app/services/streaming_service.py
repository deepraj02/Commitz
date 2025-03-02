import asyncio
import json
import logging
import time
from typing import AsyncGenerator, Dict, List, Optional, Any
import aiohttp
from fastapi import HTTPException

from services.gemini_service import GeminiService
from utils.timeout_handler import TimeoutManager
from services.text_analyzer import TextAnalyzer

logger = logging.getLogger(__name__)

class StreamingService:
    """Service to handle streaming responses with proper timeout handling"""
    
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service
        self.text_analyzer = TextAnalyzer()
        self.max_processing_time = 50  # Maximum processing time in seconds
        self.max_chunk_time = 8  # Maximum time to process a single chunk
        self.min_issues_to_return = 3  # Minimum number of issues to return
        
    async def process_transcript_stream(
        self, 
        transcript: str, 
        video_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Process a transcript and yield streaming updates
        
        Args:
            transcript: The transcript text to process
            video_id: Optional video ID for caching
            
        Yields:
            JSON strings with processing status and results
        """
        timeout_mgr = TimeoutManager(self.max_processing_time)
        if video_id:
            cached_result = await self.gemini_service.get_cached_video_issues(video_id)
            if cached_result and cached_result.get('issues'):
                logger.info(f"Found {len(cached_result['issues'])} cached issues")
                yield json.dumps({
                    "status": "complete",
                    "cached": True,
                    "issues": cached_result["issues"],
                    "total_count": len(cached_result["issues"])
                }) + "\n"
                return
                
            # Check for partial cached results
            partial_cached = await self.gemini_service.get_partial_cached_issues(video_id)
            if partial_cached and partial_cached.get('issues') and len(partial_cached.get('issues', [])) >= self.min_issues_to_return:
                logger.info(f"Found {len(partial_cached['issues'])} partially cached issues")
                partial_cached["cached"] = True
                partial_cached["partial"] = True
                yield json.dumps(partial_cached) + "\n"
                return

        # Chunk the transcript
        chunks = self.gemini_service._chunk_transcript(transcript)
        all_issues = []
        processed_chunks = 0
        
        # If there are too many chunks, we might not be able to process them all in time
        # Create a quick emergency set of issues in the background
        emergency_issues = None
        if len(chunks) > 6:
            logger.info("Many chunks detected, preparing emergency issues in background")
            emergency_task = asyncio.create_task(self._get_emergency_issues(transcript))
        
        # Yield initial status
        yield json.dumps({
            "status": "processing",
            "total_chunks": len(chunks),
            "processed_chunks": 0,
            "progress": 0
        }) + "\n"
        
        # Process chunks with proper timeout handling
        async with aiohttp.ClientSession() as session:
            # Process the first chunk to get some initial issues
            if chunks:
                try:
                    first_chunk_issues = await timeout_mgr.run_with_timeout(
                        self.gemini_service._process_chunk(chunks[0], session),
                        timeout=self.max_chunk_time,
                        fallback_func=lambda: []
                    )
                    
                    if first_chunk_issues:
                        all_issues.extend(first_chunk_issues)
                        processed_chunks += 1
                        # Cache these partial results immediately
                        if video_id:
                            partial_result = {
                                "issues": first_chunk_issues,
                                "total_count": len(first_chunk_issues),
                                "partial": True,
                                "processed_chunks": processed_chunks,
                                "total_chunks": len(chunks)
                            }
                            await self.gemini_service.cache_partial_issues(video_id, partial_result)
                except Exception as e:
                    logger.error(f"Error processing first chunk: {str(e)}")
            
            # Create tasks for remaining chunks
            remaining_chunks = chunks[1:] if len(chunks) > 1 else []
            tasks = [
                asyncio.create_task(self.gemini_service._process_chunk(chunk, session))
                for chunk in remaining_chunks[:5]  # Limit to 5 additional chunks
            ]
            
            # Wait for tasks with progress updates
            while tasks and not timeout_mgr.is_timeout_approaching(buffer=10):
                try:
                    # Wait for the next task to complete or a short timeout
                    done, pending = await asyncio.wait(
                        tasks, 
                        timeout=min(2.0, timeout_mgr.time_remaining()),
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Update tasks list
                    tasks = list(pending)
                    
                    # Process completed tasks
                    for task in done:
                        try:
                            result = task.result()
                            if result:
                                all_issues.extend(result)
                            processed_chunks += 1
                        except Exception as e:
                            logger.error(f"Error processing task: {str(e)}")
                    
                    # Send progress update
                    progress = round((processed_chunks / len(chunks)) * 100, 1)
                    yield json.dumps({
                        "status": "processing",
                        "processed_chunks": processed_chunks,
                        "total_chunks": len(chunks),
                        "progress": progress,
                        "current_issues_count": len(all_issues)
                    }) + "\n"
                    
                    # Cache partial results if we have enough issues
                    if video_id and len(all_issues) >= self.min_issues_to_return:
                        unique_issues = self.gemini_service._deduplicate_issues(all_issues)
                        partial_result = {
                            "issues": list(unique_issues.values()),
                            "total_count": len(unique_issues),
                            "partial": True,
                            "processed_chunks": processed_chunks,
                            "total_chunks": len(chunks)
                        }
                        await self.gemini_service.cache_partial_issues(video_id, partial_result)
                
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout waiting for tasks, {len(tasks)} tasks remaining")
                    break
            
            # Cancel remaining tasks if we're approaching the timeout
            if tasks:
                logger.warning(f"Cancelling {len(tasks)} remaining tasks due to timeout")
                for task in tasks:
                    task.cancel()
        
        # Deduplicate issues
        unique_issues = self.gemini_service._deduplicate_issues(all_issues)
        
        # If we have enough processing time left, enhance completeness
        if timeout_mgr.time_remaining() > 3.0:  # If we have at least 3 seconds left
            try:
                from services.issue_completeness import IssueCompletenessService
                completeness_service = IssueCompletenessService()
                
                # Convert to list for processing
                issues_list = list(unique_issues.values())
                
                # Fast completeness enhancement
                enhanced_issues = completeness_service.ensure_required_categories(issues_list, transcript)
                
                # If still time left, do more comprehensive enhancement
                if timeout_mgr.time_remaining() > 2.0:
                    coverage_analysis = completeness_service.analyze_topic_coverage(transcript, enhanced_issues)
                    
                    if coverage_analysis["coverage_score"] < 80.0:  # Less than 80% coverage
                        most_important_missing = coverage_analysis["missing_topics"][:3]  # Focus on top 3 missing topics
                        enhanced_issues = completeness_service.enhance_issues_list(
                            enhanced_issues,
                            most_important_missing,
                            transcript
                        )
                
                # Update unique_issues from the enhanced list
                unique_issues = {issue["title"]: issue for issue in enhanced_issues}
                
                logger.info(f"Enhanced issues list to {len(unique_issues)} items")
                
                # Add status update about enhancement
                yield json.dumps({
                    "status": "enhancing",
                    "message": "Enhancing issue coverage for completeness",
                    "current_issue_count": len(unique_issues)
                }) + "\n"
                
            except Exception as e:
                logger.error(f"Error enhancing issue completeness: {str(e)}")
        
        # If we have too few issues, try to use emergency issues
        if len(unique_issues) < self.min_issues_to_return:
            try:
                if 'emergency_task' in locals():
                    logger.info("Using emergency issues as fallback")
                    emergency_issues = await emergency_task
                    
                if not emergency_issues:
                    emergency_issues = self.text_analyzer.generate_emergency_issues(transcript)
                    
                if emergency_issues:
                    # Merge emergency issues with any we already have
                    for key, issue in emergency_issues.items():
                        if issue.get('title') and issue['title'] not in unique_issues:
                            unique_issues[issue['title']] = {
                                "title": issue['title'],
                                "description": issue.get('description', ''),
                                "difficulty": issue.get('difficulty', 'intermediate'),
                                "labels": issue.get('labels', ["learning"]),
                                "prerequisites": [],
                                "learning_objectives": issue.get('learning_objectives', []),
                                "implementation_steps": issue.get('implementation_steps', [])
                            }
            except Exception as e:
                logger.error(f"Error adding emergency issues: {str(e)}")
                
        # Create final result
        final_issues = list(unique_issues.values())
        result = {
            "status": "complete",
            "issues": final_issues,
            "total_count": len(final_issues),
            "processed_chunks": processed_chunks,
            "total_chunks": len(chunks),
            "partial": processed_chunks < len(chunks)
        }
        
        # Cache the result
        if video_id and final_issues:
            if processed_chunks < len(chunks):
                await self.gemini_service.cache_partial_issues(video_id, result)
            else:
                await self.gemini_service.cache_video_issues(video_id, result)
        
        # Yield final result
        yield json.dumps(result) + "\n"
    
    async def _get_emergency_issues(self, transcript: str) -> Dict[str, dict]:
        """Generate practical learning issues from transcript using multiple techniques"""
        try:
            # First try with text analyzer for quick results
            issues = self.text_analyzer.quick_analyze_transcript(transcript)
            if issues and len(issues) >= 3:
                logger.info(f"Generated {len(issues)} practical issues with text analyzer")
                return issues
            
            # If that didn't work well, use the implementation-focused prompt
            from utils.prompt_templates import get_practical_implementation_prompt
            try:
                practical_prompt = get_practical_implementation_prompt() + "\n\n" + transcript[:1500] 
                async with aiohttp.ClientSession() as session:
                    response = await self.gemini_service._call_gemini_api(practical_prompt, fast_mode=True)
                    if response and response.text:
                        response_text = self.gemini_service._clean_response(response.text)
                        parsed = json.loads(response_text)
                        if parsed and parsed.get('issues') and len(parsed.get('issues', [])) >= 3:
                            logger.info("Generated practical issues with specialized prompt")
                            # Convert to the format expected by the rest of the code
                            return {issue.get('title', f"Task {i}"): issue for i, issue in enumerate(parsed.get('issues', []))}
            except Exception as e:
                logger.error(f"Error using practical prompt: {str(e)}")
                
            # Fall back to gemini service emergency generation
            return self.gemini_service._generate_emergency_issues(transcript)
        except Exception as e:
            logger.error(f"Error generating emergency issues: {str(e)}")
            return {}
