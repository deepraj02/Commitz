import asyncio
import os
import re
import json
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from services.gemini_service import GeminiService
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

load_dotenv()
logger.info("Application starting...")

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
    logger.error("GEMINI_API_KEY not set")
    raise ValueError("GEMINI_API_KEY not set")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
logger.info(f"Using Redis at: {REDIS_URL}")

gemini_service = GeminiService(GEMINI_API_KEY)
logger.info("Gemini service initialized")

class VideoRequest(BaseModel):
    video_url: str
    x_api_key: Optional[str] = None

async def get_api_key(x_api_key: Optional[str] = Header(default=None)) -> Optional[str]:
    return x_api_key

def extract_video_id(url: str) -> str:
    patterns = [
        r'(?:v=|/)([\w-]{11})(?:\?|&|/|$)',
        r'(?:embed/)([\w-]{11})(?:\?|&|/|$)',
        r'(?:youtu\.be/)([\w-]{11})(?:\?|&|/|$)'
    ]
    for pattern in patterns:
        if match := re.search(pattern, url):
            video_id = match.group(1)
            logger.info(f"Extracted video ID: {video_id}")
            return video_id
    logger.error(f"Invalid YouTube URL: {url}")
    raise ValueError("Invalid YouTube URL")

def validate_api_key(key: Optional[str]) -> bool:
    return key == 'test_key'

async def fetch_transcript(video_id: str) -> str:
    transcript_list = await asyncio.to_thread(YouTubeTranscriptApi.get_transcript, video_id)
    transcript = " ".join(item['text'] for item in transcript_list)
    logger.info(f"Fetched transcript, length: {len(transcript)}")
    return transcript

@app.post("/api/v1/transcript")
async def process_transcript(
    request: VideoRequest,
    api_key: Optional[str] = Depends(get_api_key)
):
    key_to_validate = request.x_api_key or api_key
    if not validate_api_key(key_to_validate):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    try:
        video_id = extract_video_id(request.video_url)
        # cached_result = await gemini_service.get_cached_result(video_id)
        # if cached_result:
        #     return cached_result

        transcript = await fetch_transcript(video_id)
        if not transcript.strip():
            raise HTTPException(status_code=400, detail="Empty transcript")

        result = await gemini_service.process_transcript(transcript, video_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# @app.get("/health")
# async def health_check():
#     # redis_status = gemini_service.redis_client.ping() if gemini_service.redis_client else False
#     # status = "healthy" if redis_status else "degraded"
#     return {"status": , }

@app.get("/")
async def root():
    return {"message": "YouTube Transcript API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 9000))
    uvicorn.run(app, host="0.0.0.0", port=port)