import os
import urllib.parse
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from config import (
    ANTHROPIC_API_KEY, CORS_ORIGINS,
    VIDEO_INFO_CACHE_TTL, SUMMARY_CACHE_TTL,
    TEMP_DOWNLOAD_DIR, AI_MODEL,
)
from models.schemas import (
    VideoURLRequest, DownloadRequest,
    VideoInfoResponse, SummaryResponse,
)
from services.video_service import VideoService
from services.ai_service import AIService
from utils.cache import TTLCache

app = FastAPI(title="VideoCatcher API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
video_service = VideoService(temp_dir=TEMP_DOWNLOAD_DIR)
ai_service = AIService(api_key=ANTHROPIC_API_KEY, model=AI_MODEL)

# Caches
info_cache = TTLCache(ttl_seconds=VIDEO_INFO_CACHE_TTL)
summary_cache = TTLCache(ttl_seconds=SUMMARY_CACHE_TTL)


@app.on_event("startup")
async def startup():
    os.makedirs(TEMP_DOWNLOAD_DIR, exist_ok=True)
    video_service.cleanup_old_files()
    if not ai_service.is_configured:
        print("WARNING: ANTHROPIC_API_KEY not set. AI summary will be disabled.")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/video/info", response_model=VideoInfoResponse)
async def get_video_info(request: VideoURLRequest):
    try:
        if not request.refresh:
            cached = info_cache.get(request.url)
            if cached:
                return cached

        info = await video_service.extract_info(request.url)
        info_cache.set(request.url, info)
        return info

    except Exception as e:
        error_msg = str(e)
        retryable = _is_retryable(error_msg)
        raise HTTPException(
            status_code=502,
            detail={"error": "视频信息提取失败", "detail": error_msg, "retryable": retryable},
        )


@app.post("/api/video/summary", response_model=SummaryResponse)
async def get_video_summary(request: VideoURLRequest):
    if not ai_service.is_configured:
        raise HTTPException(
            status_code=503,
            detail={"error": "AI summary service not configured", "detail": "请配置 ANTHROPIC_API_KEY", "retryable": False},
        )

    try:
        if not request.refresh:
            cached = summary_cache.get(request.url)
            if cached:
                return cached

        # Get video info (from cache or fetch)
        info = info_cache.get(request.url)
        if info is None:
            info = await video_service.extract_info(request.url)
            info_cache.set(request.url, info)

        # Extract subtitles for better summary
        subtitles = await video_service.extract_subtitles(request.url)

        result = await ai_service.generate_summary(
            title=info.get("title", ""),
            description=info.get("description"),
            uploader=info.get("uploader"),
            duration_str=info.get("duration_str"),
            subtitles=subtitles,
        )

        summary_cache.set(request.url, result)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={"error": "AI总结生成失败", "detail": str(e), "retryable": True},
        )


@app.post("/api/download")
async def download_video(request: DownloadRequest, background_tasks: BackgroundTasks):
    try:
        file_path, filename, mime_type = await video_service.download(
            request.url, request.format_id
        )

        # Schedule cleanup after streaming
        background_tasks.add_task(video_service.cleanup, file_path)

        encoded_filename = urllib.parse.quote(filename)

        def iterfile():
            with open(file_path, 'rb') as f:
                yield from f

        return StreamingResponse(
            iterfile(),
            media_type=mime_type,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Content-Length": str(os.path.getsize(file_path)),
            },
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=502,
            detail={"error": "下载失败：生成文件失败", "detail": str(e), "retryable": True},
        )
    except Exception as e:
        error_msg = str(e)
        retryable = _is_retryable(error_msg)
        raise HTTPException(
            status_code=502,
            detail={"error": "下载失败", "detail": error_msg, "retryable": retryable},
        )


def _is_retryable(error_msg: str) -> bool:
    """Determine if an error is likely retryable."""
    non_retryable = [
        "private", "unavailable", "deleted", "not found",
        "not exist", "removed", "copyright",
    ]
    msg_lower = error_msg.lower()
    return not any(phrase in msg_lower for phrase in non_retryable)
