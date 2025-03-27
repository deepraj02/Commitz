import asyncio
from pydantic import BaseModel
import re
import logging
from youtube_transcript_api import YouTubeTranscriptApi

logger = logging.getLogger(__name__)

class VideoUtils:

    @staticmethod
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
    
    @staticmethod
    async def fetch_transcript(video_id: str) -> str:
        transcript_list = await asyncio.to_thread(YouTubeTranscriptApi.get_transcript, video_id)
        transcript = " ".join(item['text'] for item in transcript_list)
        logger.info(f"Fetched transcript, length: {len(transcript)}")
        return transcript
