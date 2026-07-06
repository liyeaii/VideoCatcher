# 🎬 VideoCatcher — 万能视频下载与 AI 分析平台

<p align="center">
  <b>粘贴链接 → 获取信息 → AI 总结 → 多格式下载</b><br/>
  支持 YouTube、Bilibili、TikTok、抖音等 <b>1000+</b> 网站
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react" alt="React 19"/>
  <img src="https://img.shields.io/badge/Vite-8-646CFF?logo=vite" alt="Vite 8"/>
  <img src="https://img.shields.io/badge/Tailwind-4-06B6D4?logo=tailwindcss" alt="Tailwind 4"/>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python" alt="Python 3.12"/>
  <img src="https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/AI-Claude+DeepSeek-7B5EA7" alt="Claude + DeepSeek"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License"/>
</p>

<p align="center">
  <a href="https://liyeaii.github.io/VideoCatcher/">🖥️ 在线演示</a> &nbsp;|&nbsp;
  <a href="#-部署">🚀 部署指南</a> &nbsp;|&nbsp;
  <a href="#-架构说明">🏗️ 架构</a>
</p>

---

## 📑 目录

1. [架构说明](#-架构说明)
2. [关键 Prompt 与 Vibe Coding 思路](#-关键-prompt-与-vibe-coding-思路)
3. [AI 调用逻辑](#-ai-调用逻辑)
4. [部署步骤（含 DNS/HTTP 说明）](#-部署)

---

## 🏗️ 架构说明

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户浏览器                              │
│                  https://liyeaii.github.io                    │
│                       /VideoCatcher/                          │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS (GitHub Pages CDN)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Pages (前端)                        │
│  React 19 + Vite 8 + Tailwind CSS 4                         │
│  静态资源托管 · 全球 CDN · 自动 HTTPS                          │
└──────────────────────────┬──────────────────────────────────┘
                           │ API 请求
                           │ https://videocatcher-api.onrender.com/api/*
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Render Cloud (后端)                          │
│  Docker Container: Python 3.12 + FastAPI + FFmpeg            │
│  ├─ video_service.py  (yt-dlp 视频引擎)                       │
│  ├─ ai_service.py     (Claude / DeepSeek 双 AI)              │
│  ├─ bilibili_service  (B站签名算法)                            │
│  ├─ douyin_service    (抖音 Playwright 浏览器)                 │
│  └─ TTLCache          (内存缓存层)                            │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| **前端框架** | React 19 + Vite 8 | Composition API 模式，Hooks 驱动 |
| **样式** | Tailwind CSS 4 | 响应式布局，渐变主题，骨架屏动画 |
| **HTTP 客户端** | Axios 1.x | blob 流式下载，请求拦截，AbortController 取消 |
| **图标** | Lucide React | Tree-shakable SVG 图标 |
| **后端框架** | FastAPI + Uvicorn | 异步路由，自动 OpenAPI 文档，流式响应 |
| **视频引擎** | yt-dlp (Python 库导入) | `extract_info()` + `sanitize_info()`，非 subprocess |
| **音视频合并** | FFmpeg | 分离下载后合并为 MP4 / 提取 MP3 192kbps |
| **AI SDK** | Anthropic SDK + OpenAI SDK | 双 Provider 抽象层 |
| **反爬** | Playwright + httpx | 抖音 JS 签名 + B站 cookie 模拟 |
| **部署** | GitHub Pages + Render Docker | 前后端分离，GitHub Actions CI/CD |

### 目录结构

```
VideoCatcher/
├── backend/                          # Python FastAPI 后端
│   ├── main.py                       # 入口：路由注册、CORS、启动事件
│   ├── config.py                     # 环境变量配置（AI Key、缓存 TTL）
│   ├── requirements.txt              # Python 依赖
│   ├── models/
│   │   └── schemas.py                # Pydantic 请求/响应模型
│   ├── services/
│   │   ├── video_service.py          # yt-dlp 封装：信息提取/下载/字幕
│   │   ├── ai_service.py             # 多 Provider AI：总结/问答/思维导图
│   │   ├── bilibili_service.py       # B站直链 API（绕过反爬）
│   │   ├── douyin_service.py         # 抖音 Playwright 浏览器拦截
│   │   ├── a_bogus.py                # B站 a_bogus 签名算法
│   │   └── X-Bogus.js                # JS 签名原版（参考）
│   └── utils/
│       └── cache.py                  # 基于 URL hash 的 TTL 内存缓存
├── frontend/                         # React 19 前端
│   ├── package.json                  # 依赖管理
│   ├── vite.config.js                # Vite 配置（dev proxy 到 localhost:8000）
│   └── src/
│       ├── App.jsx                   # 主组件：状态机驱动 + 功能特性展示
│       ├── main.jsx                  # React 入口
│       ├── index.css                 # Tailwind directives + 自定义动画
│       ├── api/
│       │   └── client.js             # Axios 实例 + API 封装
│       ├── components/
│       │   ├── URLInput.jsx          # Hero 区域：大输入框 + 提交按钮
│       │   ├── VideoInfo.jsx         # 封面+标题+播放量（响应式布局）
│       │   ├── AISummary.jsx         # AI 摘要卡片（紫色强调边框）
│       │   ├── DownloadOptions.jsx   # 分类下载卡片网格
│       │   ├── MindMapPanel.jsx      # AI 思维导图展示
│       │   ├── SubtitlesPanel.jsx    # 字幕查看面板
│       │   ├── AskPanel.jsx          # AI 视频问答面板
│       │   ├── LoadingSkeleton.jsx   # 骨架屏（pulse 动画）
│       │   ├── ErrorMessage.jsx      # 错误提示 + 重试按钮
│       │   └── Footer.jsx            # 免责声明
│       └── hooks/
│           └── useVideoData.js       # 自定义 Hook：状态机管理
├── .claude/
│   ├── settings.json                 # Claude Code 项目配置
│   └── plan.md                       # Vibe Coding 实施记录
├── .github/workflows/
│   └── deploy.yml                    # GitHub Actions 自动部署
├── Dockerfile                        # 开发容器（Python + Node.js + FFmpeg）
├── docker-compose.yml                # 一键启动隔离开发环境
├── render.yaml                       # Render Cloud 部署配置
├── agent.md                          # AI Agent 项目需求描述
├── plan.md                           # 详细实施方案
├── DEPLOY.md                         # 部署配置指南
└── RESUME.md                         # 项目简历/技术亮点
```

### API 接口设计

| 方法 | 路径 | 功能 | 关键实现 |
|------|------|------|----------|
| `GET` | `/api/health` | 健康检查 | 返回 `{"status":"ok"}` |
| `POST` | `/api/video/info` | 视频信息提取 | yt-dlp `extract_info()` + `sanitize_info()`，30 分钟缓存 |
| `POST` | `/api/video/summary` | AI 视频总结 | 字幕提取 → Claude/DeepSeek → JSON 结构化输出，1 小时缓存 |
| `POST` | `/api/video/ask` | AI 视频问答 | 基于视频字幕内容的自由提问 |
| `POST` | `/api/video/mindmap` | AI 思维导图 | 层级结构化 JSON，前端 Markmap 渲染 |
| `POST` | `/api/video/subtitles` | 字幕提取 | yt-dlp `writesubtitles` + `writeautomaticsub` |
| `GET` | `/api/proxy/image` | 图片代理 | 绕过 Bilibili 等平台的 Referer 防盗链 |
| `POST` | `/api/download` | 视频/音频下载 | UUID 临时目录 + `StreamingResponse` + `BackgroundTasks` 清理 |

### 前端状态机（核心设计模式）

```
  IDLE ──submitUrl()──▶ LOADING ──info+summary ok──▶ LOADED
                           │                            │
                           └──error──▶ ERROR ──retry()──▶ LOADING
                                                          
  LOADED ──download()──▶ DOWNLOADING ──complete──▶ LOADED
```

`useVideoData` Hook 实现要点：
- `Promise.allSettled` 并行发起 info + summary 请求，独立失败不互相阻塞
- `AbortController` 取消旧请求，防止快速切换 URL 时状态混乱
- Axios `onDownloadProgress` 实时展示下载进度百分比

---

## 🧠 关键 Prompt 与 Vibe Coding 思路

### 项目 Vibe Coding 流程

本项目 **100% 由 AI（Claude Code）驱动开发**，采用"人供意图 → AI 规划 → AI 编码 → AI 修复 → 人工验证"的 Vibe Coding 工作流：

```
agent.md (需求描述)
    │
    ▼
plan.md (AI 自动生成详细实施方案)
    │
    ▼
.claude/plan.md (迭代开发计划)
    │
    ▼
Claude Code 依次执行:
  1. 项目初始化（目录结构、依赖安装）
  2. 后端核心（video_service → ai_service → 路由注册）
  3. 前端核心（组件开发 → 状态机集成 → Tailwind 样式）
  4. Bug 修复（yaml 转义、字幕 URL 提取等）
  5. 端到端测试验证
    │
    ▼
git commit + GitHub Pages 部署
```

**核心 Vibe Coding 策略：**
- 用自然语言 `agent.md` 描述项目需求，AI 自行理解并生成方案
- `plan.md` 作为 AI 的"施工图"，包含技术选型、目录结构、API 设计、实现步骤
- `.claude/settings.json` 配置 `Bash(*)` 权限，让 AI 直接执行命令
- 每个 Phase 后 AI 自行 `git commit`，形成可追溯的开发历史

### 关键 Prompt 设计

#### 1. 视频总结 System Prompt（`ai_service.py`）

```
你是一个专业的视频内容总结助手。请根据提供的视频元数据（标题、简介、字幕）
生成一份简洁且有洞察力的中文总结。

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
}
```

**设计思路：**
- **角色设定**（"专业的视频内容总结助手"）让模型进入内容摘要角色
- **结构约束**（2-3 句总结 + 3-5 个要点）防止过短或过长
- **场景分支**（教程/娱乐分类处理）提升不同视频类型的输出质量
- **强制 JSON 输出**（`只返回JSON，不要有其他文字`）—— 这是关键，确保程序可解析；解析失败时有 fallback 逻辑将整段文本作为 summary

#### 2. 思维导图生成 Prompt

```
根据以下视频信息生成思维导图JSON。
[视频标题+简介+字幕内容]
生成一个层级思维导图，theme为视频标题，children为主要话题，
每个话题下2-4个子要点。严格JSON格式：
{"theme":"...","children":[{"label":"...","children":[{"label":"..."}]}]}
```

**设计思路：**
- **层级约束**（theme → children → grandchildren）确保输出可渲染
- **数量限制**（2-4 个子要点）防止生成过于扁平或过于深的树
- **严格 JSON 格式**让前端 Markmap 组件直接可视化

#### 3. 视频问答 Prompt

```
根据以下视频信息回答用户问题。
[视频上下文信息]
用户问题：{question}
请用中文简洁回答（不超过200字）：
```

**设计思路：**
- **上下文注入**（标题+简介+字幕）作为 RAG 知识库
- **长度限制**（200 字）避免在聊天界面中输出过长
- **系统角色**（"视频内容问答助手"）约束回答范围，减少幻觉

#### 4. AI 请求的 User Message 构造

```python
def _build_user_message(self, title, description, uploader, duration_str, subtitles):
    parts = [f"标题：{title}"]
    if uploader:  parts.append(f"频道：{uploader}")
    if duration_str: parts.append(f"时长：{duration_str}")
    parts.append(f"简介：{description or '无简介'}")
    parts.append(f"字幕内容：{subtitles or '无可用字幕'}")
    return "\n".join(parts)
```

**设计思路：**
- **字段标签化**（中文字段名）让模型明确理解每个字段含义
- **缺失值处理**（`'无简介'`、`'无可用字幕'`）避免 None 值导致 Prompt 歧义
- **字幕截断**：简介截断 3000 字，字幕截断 2000 字，控制 token 消耗

---

## 🤖 AI 调用逻辑

### 双 Provider 自动切换架构

```
                     ┌─────────────────────┐
                     │    AIService 类      │
                     │   (多Provider抽象层)   │
                     └──────────┬──────────┘
                                │
                    API Key 前缀自动识别
                     ┌──────────┴──────────┐
                     │                     │
               sk-ant-api...           sk-xxxxxxxx...
                     │                     │
                     ▼                     ▼
         ┌─────────────────┐   ┌─────────────────────┐
         │  Claude Provider │   │  DeepSeek Provider   │
         │  Anthropic SDK   │   │  OpenAI-compatible   │
         │  model: claude-  │   │  model: deepseek-    │
         │  sonnet-4-...    │   │  chat                │
         └────────┬────────┘   └──────────┬──────────┘
                  │                       │
                  │  async to_thread       │  async to_thread
                  │  messages.create       │  chat.completions.create
                  │                       │
                  ▼                       ▼
              JSON 响应解析 + Fallback 处理
```

### Provider 自动识别逻辑（`_resolve_provider_and_model`）

```python
def _resolve_provider_and_model(self):
    if self.provider == "auto":
        if self.api_key and self.api_key.startswith("sk-ant"):
            self.provider = "claude"      # Anthropic key
        else:
            self.provider = "deepseek"    # 默认走 DeepSeek

    if not self.model:
        self.model = self.PROVIDERS.get(self.provider, {}).get(
            "default_model", "deepseek-chat"
        )
```

**关键设计：**
- **零配置切换**：用户只需设置 `AI_API_KEY`，系统自动识别 Provider，无需额外配置
- **前缀匹配**：Anthropic Key 以 `sk-ant` 开头，DeepSeek Key 以 `sk-` 开头
- **配置优先级**：显式 `AI_PROVIDER=claude` > 自动检测 > 默认 DeepSeek

### 异步调用模式

```python
# Claude: Anthropic SDK 是同步的 → asyncio.to_thread 包装
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

# DeepSeek: OpenAI SDK 也是同步的 → 同样 asyncio.to_thread
async def _call_deepseek(self, user_message: str) -> str:
    from openai import OpenAI
    base_url = self.PROVIDERS["deepseek"]["base_url"]
    client = OpenAI(api_key=self.api_key, base_url=base_url)
    response = await asyncio.to_thread(
        client.chat.completions.create,
        model=self.model,
        max_tokens=1024,
        temperature=0.7,
        messages=[...],
    )
    return response.choices[0].message.content
```

**为什么用 `asyncio.to_thread`：**
- Anthropic SDK 和 OpenAI SDK 的同步调用会阻塞 FastAPI 的 event loop
- `asyncio.to_thread` 将阻塞调用放入线程池，保持 FastAPI 异步非阻塞特性
- 多个并发请求不会互相阻塞

### JSON 响应解析与容错

```python
def _parse_json_response(self, raw_text: str, default: dict = None) -> dict:
    text = raw_text.strip()
    # 处理 markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:]) if len(lines) > 1 else text
        if text.endswith("```"):
            text = text[:-3]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return default or {}  # fallback

def _parse_response(self, raw_text: str) -> dict:
    data = self._parse_json_response(raw_text)
    if not data:
        # JSON 解析失败 → 整段文本作为 summary
        return {"summary": raw_text.strip(), "key_points": []}
    return {
        "summary": data.get("summary", ""),
        "key_points": data.get("key_points", []),
    }
```

**容错策略：**
1. 剥离 Markdown ` ```json ``` ` 包裹
2. `json.loads` 解析
3. 失败 → 返回 `default`（空字典）
4. 最终 fallback：整段文本作为 summary，key_points 为空数组

### 字幕提取策略

```
优先级链：
1. info['subtitles']     ← 手动字幕（最佳质量）
   ├─ zh-Hans / zh / en  按语言偏好降级
2. info['automatic_captions']  ← 自动生成字幕
   ├─ zh-Hans / zh / en
3. yt-dlp writesubtitles  ← 下载字幕文件
4. httpx 直接请求字幕 URL   ← 备用方案
5. None → Prompt 标注"无可用字幕"
```

### AI 调用链路（完整流程）

```
用户粘贴 URL
    │
    ▼
POST /api/video/info     ─── yt-dlp extract_info()
    │                          ├─ 查缓存 (TTL 1800s)
    │                          └─ 返回标准化 JSON
    ▼
POST /api/video/summary  ─── AIService.generate_summary()
    │                          ├─ 提取字幕（优先级链）
    │                          ├─ _build_user_message()
    │                          ├─ _call_claude() / _call_deepseek()
    │                          ├─ _parse_response() → JSON
    │                          └─ 存入 summary 缓存 (TTL 3600s)
    ▼
前端并行渲染：VideoInfo + AISummary + DownloadOptions
```

---

## 🚀 部署

### 部署架构（DNS / HTTP 详解）

```
                            DNS 解析
                    ┌─────────────────────┐
                    │  liyeaii.github.io   │  ← GitHub Pages 免费域名
                    │  (A 记录 → GitHub CDN) │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
      ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
      │ 全球 CDN 边缘  │ │ 全球 CDN 边缘  │ │ 全球 CDN 边缘  │
      │ (Fastly)     │ │ (Fastly)     │ │ (Fastly)     │
      └──────────────┘ └──────────────┘ └──────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  GitHub Pages 源站   │
                    │  /VideoCatcher/      │
                    │  (静态文件: HTML/JS/  │
                    │   CSS/Images)       │
                    └─────────────────────┘

        ═══════════ 前后端分离 ═══════════

                    ┌─────────────────────┐
                    │ videocatcher-api     │  ← Render 自动分配子域名
                    │ .onrender.com        │     *.onrender.com
                    │ (A 记录 → Render LB)  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Render Load Balancer│
                    │  (TLS 终止 + 路由)    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Docker Container    │
                    │  Python FastAPI      │
                    │  + FFmpeg            │
                    │  Port: 8000          │
                    └─────────────────────┘
```

**HTTP 请求流程：**

```
用户浏览器
  │
  ├─ GET https://liyeaii.github.io/VideoCatcher/
  │   → GitHub Pages CDN → 返回 index.html + JS/CSS bundles
  │
  ├─ POST https://videocatcher-api.onrender.com/api/video/info
  │   → Render LB → Docker Container → yt-dlp → JSON 响应
  │
  └─ POST https://videocatcher-api.onrender.com/api/download
      → Render LB → Docker Container → StreamingResponse → blob 下载
```

**CORS 跨域处理：**
- 前端域名（`liyeaii.github.io`）与后端域名（`videocatcher-api.onrender.com`）不同
- 后端设置 `CORS_ORIGINS=*` 允许任意来源请求
- 生产环境建议改为具体域名：`CORS_ORIGINS=https://liyeaii.github.io`

**本地开发代理（Vite Proxy）：**
```javascript
// vite.config.js — 开发环境将 /api 请求代理到本地后端
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```
这样本地开发时前端 `localhost:5173` 的 `/api/*` 请求自动转发到 `localhost:8000`，无需处理 CORS。

### 步骤一：克隆项目

```bash
git clone https://github.com/liyeaii/VideoCatcher.git
cd VideoCatcher
```

### 步骤二：后端部署（Render Docker）

**方式 A — Render 一键部署（推荐）：**

1. Fork 此仓库到你的 GitHub
2. 在 [Render](https://render.com) 注册账号并连接 GitHub
3. 点击 **New + → Web Service**，选择你的 fork
4. Render 自动读取根目录 `render.yaml`：
   ```yaml
   services:
     - type: web
       name: videocatcher-api
       runtime: docker
       rootDir: backend
       plan: free
       healthCheckPath: /api/health
       envVars:
         - key: AI_API_KEY
           sync: false      # 密钥不同步，需手动设置
         - key: AI_PROVIDER
           value: auto
         - key: CORS_ORIGINS
           value: "*"
   ```
5. 在 Render Dashboard → Environment 中设置 `AI_API_KEY`（你的 Claude 或 DeepSeek API Key）
6. 部署完成后获得后端 URL：`https://videocatcher-api.onrender.com`

**方式 B — 本地/Docker 部署：**

```bash
# 使用 Docker Compose 一键启动（隔离环境）
docker-compose up -d

# 或手动启动后端
cd backend
pip install -r requirements.txt
python main.py
# 后端运行在 http://localhost:8000
```

### 步骤三：前端部署（GitHub Pages）

**自动部署（已配置）：**

推送代码到 `master` 分支后，GitHub Actions 自动执行：

```yaml
# .github/workflows/deploy.yml
- name: Build
  run: cd frontend && npm run build
  env:
    VITE_API_BASE_URL: ${{ vars.VITE_API_BASE_URL || 'https://videocatcher-api.onrender.com' }}

- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v4
  with:
    publish_dir: frontend/dist
```

**首次部署前需配置：**

1. **启用 GitHub Pages：**
   - 仓库 → Settings → Pages
   - Source: **GitHub Actions**（deploy from Actions）

2. **（可选）配置 API 地址变量：**
   - 仓库 → Settings → Secrets and variables → Actions → Variables
   - 添加 `VITE_API_BASE_URL` = `https://你的后端域名`

3. **（可选）自定义域名：**
   - Settings → Pages → Custom domain
   - 填入你的域名（如 `videocatcher.example.com`）
   - 在 DNS 服务商添加 CNAME 记录指向 `liyeaii.github.io`

4. 部署成功后访问：`https://你的用户名.github.io/VideoCatcher/`

### 步骤四：环境变量一览

```bash
# 后端所需环境变量（.env 或 Render Dashboard 设置）

# === AI 配置 ===
AI_API_KEY=sk-ant-api03-xxx...       # 必填。支持 Claude 或 DeepSeek Key
AI_PROVIDER=auto                      # auto / claude / deepseek
AI_MODEL=                             # 留空使用默认模型

# === 服务配置 ===
CORS_ORIGINS=*                        # 生产环境改为前端域名
VIDEO_INFO_CACHE_TTL=1800            # 视频信息缓存秒数（30分钟）
SUMMARY_CACHE_TTL=3600               # AI 总结缓存秒数（1小时）

# === 下载配置 ===
TEMP_DOWNLOAD_DIR=./downloads         # 临时下载目录

# === 平台 Cookie（可选） ===
BILIBILI_COOKIE=your-cookie           # B站 cookie 提升解析成功率
```

### 步骤五：验证部署

```bash
# 1. 健康检查
curl https://videocatcher-api.onrender.com/api/health
# → {"status":"ok"}

# 2. 测试视频解析
curl -X POST https://videocatcher-api.onrender.com/api/video/info \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# 3. 测试 AI 总结
curl -X POST https://videocatcher-api.onrender.com/api/video/summary \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# 4. 访问前端页面
open https://liyeaii.github.io/VideoCatcher/
```

### 部署检查清单

- [ ] GitHub Pages 前端正常加载
- [ ] 后端 `/api/health` 返回 `{"status":"ok"}`
- [ ] YouTube 链接解析成功
- [ ] Bilibili 链接解析成功
- [ ] 抖音链接解析成功
- [ ] AI 总结功能正常（已配置 API Key）
- [ ] 思维导图功能正常
- [ ] 视频问答功能正常
- [ ] 下载文件完整可播放
- [ ] 移动端适配正常

### DNS 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| GitHub Pages 404 | 未启用 Pages 或分支错误 | Settings → Pages → Source: GitHub Actions |
| API 请求 CORS 错误 | 后端 CORS 未配置前端域名 | 设置 `CORS_ORIGINS=https://liyeaii.github.io` |
| 后端 503 AI disabled | `AI_API_KEY` 未设置 | Render Dashboard → Environment 添加 Key |
| 抖音解析失败 | 地域限制或 cookie 过期 | 需要中国大陆 IP 或更新 Playwright cookie |
| Render 冷启动慢 | Free plan 15 分钟无请求会休眠 | 升级付费 plan 或使用 UptimeRobot 保活 |
| 自定义域名 HTTPS | DNS 传播 + SSL 证书签发需要时间 | GitHub Pages 自动签发 Let's Encrypt，等待最多 24 小时 |

---

## 🛠️ 本地开发

```bash
# 1. 启动后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 2. 启动前端（新终端）
cd frontend
npm install
npm run dev
# → http://localhost:5173

# Vite proxy 自动将 /api/* 转发到 localhost:8000
```

---

## 📝 项目灵感与致谢

- 视频引擎：[yt-dlp](https://github.com/yt-dlp/yt-dlp)
- AI 驱动：[Anthropic Claude](https://www.anthropic.com) / [DeepSeek](https://www.deepseek.com)
- 思维导图渲染：[Markmap](https://markmap.js.org/)
- 本项目 100% 由 AI（Claude Code）开发，采用 Vibe Coding 模式

---

## 📄 License

MIT License — 仅供个人学习使用。请遵守各视频平台的 ToS，勿用于商业侵权。

---

<p align="center">
  <sub>🤖 Generated with <a href="https://claude.com/claude-code">Claude Code</a> · Vibe Coded with ❤️</sub>
</p>
