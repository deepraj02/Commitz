import asyncio
from pydantic import BaseModel
import re
import logging
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
import xml.etree.ElementTree

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
        try:
            transcript_list = await asyncio.to_thread(YouTubeTranscriptApi.get_transcript, video_id)
            transcript = " ".join(item['text'] for item in transcript_list)
            logger.info(f"Fetched transcript, length: {len(transcript)}")
            return transcript
        except TranscriptsDisabled:
            logger.error(f"Transcripts are disabled for video {video_id}")
            raise ValueError("Transcripts are disabled for this video")
        except NoTranscriptFound:
            logger.error(f"No transcript found for video {video_id}")
            raise ValueError("No transcript available for this video")
        except VideoUnavailable:
            logger.error(f"Video {video_id} is unavailable")
            raise ValueError("Video is unavailable or private")
        except xml.etree.ElementTree.ParseError as e:
            logger.error(f"XML parsing error for video {video_id}: {e}")
            raise ValueError("No transcript data available for this video")
        except Exception as e:
            logger.error(f"Unexpected error fetching transcript for video {video_id}: {e}")
            if "no element found" in str(e) or "ParseError" in str(e):
                raise ValueError("No transcript data available for this video")
            raise
