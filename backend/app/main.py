from youtube_transcript_api import YouTubeTranscriptApi
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.gemini_service import GeminiService
import os
import re
import asyncio
from starlette.responses import StreamingResponse
import json
from dotenv import load_dotenv
import aiohttp
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()
logger.info("Starting application and loading environment variables")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY environment variable is not set")
    raise ValueError("GEMINI_API_KEY environment variable is not set")
else:
    logger.info("GEMINI_API_KEY successfully loaded")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
logger.info(f"Using Redis URL: {REDIS_URL}")

try:
    gemini_service = GeminiService(GEMINI_API_KEY, REDIS_URL)
    logger.info("Gemini service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini service: {str(e)}", exc_info=True)
    raise

class VideoRequest(BaseModel):
    video_url: str
    x_api_key: Optional[str] = None

async def get_api_key(x_api_key: Optional[str] = Header(None)):
    return x_api_key

def extract_video_id(url: str) -> str:
    logger.info(f"Extracting video ID from URL: {url}")
    patterns = [
        r'(?:v=|/)([\w-]{11})(?:\?|&|/|$)',
        r'(?:embed/)([\w-]{11})(?:\?|&|/|$)',
        r'(?:youtu\.be/)([\w-]{11})(?:\?|&|/|$)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            logger.info(f"Successfully extracted video ID: {video_id}")
            return video_id
    
    logger.error(f"Failed to extract video ID from URL: {url}")
    raise ValueError("Invalid YouTube URL")

def validate_api_key(key: str) -> bool:
    # For testing purposes, we're using a simple key validation
    # In production, this should be replaced with a more secure method
    logger.info(f"Validating API key: {'*****' if key else 'None'}")
    if key == 'test_key':
        logger.info("API key validation successful")
        return True
    logger.warning("API key validation failed")
    return False

async def generate_streaming_response(video_id: str):
    try:
        logger.info(f"Fetching transcript for video ID: {video_id}")
        transcript_list = await asyncio.to_thread(
            YouTubeTranscriptApi.get_transcript,
            video_id
        )
        transcript = " ".join(item['text'] for item in transcript_list)
        logger.info(f"Transcript fetched successfully, length: {len(transcript)} characters")
        
        logger.info("Chunking transcript")
        chunks = gemini_service._chunk_transcript(transcript)
        logger.info(f"Transcript split into {len(chunks)} chunks")
        
        yield json.dumps({"status": "processing", "total_chunks": len(chunks)}) + "\n"
        
        processed_chunks = 0
        all_issues = []
        
        logger.info("Beginning to process chunks")
        async with aiohttp.ClientSession() as session:
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                try:
                    chunk_issues = await gemini_service._process_chunk(chunk, session)
                    logger.info(f"Chunk {i+1} processed, found {len(chunk_issues)} issues")
                    all_issues.extend(chunk_issues)
                    processed_chunks += 1
                except Exception as e:
                    logger.error(f"Error processing chunk {i+1}: {str(e)}", exc_info=True)
                
                yield json.dumps({
                    "status": "processing",
                    "processed_chunks": processed_chunks,
                    "total_chunks": len(chunks),
                    "progress": round(processed_chunks / len(chunks) * 100, 2)
                }) + "\n"
        
        logger.info("All chunks processed, deduplicating issues")
        unique_issues = []
        seen_titles = set()
        
        for issue in all_issues:
            title = issue.get('title', '')
            if title and title not in seen_titles:
                seen_titles.add(title)
                # Ensure we only include title and description
                unique_issues.append({
                    "title": title,
                    "description": gemini_service._format_description(issue)
                })
        
        logger.info(f"Found {len(unique_issues)} unique issues after deduplication")
        final_response = {
            "status": "complete",
            "issues": unique_issues,
            "total_count": len(unique_issues)
        }
        
        yield json.dumps(final_response) + "\n"
        logger.info("Streaming response completed successfully")
        
    except Exception as e:
        logger.error(f"Error in streaming response: {str(e)}", exc_info=True)
        yield json.dumps({"status": "error", "detail": str(e)}) + "\n"

@app.post("/api/v1/transcript/stream")
async def generate_video_transcript_stream(
    request: VideoRequest, 
    api_key: Optional[str] = Depends(get_api_key)
):
    logger.info("Received streaming transcript request")
    
    # Use either the key from the request body or header
    key_to_validate = request.x_api_key or api_key
    
    if not key_to_validate or not validate_api_key(key_to_validate):
        logger.warning("Invalid or missing API key in request")
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")
    
    try:
        logger.info(f"Processing video URL: {request.video_url}")
        video_id = extract_video_id(request.video_url)
        
        # Try cached result first
        cached_result = await gemini_service.get_cached_video_issues(video_id)
        if cached_result:
            # Ensure we only return title and description
            cleaned_issues = []
            for issue in cached_result.get("issues", []):
                cleaned_issues.append({
                    "title": issue.get("title", ""),
                    "description": issue.get("description", "")
                })
            
            yield json.dumps({
                "status": "complete",
                "cached": True,
                "issues": cleaned_issues,
                "total_count": len(cleaned_issues)
            }) + "\n"
            return

        # Continue with normal processing if not cached
        async for data in generate_streaming_response(video_id):
            yield data
            
    except ValueError as e:
        logger.error(f"Invalid URL error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in stream endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

@app.post("/api/v1/transcript")
async def generate_video_transcript(request: VideoRequest, api_key: Optional[str] = Depends(get_api_key)):
    logger.info("Received transcript request")
    
    key_to_validate = request.x_api_key or api_key
    
    if not key_to_validate or not validate_api_key(key_to_validate):
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")
    
    try:
        logger.info(f"Processing video URL: {request.video_url}")
        video_id = extract_video_id(request.video_url)
        
        # Try to get cached result first
        cached_result = await gemini_service.get_cached_video_issues(video_id)
        if cached_result:
            # Ensure we only return title and description
            cleaned_issues = []
            for issue in cached_result.get("issues", []):
                cleaned_issues.append({
                    "title": issue.get("title", ""),
                    "description": issue.get("description", "")
                })
            
            return {
                "issues": cleaned_issues,
                "total_count": len(cleaned_issues),
                "cached": True
            }
        
        transcript_list = await asyncio.to_thread(
            YouTubeTranscriptApi.get_transcript,
            video_id
        )
        transcript = " ".join(item['text'] for item in transcript_list)
        
        if not transcript.strip():
            raise HTTPException(
                status_code=400,
                detail="No transcript content found for this video"
            )
        
        issues_response = await gemini_service.process_transcript(transcript, video_id)
        
        # Final check to ensure only title and description are included
        if "issues" in issues_response:
            clean_issues = []
            for issue in issues_response["issues"]:
                clean_issues.append({
                    "title": issue.get("title", ""),
                    "description": issue.get("description", "")
                })
            issues_response["issues"] = clean_issues
            
        return issues_response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the request"
        )

@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    try:
        # Check Redis connection
        redis_ping = gemini_service.redis_client.ping()
        logger.info(f"Redis connection: {'OK' if redis_ping else 'Failed'}")
        
        # Return healthy status if Redis is connected
        if redis_ping:
            return {"status": "healthy", "components": {"redis": "connected"}}
        else:
            return {"status": "degraded", "components": {"redis": "disconnected"}}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return {"status": "unhealthy", "error": str(e)}

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the YouTube Transcript API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "9000"))
    logger.info(f"Starting uvicorn server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)