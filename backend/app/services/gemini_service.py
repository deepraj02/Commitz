import google.generativeai as genai
from typing import List, Dict
import json
import asyncio
from functools import lru_cache
import hashlib
from collections import defaultdict
import aiohttp
import redis
from datetime import timedelta

class GeminiService:
    def __init__(self, api_key: str, redis_url: str = "redis://localhost:6379"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 1,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        self.redis_client = redis.from_url(redis_url)
        self.chunk_semaphore = asyncio.Semaphore(5) 
    def _cache_key(self, text: str) -> str:
        return f"gemini:{hashlib.md5(text.encode()).hexdigest()}"

    def _chunk_transcript(self, transcript: str) -> List[str]:
        words = transcript.split()
        chunks = []
        chunk_size = 500 
        
        for i in range(0, len(words), chunk_size - 100):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks

    async def _process_chunk(self, chunk: str, session: aiohttp.ClientSession) -> List[dict]:
        cache_key = self._cache_key(chunk)
        cached_result = self.redis_client.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        async with self.chunk_semaphore: 

            try:
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    self._get_prompt() + chunk,
                    generation_config=self.generation_config
                )
                
                response_text = self._clean_response(response.text)
                issues = self._parse_response(response_text)
                
                if issues:
                    self.redis_client.setex(
                        cache_key,
                        timedelta(hours=24),
                        json.dumps(issues)
                    )
                
                return issues
                
            except Exception as e:
                print(f"Chunk processing error: {str(e)}")
                return []

    def _get_prompt(self) -> str:
        return """
        You are a senior software developer creating detailed GitHub issues from a video transcript.
        Analyze this transcript segment and create practical, actionable GitHub issues that will help someone learn and implement the concepts discussed and send me the issues in order to the timestamp of the video thus maintaining a clear learning path.
        
        Create detailed issues that include:
        1. Clear implementation steps
        2. Code examples where relevant
        3. Learning objectives
        4. Expected outcomes
        5. Prerequisites

        Format each issue exactly like this JSON:
        {
            "issues": [
                {
                    "title": "Implement [Specific Feature/Concept]",
                    "body": {
                        "description": "Summary of what needs to be implemented",
                        "learning_objectives": [
                            "- What you'll learn 1",
                            "- What you'll learn 2"
                        ],
                        "implementation_steps": [
                            "1. First step with code example if applicable",
                            "2. Second step with technical details",
                            "3. Testing and validation steps"
                        ],
                        "expected_outcome": "What you should have after completing this issue",
                        "prerequisites": [
                            "Required knowledge/setup 1",
                            "Required knowledge/setup 2"
                        ]
                    },
                    "difficulty": "beginner/intermediate/advanced",
                    "labels": ["enhancement", "learning"]
                }
            ]
        }

        Analyze this transcript segment and create detailed issues:
        """

    def _clean_response(self, response_text: str) -> str:
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0]
        return response_text.strip()

    def _parse_response(self, response_text: str) -> List[dict]:
        try:
            parsed = json.loads(response_text)
            return parsed.get('issues', [])
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return []

    async def process_transcript(self, transcript: str) -> dict:
        chunks = self._chunk_transcript(transcript)
        all_issues = []

        async with aiohttp.ClientSession() as session:
            tasks = [self._process_chunk(chunk, session) for chunk in chunks]
            chunk_results = await asyncio.gather(*tasks)
            
            for chunk_issues in chunk_results:
                all_issues.extend(chunk_issues)
        unique_issues = {}
        for issue in all_issues:
            title = issue.get('title', '')
            if title and title not in unique_issues:
                unique_issues[title] = {
                    "title": title,
                    "description": self._format_description(issue),
                    "difficulty": issue.get('difficulty', 'intermediate'),
                    "estimated_hours": issue.get('estimated_hours', 2),
                    "labels": issue.get('labels', ["learning"]),
                    "prerequisites": issue.get('body', {}).get('prerequisites', [])
                }

        return {
            "issues": list(unique_issues.values()),
            "total_count": len(unique_issues)
        }

    def _format_description(self, issue: dict) -> str:
        body = issue.get('body', {})
        return f"""
## Overview
{body.get('description', '')}

## Learning Objectives
{chr(10).join(body.get('learning_objectives', []))}

## Implementation Steps
{chr(10).join(body.get('implementation_steps', []))}

## Expected Outcome
{body.get('expected_outcome', '')}

## Prerequisites
{chr(10).join(body.get('prerequisites', []))}
        """.strip()