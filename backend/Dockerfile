# ============================================
# VideoCatcher Backend — Railway Production Image
# Python 3.12 + Playwright Chromium + FFmpeg
# ============================================
FROM python:3.12-slim

# Set environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install Playwright Chromium (browser binaries)
RUN python -m playwright install chromium
RUN python -m playwright install-deps chromium

# Copy application code
WORKDIR /app
COPY . .

# Start command (PORT comes from Railway env)
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info"]
