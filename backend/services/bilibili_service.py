"""
Direct Bilibili API client — bypasses yt-dlp for Bilibili video extraction.
Uses Bilibili's official web API which is more reliable than yt-dlp's extractor.

Quality notes:
- Without login cookies: max 480p (Bilibili restriction)
- With SESSDATA cookie: up to 1080p/4K depending on video
- Set BILIBILI_COOKIE in .env or pass cookies via API for higher quality
"""

import hashlib
import os
import re
import time
import urllib.parse
from typing import Optional


# Bilibili BV号正则
BV_PATTERN = re.compile(r'(BV[a-zA-Z0-9]{10})')


# Wbi 签名相关常量（Bilibili 的 API 签名机制）
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com/',
    'Origin': 'https://www.bilibili.com',
}


def _format_size(size: Optional[int]) -> str:
    """Format file size to human-readable string."""
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


def _get_mixin_key(orig: str) -> str:
    """Get the shortened mixin key used for Wbi signing."""
    return ''.join(orig[i] for i in MIXIN_KEY_ENC_TAB if i < len(orig))[:32]


def _sign_params(params: dict, img_key: str, sub_key: str) -> dict:
    """Add Wbi signature to API parameters."""
    mixin_key = _get_mixin_key(img_key + sub_key)
    wts = int(time.time())
    params['wts'] = wts
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    query = urllib.parse.urlencode(sorted_params)
    w_rid = hashlib.md5((query + mixin_key).encode()).hexdigest()
    params['w_rid'] = w_rid
    return params


def _get_wbi_keys(client) -> tuple[str, str]:
    """Fetch the Wbi sign keys from Bilibili's nav API."""
    import httpx
    try:
        resp = client.get(
            'https://api.bilibili.com/x/web-interface/nav',
            headers=HEADERS,
            timeout=10.0,
        )
        data = resp.json().get('data', {})
        wbi_img = data.get('wbi_img', {})
        img_url = wbi_img.get('img_url', '')
        sub_url = wbi_img.get('sub_url', '')
        img_key = img_url.split('/')[-1].split('.')[0] if img_url else ''
        sub_key = sub_url.split('/')[-1].split('.')[0] if sub_url else ''
        return img_key, sub_key
    except Exception:
        return '', ''


# Codec priority: H.264/AVC > HEVC > AV1 (AVC has best browser compatibility)
CODEC_RANK = {'avc': 0, 'hev': 1, 'av0': 2, 'av1': 2}


def _codec_rank(codecs: str) -> int:
    """Rank codec for deduplication: lower = better (AVC preferred for compatibility)."""
    c = codecs.lower()[:4] if codecs else ''
    return CODEC_RANK.get(c, 99)


class BilibiliService:
    """Direct Bilibili API client."""

    def __init__(self, cookie_str: str = ""):
        self._cookie_str = cookie_str or os.getenv("BILIBILI_COOKIE", "")
        self._wbi_keys = None
        self._wbi_keys_time = 0
        self._client = None

    def _get_client(self):
        """Get or create an httpx client with Bilibili cookies."""
        import httpx
        from urllib.parse import unquote
        if self._client is None:
            self._client = httpx.Client(
                headers=HEADERS,
                timeout=httpx.Timeout(15.0),
                follow_redirects=True,
            )
            # Visit homepage to get basic cookies (buvid3, b_nut)
            try:
                self._client.get('https://www.bilibili.com/')
            except Exception:
                pass
            # Add user-provided cookies (e.g., SESSDATA for login → unlocks 1080p+)
            if self._cookie_str:
                for part in self._cookie_str.split(';'):
                    part = part.strip()
                    if '=' in part:
                        k, v = part.split('=', 1)
                        k, v = k.strip(), unquote(v.strip())
                        # Bilibili cookies need .bilibili.com domain
                        self._client.cookies.set(k, v, domain='.bilibili.com', path='/')
        return self._client

    def _get_wbi_signed_params(self, base_params: dict) -> dict:
        """Get WBI-signed params, refreshing keys if needed."""
        now = time.time()
        if self._wbi_keys is None or now - self._wbi_keys_time > 3600:
            self._wbi_keys = _get_wbi_keys(self._get_client())
            self._wbi_keys_time = now

        img_key, sub_key = self._wbi_keys
        if img_key and sub_key:
            return _sign_params(base_params, img_key, sub_key)
        return base_params

    def extract_info(self, url: str) -> Optional[dict]:
        """Extract video metadata from Bilibili URL."""

        bvid = self._extract_bvid(url)
        if not bvid:
            return None

        info = self._get_video_info(bvid)
        if not info:
            return None

        cid = info.get('cid', 0)
        duration = info.get('duration', 0)
        formats = self._get_video_formats(bvid, cid, duration)

        return self._normalize(info, formats, bvid)

    def _extract_bvid(self, url: str) -> Optional[str]:
        """Extract BV id from URL."""
        match = BV_PATTERN.search(url)
        if match:
            return match.group(1)
        return None

    def _get_video_info(self, bvid: str) -> Optional[dict]:
        """Call Bilibili's video view API."""
        try:
            params = self._get_wbi_signed_params({'bvid': bvid})
            resp = self._get_client().get(
                'https://api.bilibili.com/x/web-interface/view',
                params=params,
            )
            data = resp.json()
            if data.get('code') != 0:
                return None
            return data['data']
        except Exception:
            return None

    def _get_video_formats(self, bvid: str, cid: int, duration: int = 0) -> list[dict]:
        """Call Bilibili's player API to get video/audio stream URLs."""
        try:
            params = self._get_wbi_signed_params({
                'bvid': bvid,
                'cid': cid,
                'qn': 127,
                'fnval': 4048,
                'fourk': 1,
            })
            resp = self._get_client().get(
                'https://api.bilibili.com/x/player/wbi/playurl',
                params=params,
            )
            data = resp.json()
            if data.get('code') != 0:
                return []
            dash = data.get('data', {}).get('dash', {})
            return self._parse_dash_formats(dash, duration)
        except Exception:
            return []

    def _parse_dash_formats(self, dash: dict, duration: int = 0) -> list[dict]:
        """Parse DASH formats. Deduplicate by resolution, keep best codec per tier."""
        formats = []

        videos = dash.get('video', [])
        audios = dash.get('audio', [])

        if not videos:
            return formats

        # Deduplicate video streams: one per resolution, keep best codec (AVC > HEVC > AV1)
        resolution_best = {}
        for v in videos:
            height = v.get('height', 0)
            fps = v.get('frame_rate', '')
            key = f'{height}p{fps}'
            existing = resolution_best.get(key)
            if existing is None or _codec_rank(v.get('codecs', '')) < _codec_rank(existing.get('codecs', '')):
                resolution_best[key] = v

        # Sort by resolution descending
        sorted_videos = sorted(resolution_best.values(), key=lambda v: v.get('height', 0), reverse=True)

        # Best audio for combined formats
        best_audio = max(audios, key=lambda a: a.get('bandwidth', 0)) if audios else None

        # ── 1. Video+Audio combined (mp4 output after ffmpeg merge) ──
        for v in sorted_videos:
            codecs = v.get('codecs', '')
            height = v.get('height', 0)
            fps = v.get('frame_rate', '')
            quality = f'{height}p{fps}' if fps and fps != '30.0' else f'{height}p'

            v_bw = v.get('bandwidth', 0)
            a_bw = best_audio.get('bandwidth', 0) if best_audio else 0
            est_size = int((v_bw + a_bw) * duration / 8) if duration > 0 else None

            fmt = {
                'format_id': f'va_{v["id"]}',  # va = video+audio combined
                'quality': quality,
                'type': 'video+audio',
                'ext': 'mp4',
                'filesize': est_size,
                'filesize_str': _format_size(est_size),
                'note': f"{'最佳编码' if _codec_rank(codecs)==0 else ''} {height}p".strip(),
            }
            if v.get('base_url'):
                fmt['_video_url'] = v['base_url']
                fmt['_video_backup'] = v.get('backup_url', [])
                if best_audio and best_audio.get('base_url'):
                    fmt['_audio_url'] = best_audio['base_url']
                    fmt['_audio_backup'] = best_audio.get('backup_url', [])
            formats.append(fmt)

        # ── 2. Video only ──
        for v in sorted_videos:
            height = v.get('height', 0)
            v_bw = v.get('bandwidth', 0)
            est_size = int(v_bw * duration / 8) if duration > 0 else None
            codecs = v.get('codecs', '')

            fmt = {
                'format_id': f'v_{v["id"]}',  # v = video only
                'quality': f'{height}p',
                'type': 'video only',
                'ext': 'mp4',
                'filesize': est_size,
                'filesize_str': _format_size(est_size),
                'note': f'仅画面' + (f' ({codecs})' if codecs else ''),
            }
            if v.get('base_url'):
                fmt['_video_url'] = v['base_url']
                fmt['_video_backup'] = v.get('backup_url', [])
            formats.append(fmt)

        # ── 3. Audio only (converted to mp3 by ffmpeg) ──
        for a in sorted(audios, key=lambda a: a.get('bandwidth', 0), reverse=True):
            bandwidth = a.get('bandwidth', 0)
            est_size = int(bandwidth * duration / 8) if duration > 0 else None

            fmt = {
                'format_id': f'a_{a["id"]}',  # a = audio only
                'quality': f'{bandwidth // 1000}kbps',
                'type': 'audio only',
                'ext': 'mp3',
                'filesize': est_size,
                'filesize_str': _format_size(est_size),
                'note': None,
            }
            if a.get('base_url'):
                fmt['_audio_url'] = a['base_url']
                fmt['_audio_backup'] = a.get('backup_url', [])
            formats.append(fmt)

        return formats

    def get_download_urls(self, bvid: str, format_id: str) -> Optional[dict]:
        """Get the actual stream URLs for a specific format (for download)."""
        try:
            info = self._get_video_info(bvid)
            if not info:
                return None
            cid = info.get('cid', 0)
            duration = info.get('duration', 0)
            formats = self._get_video_formats(bvid, cid, duration)
            for f in formats:
                if f['format_id'] == format_id:
                    return {
                        'format': f,
                        'title': info.get('title', 'video'),
                        'bvid': bvid,
                        'cid': cid,
                    }
            return None
        except Exception:
            return None

    def _normalize(self, info: dict, formats: list[dict], bvid: str) -> dict:
        """Normalize Bilibili API response to VideoCatcher standard format."""
        stat = info.get('stat', {})
        owner = info.get('owner', {})

        duration = info.get('duration')
        if duration:
            h, rem = divmod(duration, 3600)
            m, s = divmod(rem, 60)
            duration_str = f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m}:{s:02d}"
        else:
            duration_str = None

        # Convert to HTTPS (Bilibili CDN serves both http and https)
        thumbnail = info.get('pic', '') or ''
        if thumbnail.startswith('http://'):
            thumbnail = 'https://' + thumbnail[7:]

        return {
            'id': bvid,
            'title': info.get('title', '未知标题'),
            'thumbnail': thumbnail,
            'description': info.get('desc', ''),
            'duration': duration,
            'duration_str': duration_str,
            'uploader': owner.get('name', ''),
            'view_count': stat.get('view', 0),
            'webpage_url': f'https://www.bilibili.com/video/{bvid}',
            'formats': formats,
            '_bili_cid': info.get('cid', 0),
        }
