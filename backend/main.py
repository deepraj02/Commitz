from youtube_transcript_api import YouTubeTranscriptApi
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    video_url: str
    x_api_key: str

def extract_video_id(url: str) -> str:
    # Match YouTube URL patterns
    patterns = [
        r'(?:v=|/)([\w-]{11})(?:\?|&|/|$)',  # Standard and short YouTube URLs
        r'(?:embed/)([\w-]{11})(?:\?|&|/|$)',  # Embed URLs
        r'(?:youtu\.be/)([\w-]{11})(?:\?|&|/|$)'  # Short URLs
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("Invalid YouTube URL")

def validate_api_key(key:str)->bool:
    if key == 'test_key':
        return True
    return False

@app.post("/api/v1/transcript")
async def generate_video_transcript(request: VideoRequest):
    if not validate_api_key(request.x_api_key):
        return {"error": "Invalid API Key"}
    try:
        video_id = extract_video_id(request.video_url)
        video_transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join(item['text'] for item in video_transcript)
        return {"transcript": transcript}
    except Exception as e:
        return {"error": str(e)}
