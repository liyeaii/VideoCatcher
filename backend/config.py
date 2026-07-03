import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
VIDEO_INFO_CACHE_TTL = int(os.getenv("VIDEO_INFO_CACHE_TTL", "1800"))
SUMMARY_CACHE_TTL = int(os.getenv("SUMMARY_CACHE_TTL", "3600"))
TEMP_DOWNLOAD_DIR = os.getenv("TEMP_DOWNLOAD_DIR", "./downloads")
AI_MODEL = os.getenv("AI_MODEL", "claude-sonnet-4-20250514")
