import os
import urllib.parse
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response

from config import (
    AI_API_KEY, AI_PROVIDER, AI_MODEL, CORS_ORIGINS,
    VIDEO_INFO_CACHE_TTL, SUMMARY_CACHE_TTL,
    TEMP_DOWNLOAD_DIR,
)
from models.schemas import (
    VideoURLRequest, DownloadRequest,
    VideoInfoResponse, SummaryResponse,
    AskRequest, AskResponse, SubtitlesResponse,
)
from services.video_service import VideoService
from services.ai_service import AIService
from utils.cache import TTLCache

app = FastAPI(title="VideoCatcher API", version="1.0.0")


@app.get("/")
async def root():
    return {"status": "ok", "service": "VideoCatcher API", "version": "1.0.0"}


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
ai_service = AIService(api_key=AI_API_KEY, model=AI_MODEL or None, provider=AI_PROVIDER)

# Caches
info_cache = TTLCache(ttl_seconds=VIDEO_INFO_CACHE_TTL)
summary_cache = TTLCache(ttl_seconds=SUMMARY_CACHE_TTL)


@app.on_event("startup")
async def startup():
    os.makedirs(TEMP_DOWNLOAD_DIR, exist_ok=True)
    video_service.cleanup_old_files()
    if not ai_service.is_configured:
        print("WARNING: AI_API_KEY not set. AI summary will be disabled.")
    else:
        print(f"AI service configured: provider={ai_service.provider}, model={ai_service.model}")


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
            detail={"error": "AI summary service not configured", "detail": "请配置 AI_API_KEY（支持 DeepSeek 和 Claude）", "retryable": False},
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
            request.url, request.format_id, request.type
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


@app.get("/api/image/proxy")
async def proxy_image(url: str = Query(...)):
    """Proxy external images to bypass Referer/CORS restrictions (e.g. Bilibili CDN)."""
    import httpx
    try:
        resp = httpx.get(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bilibili.com/',
                'Origin': 'https://www.bilibili.com',
            },
            timeout=10.0,
            follow_redirects=True,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Image not found")

        content_type = resp.headers.get('content-type', 'image/jpeg')
        return Response(
            content=resp.content,
            media_type=content_type,
            headers={'Cache-Control': 'public, max-age=3600'},
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Image fetch failed")


@app.post("/api/video/ask", response_model=AskResponse)
async def ask_video(request: AskRequest):
    """AI Q&A: ask questions about a video using its metadata + subtitles as context."""
    if not ai_service.is_configured:
        raise HTTPException(status_code=503, detail={"error": "AI not configured"})

    try:
        info = info_cache.get(request.url)
        if info is None:
            info = await video_service.extract_info(request.url)
            info_cache.set(request.url, info)

        subtitles = await video_service.extract_subtitles(request.url)

        answer = await ai_service.ask_question(
            title=info.get("title", ""),
            description=info.get("description", ""),
            uploader=info.get("uploader", ""),
            subtitles=subtitles,
            question=request.question,
        )
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=502, detail={"error": str(e)})


@app.get("/api/video/subtitles", response_model=SubtitlesResponse)
async def get_subtitles(url: str = Query(...)):
    """Get raw subtitle text for a video."""
    try:
        text = await video_service.extract_subtitles(url)
        return {"text": text or "该视频没有可用字幕", "language": "auto"}
    except Exception as e:
        raise HTTPException(status_code=502, detail={"error": str(e)})


@app.post("/api/video/mindmap")
async def generate_mindmap(request: VideoURLRequest):
    """Generate a mind map structure from video content."""
    if not ai_service.is_configured:
        raise HTTPException(status_code=503, detail={"error": "AI not configured"})

    try:
        info = info_cache.get(request.url)
        if info is None:
            info = await video_service.extract_info(request.url)
            info_cache.set(request.url, info)

        subtitles = await video_service.extract_subtitles(request.url)

        mindmap = await ai_service.generate_mindmap(
            title=info.get("title", ""),
            description=info.get("description", ""),
            subtitles=subtitles,
        )
        return mindmap
    except Exception as e:
        raise HTTPException(status_code=502, detail={"error": str(e)})


def _is_retryable(error_msg: str) -> bool:
    """Determine if an error is likely retryable."""
    non_retryable = [
        "private", "unavailable", "deleted", "not found",
        "not exist", "removed", "copyright",
    ]
    msg_lower = error_msg.lower()
    return not any(phrase in msg_lower for phrase in non_retryable)
