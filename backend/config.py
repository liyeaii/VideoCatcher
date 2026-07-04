import os
from dotenv import load_dotenv

load_dotenv()

# ── AI Provider ──
AI_API_KEY = os.getenv("AI_API_KEY", "") or os.getenv("ANTHROPIC_API_KEY", "")
AI_PROVIDER = os.getenv("AI_PROVIDER", "auto")  # "auto" | "deepseek" | "claude"
AI_MODEL = os.getenv("AI_MODEL", "")  # empty = use provider default

# ── Server ──
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
VIDEO_INFO_CACHE_TTL = int(os.getenv("VIDEO_INFO_CACHE_TTL", "1800"))
SUMMARY_CACHE_TTL = int(os.getenv("SUMMARY_CACHE_TTL", "3600"))
TEMP_DOWNLOAD_DIR = os.getenv("TEMP_DOWNLOAD_DIR", "./downloads")
