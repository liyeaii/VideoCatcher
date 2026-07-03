import asyncio
import json
from typing import Optional

SYSTEM_PROMPT = """你是一个专业的视频内容总结助手。请根据提供的视频元数据（标题、简介、字幕）生成一份简洁且有洞察力的中文总结。

要求：
1. 总结长度控制在2-3句话，点明视频核心内容
2. 提炼3-5个关键要点
3. 如果视频是教程类，指出学到的技能
4. 如果视频是娱乐类，指出精彩看点
5. 语气简洁专业

请严格按照以下JSON格式回复（只返回JSON，不要有其他文字）：
{
  "summary": "...",
  "key_points": ["...", "..."]
}"""


class AIService:
    """Wrapper around Anthropic Claude API for video summarization."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-5"):
        self.api_key = api_key
        self.model = model
        self._client = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key != "your_api_key_here")

    @property
    def client(self):
        if self._client is None and self.is_configured:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    async def generate_summary(
        self,
        title: str,
        description: Optional[str] = None,
        uploader: Optional[str] = None,
        duration_str: Optional[str] = None,
        subtitles: Optional[str] = None,
    ) -> dict:
        """Generate AI summary of video content. Returns {summary, key_points}."""

        user_message = self._build_user_message(
            title, description, uploader, duration_str, subtitles
        )

        response = await asyncio.to_thread(
            self.client.messages.create,
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        raw_text = response.content[0].text
        return self._parse_response(raw_text)

    def _build_user_message(self, title, description, uploader, duration_str, subtitles):
        parts = [f"标题：{title}"]
        if uploader:
            parts.append(f"频道：{uploader}")
        if duration_str:
            parts.append(f"时长：{duration_str}")
        parts.append(f"简介：{description or '无简介'}")
        parts.append(f"字幕内容：{subtitles or '无可用字幕'}")
        return "\n".join(parts)

    def _parse_response(self, raw_text: str) -> dict:
        """Parse Claude's JSON response, with fallback for non-JSON output."""
        text = raw_text.strip()
        # Remove markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[-1].strip() == "```":
                text = "\n".join(lines[1:-1])
            else:
                text = "\n".join(lines[1:])

        try:
            data = json.loads(text)
            return {
                "summary": data.get("summary", ""),
                "key_points": data.get("key_points", []),
            }
        except json.JSONDecodeError:
            # Fallback: treat entire response as summary
            return {"summary": raw_text.strip(), "key_points": []}
