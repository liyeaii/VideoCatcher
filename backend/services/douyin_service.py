"""
Douyin (抖音) video extraction via Playwright headless browser.

Douyin requires browser-executed JavaScript to generate a_bogus signatures.
Playwright runs a real Chromium browser, so signatures and cookies work naturally.

Fallback chain:
  1. Playwright headless browser (primary, most reliable)
  2. yt-dlp with browser cookies (fallback)
"""

import asyncio
import json
import os
import re
import time
from typing import Optional
from pathlib import Path

# Douyin URL patterns
DOUYIN_VIDEO_ID_PATTERN = re.compile(r'/video/(\d+)')
DOUYIN_DISCOVER_ID_PATTERN = re.compile(r'modal_id=(\d+)')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
}


def _format_size(size: Optional[int]) -> str:
    if size is None or size <= 0:
        return "大小未知"
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"


def _format_duration(seconds) -> Optional[str]:
    if seconds is None:
        return None
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class DouyinService:
    """Douyin video extraction using Playwright for real browser JS execution."""

    def __init__(self):
        self._playwright = None
        self._browser = None

    async def _ensure_browser(self):
        """Lazy-init Playwright browser (Chromium must be installed)."""
        if self._browser is not None:
            return self._browser

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RuntimeError(
                "Playwright 未安装。请在 Railway Dockerfile 中添加:\n"
                "RUN pip install playwright && python -m playwright install chromium"
            )

        self._playwright = await async_playwright().start()
        try:
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                ],
            )
        except Exception as e:
            raise RuntimeError(
                f"Chromium 启动失败: {e}\n"
                "请在 Railway Dockerfile 中安装 Chromium:\n"
                "RUN python -m playwright install chromium && python -m playwright install-deps chromium"
            )
        return self._browser

    async def close(self):
        """Clean up browser resources."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._playwright = None

    # ── Public API ──

    def extract_info(self, url: str) -> Optional[dict]:
        """Synchronous entry point. Creates a dedicated event loop for async extraction."""
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self._extract_info_async(url))
        except RuntimeError:
            raise  # Re-raise filtered/unavailable video errors
        except Exception:
            return None
        finally:
            try:
                loop.run_until_complete(self.close())
            except Exception:
                pass
            try:
                loop.close()
            except Exception:
                pass

    async def _extract_info_async(self, url: str) -> Optional[dict]:
        """Extract video metadata using Playwright."""
        video_id = self._extract_video_id(url)
        if not video_id:
            return None

        # Resolve short URLs
        if 'v.douyin.com' in url:
            resolved = await self._resolve_short_url(url)
            if resolved:
                video_id = self._extract_video_id(resolved) or video_id

        # Try Playwright extraction
        try:
            result = await self._extract_with_playwright(video_id)
            if result and result.get('formats'):
                return result
        except RuntimeError as e:
            # Re-raise filtered/blocked errors with clear message
            raise RuntimeError(f'抖音视频不可用：{e}')

        return None

    # ── Playwright Extraction ──

    async def _extract_with_playwright(self, video_id: str) -> Optional[dict]:
        """Use Playwright to visit the Douyin video page and intercept the API response."""
        try:
            browser = await self._ensure_browser()
            context = await browser.new_context(
                user_agent=HEADERS['User-Agent'],
                viewport={'width': 1920, 'height': 1080},
                locale='zh-CN',
            )

            page = await context.new_page()

            # Intercept the aweme/detail API response
            api_response_data = {}

            async def handle_response(response):
                if 'aweme/v1/web/aweme/detail' in response.url and f'aweme_id={video_id}' in response.url:
                    try:
                        body = await response.json()
                        if body.get('aweme_detail'):
                            api_response_data['data'] = body
                        elif body.get('filter_detail', {}).get('filter_reason'):
                            api_response_data['filtered'] = body['filter_detail']
                    except Exception:
                        pass

            page.on('response', handle_response)

            # Navigate to the video page
            video_url = f'https://www.douyin.com/video/{video_id}'
            await page.goto(video_url, wait_until='domcontentloaded', timeout=30000)

            # Wait for the API response (the page makes this call via JS)
            for _ in range(20):  # Wait up to 10 seconds
                if api_response_data.get('data'):
                    break
                await asyncio.sleep(0.5)

            await context.close()

            if api_response_data.get('data'):
                detail = api_response_data['data']['aweme_detail']
                return self._normalize(detail, video_id)

            if api_response_data.get('filtered'):
                reason = api_response_data['filtered'].get('filter_reason', 'unknown')
                raise RuntimeError(f'视频不可用 (filter: {reason})')

        except RuntimeError:
            raise
        except Exception:
            pass

        return None

    # ── URL Parsing ──

    def _extract_video_id(self, url: str) -> Optional[str]:
        match = DOUYIN_VIDEO_ID_PATTERN.search(url)
        if match:
            return match.group(1)
        match = DOUYIN_DISCOVER_ID_PATTERN.search(url)
        if match:
            return match.group(1)
        return None

    async def _resolve_short_url(self, url: str) -> Optional[str]:
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=HEADERS, follow_redirects=False, timeout=10.0)
                if resp.status_code in (301, 302):
                    location = resp.headers.get('Location', '')
                    return location.split('?')[0] if '?' in location else location
        except Exception:
            pass
        return None

    # ── Normalize ──

    def _normalize(self, data: dict, video_id: str) -> dict:
        """Normalize raw Douyin API response to VideoCatcher format."""
        title = data.get('desc', '未知标题')
        duration_ms = data.get('duration', 0)
        duration_sec = duration_ms // 1000 if duration_ms else None

        author = data.get('author', {})
        statistics = data.get('statistics', {})
        video_info = data.get('video', {})

        cover = video_info.get('cover', {})
        thumbnail = ''
        if isinstance(cover, dict):
            url_list = cover.get('url_list', [])
            thumbnail = url_list[0] if url_list else ''
        elif isinstance(cover, str):
            thumbnail = cover

        formats = []

        # Main play address (no watermark)
        play_addr = video_info.get('play_addr', {})
        if play_addr:
            uri = play_addr.get('uri', '')
            url_list = play_addr.get('url_list', [])
            if uri:
                nwm_url = f"https://aweme.snssdk.com/aweme/v1/play/?video_id={uri}&ratio=1080p&line=0"
                formats.append({
                    'format_id': 'nwm_video',
                    'quality': '1080p',
                    'type': 'video+audio',
                    'ext': 'mp4',
                    'filesize': None,
                    'filesize_str': _format_size(None),
                    'note': '无水印',
                    '_direct_url': nwm_url,
                })

        # Higher quality variants
        bit_rate_list = video_info.get('bit_rate', [])
        for i, br in enumerate(bit_rate_list):
            br_play_addr = br.get('play_addr', {})
            br_url_list = br_play_addr.get('url_list', [])
            if br_url_list:
                height = br.get('gear_name', f'quality_{i}')
                formats.append({
                    'format_id': f'nwm_video_br_{i}',
                    'quality': height,
                    'type': 'video+audio',
                    'ext': 'mp4',
                    'filesize': None,
                    'filesize_str': _format_size(None),
                    'note': f'高清 {height}',
                    '_direct_url': br_url_list[0],
                })

        # Add watermark version if available
        if play_addr and play_addr.get('url_list'):
            wm_url = play_addr['url_list'][0]
            if wm_url:
                formats.append({
                    'format_id': 'wm_video',
                    'quality': '1080p',
                    'type': 'video+audio',
                    'ext': 'mp4',
                    'filesize': None,
                    'filesize_str': _format_size(None),
                    'note': '有水印',
                    '_direct_url': wm_url,
                })

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'description': title,
            'duration': duration_sec,
            'duration_str': _format_duration(duration_sec),
            'uploader': author.get('nickname', '') if isinstance(author, dict) else '',
            'view_count': statistics.get('play_count', 0) if isinstance(statistics, dict) else 0,
            'webpage_url': f'https://www.douyin.com/video/{video_id}',
            'formats': formats,
        }

    # ── Download ──

    def get_download_urls(self, video_id: str, format_id: str) -> Optional[dict]:
        """Get download URL for a specific format."""
        info = self.extract_info(f'https://www.douyin.com/video/{video_id}')
        if not info:
            return None

        for f in info.get('formats', []):
            if f['format_id'] == format_id:
                return {
                    'format': f,
                    'title': info.get('title', 'video'),
                    'video_id': video_id,
                }
        return None
