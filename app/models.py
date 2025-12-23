from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoInfo(BaseModel):
    id: str
    title: str
    duration: int
    thumbnail: str
    selected: bool = True


class DownloadRequest(BaseModel):
    url: HttpUrl = Field(..., description="YouTube video or playlist URL")
    is_playlist: bool = False


class PlaylistRequest(BaseModel):
    url: HttpUrl = Field(..., description="YouTube playlist URL")
    video_ids: List[str] = Field(..., description="Selected video IDs to download")


class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    message: str
    progress: float = 0.0
    total_videos: int = 0
    completed_videos: int = 0


class VideoInfoResponse(BaseModel):
    is_playlist: bool
    videos: List[VideoInfo]
    playlist_title: Optional[str] = None