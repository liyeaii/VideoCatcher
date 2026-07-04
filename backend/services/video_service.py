import asyncio
import os
import re
import uuid
import shutil
import tempfile
from typing import Optional


# Bilibili BV号正则
BV_PATTERN = re.compile(r'(BV[a-zA-Z0-9]{10})')


# 模拟浏览器请求头（Bilibili 等国内网站需要）
BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Origin': 'https://www.bilibili.com',
    'Referer': 'https://www.bilibili.com/',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
}


class VideoService:
    """Wrapper around yt-dlp for metadata extraction and downloading."""

    INFO_OPTS = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'http_headers': BROWSER_HEADERS,
    }

    # Douyin video ID pattern
    DOUYIN_PATTERN = re.compile(r'douyin\.com/(?:video|discover\?modal_id=)(\d+)')

    def __init__(self, temp_dir: str = "./downloads"):
        self.temp_dir = os.path.abspath(temp_dir)
        os.makedirs(self.temp_dir, exist_ok=True)
        self._bilibili_cookies = None  # cached Bilibili cookies
        self._bilibili_svc = None  # lazy-loaded Bilibili direct API client
        self._douyin_svc = None  # lazy-loaded Douyin direct API client

    async def extract_info(self, url: str) -> dict:
        """Extract video metadata. Runs sync yt-dlp in executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_info_sync, url)

    def _get_bilibili_cookies(self) -> dict:
        """Fetch Bilibili homepage to obtain required anti-crawler cookies (buvid3, etc.)."""
        if self._bilibili_cookies is not None:
            return self._bilibili_cookies

        try:
            import httpx
            # Visit the homepage to get buvid3, b_nut, etc.
            resp = httpx.get(
                "https://www.bilibili.com/",
                headers=BROWSER_HEADERS,
                timeout=10.0,
                follow_redirects=True,
            )
            cookies = dict(resp.cookies.items())
            self._bilibili_cookies = cookies
            return cookies
        except Exception:
            self._bilibili_cookies = {}
            return {}

    def _get_bilibili_video_cookies(self, url: str) -> dict:
        """Visit the actual Bilibili video page to get all required session cookies."""
        try:
            import httpx
            # First get homepage cookies
            base_cookies = self._get_bilibili_cookies()

            # Visit the video page to set additional cookies
            resp = httpx.get(
                url,
                headers={**BROWSER_HEADERS, 'Referer': 'https://www.bilibili.com/'},
                cookies=base_cookies,
                timeout=10.0,
                follow_redirects=True,
            )
            # Merge all cookies
            all_cookies = {**base_cookies, **dict(resp.cookies.items())}
            return all_cookies
        except Exception:
            return self._get_bilibili_cookies()

    def _setup_bilibili_cookies(self, url: str, opts: dict):
        """If URL is from Bilibili, inject video-page cookies into yt-dlp opts.
        Returns a cleanup callable (or None).
        """
        if 'bilibili.com' not in url and 'b23.tv' not in url:
            return None

        cookies = self._get_bilibili_video_cookies(url)
        if not cookies:
            return None

        cookie_lines = []
        for name, value in cookies.items():
            cookie_lines.append(
                f".bilibili.com\tTRUE\t/\tFALSE\t0\t{name}\t{value}"
            )
        if not cookie_lines:
            return None

        fd, cookie_path = tempfile.mkstemp(suffix='.txt', prefix='bili_cookies_')
        with os.fdopen(fd, 'w') as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("\n".join(cookie_lines) + "\n")
        opts['cookiefile'] = cookie_path
        return lambda: os.unlink(cookie_path)

    def _extract_info_sync(self, url: str) -> dict:
        # Try direct Bilibili API first (more reliable than yt-dlp for Bilibili)
        if ('bilibili.com' in url or 'b23.tv' in url) and BV_PATTERN.search(url):
            result = self._try_bilibili_direct(url)
            if result and result.get('formats'):
                return result

        # Try direct Douyin API first (with a_bogus / X-Bogus signatures)
        if 'douyin.com' in url:
            result = self._try_douyin_direct(url)
            if result and result.get('formats'):
                return result
            # Direct API failed - try yt-dlp with browser cookies
            # (skip plain yt-dlp for Douyin as it requires fresh cookies)
            return self._extract_douyin_with_browser_cookies(url)

        # Fall back to yt-dlp for all other sites
        import yt_dlp

        opts = {
            **self.INFO_OPTS,
            'extract_flat': False,
        }

        cleanup = self._setup_bilibili_cookies(url, opts)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                raw = ydl.extract_info(url, download=False)
                safe = ydl.sanitize_info(raw)
            return self._normalize_info(safe)
        finally:
            if cleanup:
                cleanup()

    def _extract_douyin_with_browser_cookies(self, url: str) -> dict:
        """Last resort for Douyin: try yt-dlp with cookies from Edge/Chrome browser."""
        import yt_dlp

        # Convert non-standard Douyin URLs (e.g. /jingxuan?modal_id=) to standard /video/ format
        normalized_url = url
        modal_match = re.search(r'modal_id=(\d+)', url)
        if modal_match:
            normalized_url = f'https://www.douyin.com/video/{modal_match.group(1)}'

        browsers = ['edge', 'chrome', 'firefox', 'opera', 'brave']
        last_error = None

        for browser in browsers:
            try:
                opts = {
                    **self.INFO_OPTS,
                    'extract_flat': False,
                    'cookiesfrombrowser': (browser,),
                }
                with yt_dlp.YoutubeDL(opts) as ydl:
                    raw = ydl.extract_info(normalized_url, download=False)
                    safe = ydl.sanitize_info(raw)
                return self._normalize_info(safe)
            except Exception as e:
                last_error = e
                continue

        # All methods failed
        raise RuntimeError("抖音视频解析失败：所有提取方式均未成功。请确认链接有效且视频未被删除。")

    def _try_bilibili_direct(self, url: str) -> Optional[dict]:
        """Try extracting info via direct Bilibili API."""
        try:
            from services.bilibili_service import BilibiliService
            if self._bilibili_svc is None:
                self._bilibili_svc = BilibiliService()
            return self._bilibili_svc.extract_info(url)
        except Exception:
            return None

    def _try_douyin_direct(self, url: str) -> Optional[dict]:
        """Try extracting info via direct Douyin API using Playwright."""
        try:
            from services.douyin_service import DouyinService
            if self._douyin_svc is None:
                self._douyin_svc = DouyinService()
            result = self._douyin_svc.extract_info(url)
            return result
        except RuntimeError as e:
            # Re-raise filtered/unavailable video errors
            raise
        except Exception:
            return None

    def _normalize_info(self, raw_info: dict) -> dict:
        """Normalize raw yt-dlp output to a consistent format."""
        # Handle playlist: use first entry
        entries = raw_info.get('entries')
        if entries and isinstance(entries, list):
            raw_info = entries[0]

        return {
            'id': raw_info.get('id', ''),
            'title': raw_info.get('title', '未知标题'),
            'thumbnail': raw_info.get('thumbnail'),
            'description': raw_info.get('description'),
            'duration': raw_info.get('duration'),
            'duration_str': self._format_duration(raw_info.get('duration')),
            'uploader': raw_info.get('uploader') or raw_info.get('channel'),
            'view_count': raw_info.get('view_count'),
            'webpage_url': raw_info.get('webpage_url') or raw_info.get('original_url'),
            'formats': self._parse_formats(raw_info.get('formats', [])),
        }

    def _parse_formats(self, formats: list) -> list[dict]:
        """Parse and categorize formats into video+audio / video only / audio only."""
        combined, video_only, audio_only = [], [], []

        for f in formats:
            # Skip formats with no URL or storyboard entries
            if f.get('url') is None:
                continue
            if f.get('format_note') == 'storyboard':
                continue

            vcodec = f.get('vcodec', 'none') or 'none'
            acodec = f.get('acodec', 'none') or 'none'

            filesize = f.get('filesize') or f.get('filesize_approx')

            entry = {
                'format_id': f['format_id'],
                'quality': self._quality_label(f),
                'ext': f.get('ext', 'unknown'),
                'filesize': filesize,
                'filesize_str': self._format_size(filesize),
                'note': f.get('format_note'),
            }

            if vcodec != 'none' and acodec != 'none':
                entry['type'] = 'video+audio'
                combined.append(entry)
            elif vcodec != 'none' and acodec == 'none':
                entry['type'] = 'video only'
                video_only.append(entry)
            elif vcodec == 'none' and acodec != 'none':
                entry['type'] = 'audio only'
                audio_only.append(entry)

        def dedup_and_sort(fmts, sort_key='quality'):
            seen = set()
            unique = []
            for fmt in sorted(fmts, key=lambda x: (x.get('filesize') or 0), reverse=True):
                fid = fmt['format_id']
                if fid not in seen:
                    seen.add(fid)
                    unique.append(fmt)
            return unique[:5]

        return dedup_and_sort(combined) + dedup_and_sort(video_only) + dedup_and_sort(audio_only)

    def _quality_label(self, f: dict) -> str:
        """Generate a human-readable quality label."""
        height = f.get('height')
        if isinstance(height, int) and height > 0:
            fps = f.get('fps')
            if isinstance(fps, (int, float)) and fps and fps > 30:
                return f"{height}p{fps}"
            return f"{height}p"
        note = f.get('format_note')
        if note:
            return note
        abr = f.get('abr')
        if abr:
            return f"{abr:.0f}kbps"
        return f.get('ext', 'unknown')

    @staticmethod
    def _format_duration(seconds) -> Optional[str]:
        if seconds is None:
            return None
        h, rem = divmod(int(seconds), 3600)
        m, s = divmod(rem, 60)
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"

    @staticmethod
    def _format_size(size) -> str:
        if size is None:
            return "大小未知"
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"

    # ── Subtitle Extraction ──

    async def extract_subtitles(self, url: str) -> Optional[str]:
        """Extract subtitles for AI summary. Returns combined text or None."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_subs_sync, url)

    def _extract_subs_sync(self, url: str) -> Optional[str]:
        try:
            import yt_dlp
            import httpx
            import re

            opts = {**self.INFO_OPTS}
            cleanup = self._setup_bilibili_cookies(url, opts)
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
            finally:
                if cleanup:
                    cleanup()

            # Try requested_subtitles first (yt-dlp may auto-request based on opts),
            # then fall back to subtitles and automatic_captions in raw info
            subtitles = (
                info.get('requested_subtitles')
                or info.get('subtitles', {})
            )
            auto_captions = info.get('automatic_captions', {})

            preferred = ['zh-Hans', 'zh-CN', 'zh', 'en']
            sub_url = None

            # Search manual subtitles first, then auto captions
            for source in (subtitles, auto_captions):
                if not source:
                    continue
                for lang in preferred:
                    if lang in source:
                        candidates = source[lang]
                        if isinstance(candidates, list) and len(candidates) > 0:
                            sub_url = candidates[0].get('url')
                            if sub_url:
                                break
                if sub_url:
                    break
                # fallback: first available language
                if source:
                    first_key = next(iter(source), None)
                    if first_key:
                        candidates = source[first_key]
                        if isinstance(candidates, list) and len(candidates) > 0:
                            sub_url = candidates[0].get('url')
                            if sub_url:
                                break

            if not sub_url:
                return None

            # Fetch subtitle content
            resp = httpx.get(sub_url, timeout=10.0, follow_redirects=True)
            if resp.status_code != 200:
                return None

            raw_text = resp.text

            # Strip SRT/VTT formatting: remove timestamps, numbers, tags
            lines = raw_text.split('\n')
            clean_lines = []
            for line in lines:
                line = line.strip()
                # Skip empty, numeric-only (SRT index), timestamp lines, WEBVTT header
                if not line:
                    continue
                if line.isdigit():
                    continue
                if '-->' in line:
                    continue
                if line.startswith('WEBVTT'):
                    continue
                if line.startswith('Kind:'):
                    continue
                if line.startswith('Language:'):
                    continue
                # Remove HTML/XML tags
                line = re.sub(r'<[^>]+>', '', line)
                # Remove SRT/VTT style markup like {\an8}
                line = re.sub(r'\{[^}]+\}', '', line)
                if line.strip():
                    clean_lines.append(line.strip())

            text = ' '.join(clean_lines)
            return text[:2000] if text else None

        except Exception:
            return None

    # ── Download ──

    async def download(self, url: str, format_id: str, download_type: str = "video+audio") -> tuple[str, str, str]:
        """Download video. Returns (file_path, filename, mime_type)."""
        download_id = str(uuid.uuid4())[:8]
        download_dir = os.path.join(self.temp_dir, download_id)
        os.makedirs(download_dir, exist_ok=True)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._download_sync, url, format_id, download_dir, download_type
        )

    def _download_sync(self, url: str, format_id: str, download_dir: str, download_type: str = "video+audio") -> tuple[str, str, str]:
        # Use direct Bilibili download if this is a Bilibili format ID (prefixed: va_/v_/a_)
        if ('bilibili.com' in url) and BV_PATTERN.search(url):
            if format_id.startswith(('va_', 'v_', 'a_')):
                return self._download_bilibili_sync(url, format_id, download_dir, download_type)

        # Use direct Douyin download if this is a Douyin format ID (prefixed: nwm_video)
        if 'douyin.com' in url and format_id.startswith('nwm_video'):
            return self._download_douyin_sync(url, format_id, download_dir, download_type)

        import yt_dlp

        # Check if aria2c is available
        aria2c_available = shutil.which('aria2c') is not None

        output_template = os.path.join(download_dir, '%(title)s.%(ext)s')
        opts = {
            'quiet': True,
            'no_warnings': True,
            'format': format_id,
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
            'http_headers': BROWSER_HEADERS,
            'socket_timeout': 30,
            'retries': 5,
            'fragment_retries': 5,
            'file_access_retries': 3,
        }

        # Use aria2c if available (multi-connection parallel downloads = much faster)
        # CRITICAL: --file-allocation=none is required on Windows to avoid prealloc
        # (which writes zeros to entire file before download = minutes of "preparing")
        if aria2c_available:
            opts['external_downloader'] = 'aria2c'
            opts['external_downloader_args'] = [
                '--max-connection-per-server=16',
                '--split=16',
                '--min-split-size=1M',
                '--file-allocation=none',
                '--max-tries=5',
                '--retry-wait=3',
            ]

        # For audio-only downloads, extract audio to mp3
        if download_type == 'audio only':
            opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            if 'merge_output_format' in opts:
                del opts['merge_output_format']

        cleanup = self._setup_bilibili_cookies(url, opts)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
        finally:
            if cleanup:
                cleanup()

        # Find the actual output file
        files = os.listdir(download_dir)
        if not files:
            raise FileNotFoundError("下载完成但没有生成文件")

        file_path = os.path.join(download_dir, files[0])
        filename = files[0]
        # yt-dlp may have put the file in a subdirectory; walk if needed
        if os.path.isdir(file_path):
            for root, _, walk_files in os.walk(file_path):
                if walk_files:
                    file_path = os.path.join(root, walk_files[0])
                    filename = walk_files[0]
                    break

        mime_type = self._get_mime_type(file_path)
        return file_path, filename, mime_type

    def _download_bilibili_sync(self, url: str, format_id: str, download_dir: str, download_type: str) -> tuple[str, str, str]:
        """Download Bilibili video using direct stream URLs + ffmpeg."""
        import httpx
        import subprocess

        bv_match = BV_PATTERN.search(url)
        bvid = bv_match.group(1) if bv_match else ''

        # Get stream URLs from Bilibili service
        from services.bilibili_service import BilibiliService
        if self._bilibili_svc is None:
            self._bilibili_svc = BilibiliService()
        dl_info = self._bilibili_svc.get_download_urls(bvid, format_id)
        if not dl_info:
            raise RuntimeError("无法获取 Bilibili 视频流地址")

        fmt = dl_info['format']
        title = dl_info.get('title', 'video')
        # Sanitize filename
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        output_ext = 'mp3' if download_type == 'audio only' else 'mp4'
        output_path = os.path.join(download_dir, f'{safe_title}.{output_ext}')

        headers = {**BROWSER_HEADERS, 'Referer': f'https://www.bilibili.com/video/{bvid}'}

        if download_type == 'audio only':
            # Download audio stream only
            audio_url = fmt.get('_audio_url', '')
            if not audio_url:
                raise RuntimeError("该格式没有音频流")
            self._download_stream(audio_url, output_path, headers)
        elif download_type == 'video only':
            # Download video stream only
            video_url = fmt.get('_video_url', '')
            if not video_url:
                raise RuntimeError("该格式没有视频流")
            self._download_stream(video_url, output_path, headers)
        else:
            # Download video+audio and merge
            video_url = fmt.get('_video_url', '')
            audio_url = fmt.get('_audio_url', '')
            if not video_url or not audio_url:
                raise RuntimeError("该格式缺少视频或音频流")

            video_tmp = os.path.join(download_dir, f'_video_{uuid.uuid4().hex[:4]}.m4s')
            audio_tmp = os.path.join(download_dir, f'_audio_{uuid.uuid4().hex[:4]}.m4s')

            try:
                self._download_stream(video_url, video_tmp, headers)
                self._download_stream(audio_url, audio_tmp, headers)

                # Merge with ffmpeg
                subprocess.run([
                    'ffmpeg', '-y', '-i', video_tmp, '-i', audio_tmp,
                    '-c', 'copy', '-movflags', '+faststart',
                    output_path,
                ], check=True, capture_output=True)
            finally:
                if os.path.exists(video_tmp):
                    os.unlink(video_tmp)
                if os.path.exists(audio_tmp):
                    os.unlink(audio_tmp)

        filename = os.path.basename(output_path)
        mime_type = self._get_mime_type(output_path)
        return output_path, filename, mime_type

    @staticmethod
    def _download_stream(url: str, dest_path: str, headers: dict):
        """Download a single stream to a file. Uses aria2c if available (fast), falls back to httpx."""
        import subprocess
        import httpx

        aria2c_path = shutil.which('aria2c')
        if aria2c_path:
            # Build aria2c header arguments
            header_args = []
            for k, v in headers.items():
                if k.lower() not in ('accept-encoding',):  # Avoid decompression issues
                    header_args.extend(['--header', f'{k}: {v}'])
            try:
                subprocess.run([
                    aria2c_path,
                    '--max-connection-per-server=16',
                    '--split=16',
                    '--min-split-size=1M',
                    '--file-allocation=none',
                    '--max-tries=5',
                    '--retry-wait=3',
                    '--connect-timeout=15',
                    '--timeout=30',
                    '--dir', os.path.dirname(dest_path),
                    '--out', os.path.basename(dest_path),
                    *header_args,
                    url,
                ], check=True, capture_output=True)
                return
            except subprocess.CalledProcessError:
                # Fall back to httpx on aria2c failure
                pass

        # Fallback: httpx streaming with 1MB chunks
        with httpx.stream('GET', url, headers=headers, timeout=600.0, follow_redirects=True) as resp:
            resp.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in resp.iter_bytes(chunk_size=1048576):
                    f.write(chunk)

    def _download_douyin_sync(self, url: str, format_id: str, download_dir: str, download_type: str) -> tuple[str, str, str]:
        """Download Douyin video using direct CDN URLs."""
        import httpx

        video_id_match = self.DOUYIN_PATTERN.search(url)
        video_id = video_id_match.group(1) if video_id_match else ''

        # Get download URLs from Douyin service
        from services.douyin_service import DouyinService
        if self._douyin_svc is None:
            self._douyin_svc = DouyinService()
        dl_info = self._douyin_svc.get_download_urls(video_id, format_id)
        if not dl_info:
            raise RuntimeError("无法获取抖音视频下载地址")

        fmt = dl_info['format']
        title = dl_info.get('title', 'video')
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        output_ext = 'mp4'
        output_path = os.path.join(download_dir, f'{safe_title}.{output_ext}')

        # Use direct download URL
        download_url = fmt.get('_direct_url') or fmt.get('_download_url', '')
        if not download_url:
            raise RuntimeError("该格式没有可用的下载地址")

        headers = {
            **BROWSER_HEADERS,
            'Referer': f'https://www.douyin.com/video/{video_id}',
        }

        self._download_stream(download_url, output_path, headers)

        filename = os.path.basename(output_path)
        mime_type = self._get_mime_type(output_path)
        return output_path, filename, mime_type

    def cleanup(self, file_path: str):
        """Remove temp files after streaming."""
        abs_path = os.path.abspath(file_path)
        parent_dir = os.path.dirname(abs_path)
        # Walk up to find the temp subdirectory (e.g. downloads/{uuid})
        while parent_dir and os.path.commonpath([parent_dir, self.temp_dir]) != os.path.abspath(self.temp_dir):
            parent_dir = os.path.dirname(parent_dir)
        if parent_dir and parent_dir.startswith(self.temp_dir) and os.path.exists(parent_dir):
            shutil.rmtree(parent_dir, ignore_errors=True)

    def cleanup_old_files(self):
        """Remove all temp files older than 1 hour."""
        import time
        now = time.time()
        if not os.path.exists(self.temp_dir):
            return
        for entry in os.listdir(self.temp_dir):
            entry_path = os.path.join(self.temp_dir, entry)
            try:
                mtime = os.path.getmtime(entry_path)
                if now - mtime > 3600:
                    if os.path.isfile(entry_path):
                        os.remove(entry_path)
                    else:
                        shutil.rmtree(entry_path, ignore_errors=True)
            except OSError:
                pass

    @staticmethod
    def _get_mime_type(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        mime_map = {
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.mkv': 'video/x-matroska',
            '.m4a': 'audio/mp4',
            '.mp3': 'audio/mpeg',
            '.opus': 'audio/opus',
            '.ogg': 'audio/ogg',
        }
        return mime_map.get(ext, 'application/octet-stream')
