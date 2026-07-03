import asyncio
import os
import uuid
import shutil
from typing import Optional


class VideoService:
    """Wrapper around yt-dlp for metadata extraction and downloading."""

    INFO_OPTS = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'writesubtitles': False,
        'writeautomaticsub': False,
    }

    SUBS_OPTS = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['zh-Hans', 'zh', 'en'],
        'subtitlesformat': 'srt',
    }

    def __init__(self, temp_dir: str = "./downloads"):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)

    async def extract_info(self, url: str) -> dict:
        """Extract video metadata. Runs sync yt-dlp in executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_info_sync, url)

    def _extract_info_sync(self, url: str) -> dict:
        # Import locally to avoid import errors on startup
        import yt_dlp

        opts = {
            **self.INFO_OPTS,
            'extract_flat': False,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            raw = ydl.extract_info(url, download=False)
            safe = ydl.sanitize_info(raw)
        return self._normalize_info(safe)

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
            with yt_dlp.YoutubeDL(self.SUBS_OPTS) as ydl:
                info = ydl.extract_info(url, download=False)
            # Check requested_subtitles or subtitles from info dict
            subs = info.get('requested_subtitles') or info.get('subtitles', {})
            if not subs:
                return None
            # Pick best language: zh-Hans > zh > en > first available
            preferred = ['zh-Hans', 'zh-CN', 'zh', 'en']
            sub_data = None
            for lang in preferred:
                if lang in subs:
                    sub_data = subs[lang]
                    break
            if not sub_data and subs:
                sub_data = list(subs.values())[0]
            if not sub_data:
                return None
            # sub_data is a list of dicts; get the first one with 'data'
            if isinstance(sub_data, list) and len(sub_data) > 0:
                text = sub_data[0].get('data', '')
                return text[:2000] if text else None
            return None
        except Exception:
            return None

    # ── Download ──

    async def download(self, url: str, format_id: str) -> tuple[str, str, str]:
        """Download video. Returns (file_path, filename, mime_type)."""
        download_id = str(uuid.uuid4())[:8]
        download_dir = os.path.join(self.temp_dir, download_id)
        os.makedirs(download_dir, exist_ok=True)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._download_sync, url, format_id, download_dir
        )

    def _download_sync(self, url: str, format_id: str, download_dir: str) -> tuple[str, str, str]:
        import yt_dlp

        output_template = os.path.join(download_dir, '%(title)s.%(ext)s')
        opts = {
            'quiet': True,
            'no_warnings': True,
            'format': format_id,
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

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

    def cleanup(self, file_path: str):
        """Remove temp files after streaming."""
        parent_dir = os.path.dirname(file_path)
        # Find the top-level temp dir (downloads/{uuid})
        while parent_dir and os.path.commonpath([parent_dir, self.temp_dir]) != self.temp_dir:
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
