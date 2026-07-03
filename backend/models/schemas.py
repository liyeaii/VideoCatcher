from pydantic import BaseModel, HttpUrl
from typing import Optional


# ── Request Models ──

class VideoURLRequest(BaseModel):
    url: str
    refresh: bool = False


class DownloadRequest(BaseModel):
    url: str
    format_id: str


# ── Response Models ──

class FormatInfo(BaseModel):
    format_id: str
    quality: str
    type: str          # "video+audio" | "video only" | "audio only"
    ext: str
    filesize: Optional[int] = None
    filesize_str: str
    note: Optional[str] = None


class VideoInfoResponse(BaseModel):
    id: str
    title: str
    thumbnail: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    duration_str: Optional[str] = None
    uploader: Optional[str] = None
    view_count: Optional[int] = None
    webpage_url: Optional[str] = None
    formats: list[FormatInfo] = []


class SummaryResponse(BaseModel):
    summary: str
    key_points: list[str] = []
