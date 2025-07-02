import os
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from utils.video_utils import VideoUtils
from models.video_request_model import VideoRequest
from models.sync_request_model import SyncRequest
from services.gemini_service import GeminiService
from services.github_service import GithubService
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
video_utils = VideoUtils()


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
gemini_service = GeminiService(GEMINI_API_KEY, redis_url=REDIS_URL)
logger.info("Gemini service initialized")

GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_PRIVATE_KEY = os.getenv("GITHUB_PRIVATE_KEY")
if not GITHUB_APP_ID or not GITHUB_PRIVATE_KEY:
    logger.error("GITHUB_APP_ID or GITHUB_PRIVATE_KEY not set")
    raise ValueError("GITHUB_APP_ID and GITHUB_PRIVATE_KEY must be set")
logger.info("GitHub service initialized")
github_service = GithubService(GITHUB_APP_ID, GITHUB_PRIVATE_KEY)

async def get_api_key(x_api_key: Optional[str] = Header(default=None)) -> Optional[str]:
    return x_api_key

def validate_api_key(key: Optional[str]) -> bool:
    return key == 'test_key'

@app.post("/api/v1/transcript")
async def process_transcript(
    request: VideoRequest,
    api_key: Optional[str] = Depends(get_api_key)
):
    key_to_validate = request.x_api_key or api_key
    if not validate_api_key(key_to_validate):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    try:
        video_id = video_utils.extract_video_id(request.video_url)
        cached_result = await gemini_service.get_cached_result(video_id)
        if cached_result:
            return cached_result

        transcript = await video_utils.fetch_transcript(video_id)
        if not transcript.strip():
            raise HTTPException(status_code=400, detail="Empty transcript")

        result = await gemini_service.process_transcript(transcript, video_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/github/installation_url")
async def get_github_installation_url():
    url = github_service.get_installation_url()
    return {"installation_url": url}

@app.get("/api/v1/github/callback")
async def github_callback(request: Request):
    installation_id = request.query_params.get("installation_id")
    if not installation_id:
        raise HTTPException(status_code=400, detail="installation_id is required")
    
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    redirect_url = f"{frontend_url}/?installation_id={installation_id}"
    return RedirectResponse(url=redirect_url)


@app.post("/api/v1/github/sync")
async def sync_issues(
    request: SyncRequest,
    api_key: Optional[str] = Depends(get_api_key)
):
    if not validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    try:
        for issue in request.issues:
            github_service.create_issue(
                installation_id=request.installation_id,
                repo_name=request.repo_name,
                title=issue.title,
                body=issue.body
            )
        return {"message": "Issues synced successfully"}
    except Exception as e:
        logger.error(f"Failed to sync issues: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to sync issues")


@app.get("/health")
async def health_check():
    redis_status = await gemini_service.is_redis_connected()
    status = "healthy" if redis_status else "degraded"
    return {"status": status, "redis": "connected" if redis_status else "disconnected"}

@app.get("/")
async def root():
    return {"message": "YouTube Transcript API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 9000))
    uvicorn.run(app, host="0.0.0.0", port=port)