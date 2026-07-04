import asyncio
import json
import os
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
    """Multi-provider AI service: supports Claude (Anthropic) and DeepSeek (OpenAI-compatible)."""

    # Provider configurations
    PROVIDERS = {
        "deepseek": {
            "base_url": "https://api.deepseek.com",
            "default_model": "deepseek-chat",
        },
        "claude": {
            "default_model": "claude-sonnet-4-20250514",
        },
    }

    def __init__(self, api_key: str, model: str = None, provider: str = "auto"):
        self.api_key = api_key
        self.provider = provider
        self.model = model  # will be resolved in __post_init__

        self._resolve_provider_and_model()

    def _resolve_provider_and_model(self):
        """Auto-detect provider from API key prefix, or use explicit setting."""
        if self.provider == "auto":
            # DeepSeek keys start with 'sk-'
            # Anthropic keys start with 'sk-ant-'
            if self.api_key and self.api_key.startswith("sk-ant"):
                self.provider = "claude"
            else:
                self.provider = "deepseek"

        # Set default model per provider
        if not self.model:
            self.model = self.PROVIDERS.get(self.provider, {}).get(
                "default_model", "deepseek-chat"
            )

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    @property
    def is_claude(self) -> bool:
        return self.provider == "claude"

    @property
    def is_deepseek(self) -> bool:
        return self.provider == "deepseek"

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

        if self.is_claude:
            raw_text = await self._call_claude(user_message)
        else:
            raw_text = await self._call_deepseek(user_message)

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

    # ── Claude (Anthropic SDK) ──

    async def _call_claude(self, user_message: str) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)

        response = await asyncio.to_thread(
            client.messages.create,
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    # ── DeepSeek (OpenAI-compatible SDK) ──

    async def _call_deepseek(self, user_message: str) -> str:
        from openai import OpenAI

        base_url = self.PROVIDERS["deepseek"]["base_url"]
        client = OpenAI(api_key=self.api_key, base_url=base_url)

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=self.model,
            max_tokens=1024,
            temperature=0.7,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content

    # ── AI Q&A ──

    async def ask_question(
        self,
        title: str,
        description: Optional[str] = None,
        uploader: Optional[str] = None,
        subtitles: Optional[str] = None,
        question: str = "",
    ) -> str:
        """Answer a user question about the video."""
        context = "\n".join([
            f"视频标题：{title}",
            f"UP主：{uploader or '未知'}",
            f"视频简介：{description or '无'}",
            f"字幕内容：{subtitles or '无'}",
        ])
        prompt = f"根据以下视频信息回答用户问题。\n\n{context}\n\n用户问题：{question}\n\n请用中文简洁回答（不超过200字）："

        if self.is_claude:
            return await self._call_claude_with_system(prompt, "你是视频内容问答助手，根据提供的信息准确回答问题。")
        else:
            return await self._call_deepseek_with_system(prompt, "你是视频内容问答助手，根据提供的信息准确回答问题。")

    # ── Mind Map Generation ──

    async def generate_mindmap(
        self,
        title: str = "",
        description: Optional[str] = None,
        subtitles: Optional[str] = None,
    ) -> dict:
        """Generate a structured mind map from video content."""
        context = "\n".join([
            f"标题：{title}",
            f"简介：{description or '无'}",
            f"字幕：{(subtitles or '无')[:1500]}",
        ])
        prompt = f"根据以下视频信息生成思维导图JSON。\n\n{context}\n\n生成一个层级思维导图，theme为视频标题，children为主要话题，每个话题下2-4个子要点。严格JSON格式：\n{{\"theme\":\"...\",\"children\":[{{\"label\":\"...\",\"children\":[{{\"label\":\"...\"}}]}}]}}"

        if self.is_claude:
            raw = await self._call_claude_with_system(prompt, "你是知识整理专家，输出简洁的中文思维导图JSON。")
        else:
            raw = await self._call_deepseek_with_system(prompt, "你是知识整理专家，输出简洁的中文思维导图JSON。")

        return self._parse_json_response(raw, default={"theme": title, "children": []})

    # ── Unified AI call methods ──

    async def _call_claude_with_system(self, user_message: str, system: str) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)
        response = await asyncio.to_thread(
            client.messages.create,
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    async def _call_deepseek_with_system(self, user_message: str, system: str) -> str:
        from openai import OpenAI
        base_url = self.PROVIDERS["deepseek"]["base_url"]
        client = OpenAI(api_key=self.api_key, base_url=base_url)
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=self.model,
            max_tokens=1024,
            temperature=0.7,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content

    # ── Response parsing ──

    def _parse_json_response(self, raw_text: str, default: dict = None) -> dict:
        """Parse JSON, stripping markdown fences."""
        text = raw_text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:]) if len(lines) > 1 else text
            if text.endswith("```"):
                text = text[:-3]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return default or {}

    def _parse_response(self, raw_text: str) -> dict:
        """Parse JSON response, with fallback for non-JSON output."""
        data = self._parse_json_response(raw_text)
        if not data:
            return {"summary": raw_text.strip(), "key_points": []}
        return {
            "summary": data.get("summary", ""),
            "key_points": data.get("key_points", []),
        }
