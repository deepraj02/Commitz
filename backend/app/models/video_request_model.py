from typing import Optional
from pydantic import BaseModel


class VideoRequest(BaseModel):
    video_url: str
    x_api_key: Optional[str] = None