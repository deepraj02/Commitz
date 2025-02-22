from youtube_transcript_api import YouTubeTranscriptApi
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.gemini_service import GeminiService
import os
import re
import asyncio
from starlette.responses import StreamingResponse
import json
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
gemini_service = GeminiService(GEMINI_API_KEY, REDIS_URL)

class VideoRequest(BaseModel):
    video_url: str
    x_api_key: str

def extract_video_id(url: str) -> str:
    patterns = [
        r'(?:v=|/)([\w-]{11})(?:\?|&|/|$)',
        r'(?:embed/)([\w-]{11})(?:\?|&|/|$)',
        r'(?:youtu\.be/)([\w-]{11})(?:\?|&|/|$)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("Invalid YouTube URL")

def validate_api_key(key: str) -> bool:
    if key == 'test_key':
        return True
    return False

async def generate_streaming_response(video_id: str):
    try:
        # Get transcript chunks
        transcript_list = await asyncio.to_thread(
            YouTubeTranscriptApi.get_transcript,
            video_id
        )
        transcript = " ".join(item['text'] for item in transcript_list)
        
        # Process transcript and stream results
        chunks = gemini_service._chunk_transcript(transcript)
        
        # Initial response
        yield json.dumps({"status": "processing", "total_chunks": len(chunks)}) + "\n"
        
        processed_chunks = 0
        all_issues = []
        
        async with aiohttp.ClientSession() as session:
            for chunk in chunks:
                chunk_issues = await gemini_service._process_chunk(chunk, session)
                all_issues.extend(chunk_issues)
                processed_chunks += 1
                
                # Send progress update
                yield json.dumps({
                    "status": "processing",
                    "processed_chunks": processed_chunks,
                    "total_chunks": len(chunks),
                    "progress": round(processed_chunks / len(chunks) * 100, 2)
                }) + "\n"
        
        # Final response with deduplicated issues
        unique_issues = {}
        for issue in all_issues:
            title = issue.get('title', '')
            if title and title not in unique_issues:
                unique_issues[title] = {
                    "title": title,
                    "description": gemini_service._format_description(issue),
                    "difficulty": issue.get('difficulty', 'intermediate'),
                    "estimated_hours": issue.get('estimated_hours', 2),
                    "labels": issue.get('labels', ["learning"]),
                    "prerequisites": issue.get('body', {}).get('prerequisites', [])
                }
        
        final_response = {
            "status": "complete",
            "issues": list(unique_issues.values()),
            "total_count": len(unique_issues)
        }
        
        yield json.dumps(final_response) + "\n"
        
    except Exception as e:
        yield json.dumps({"status": "error", "detail": str(e)}) + "\n"

@app.post("/api/v1/transcript/stream")
async def generate_video_transcript_stream(request: VideoRequest):
    if not validate_api_key(request.x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    try:
        video_id = extract_video_id(request.video_url)
        return StreamingResponse(
            generate_streaming_response(video_id),
            media_type="application/x-ndjson"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

# Keep the original endpoint for backwards compatibility
@app.post("/api/v1/transcript")
async def generate_video_transcript(request: VideoRequest):
    if not validate_api_key(request.x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    try:
        video_id = extract_video_id(request.video_url)
        
        transcript_list = await asyncio.to_thread(
            YouTubeTranscriptApi.get_transcript,
            video_id
        )
        transcript = " ".join(item['text'] for item in transcript_list)
        
        issues_response = await gemini_service.process_transcript(transcript)
        
        if not issues_response.get('issues'):
            raise HTTPException(
                status_code=400,
                detail="No issues could be generated from this transcript"
            )
        
        return issues_response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )