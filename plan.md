# VideoCatcher 万能视频下载器 — 详细实施方案

## 背景

当前 `d:\develop\vscode\VideoCatcher\` 目录仅有 `agent.md` 一份项目简述（输入视频链接 → 展示信息+AI总结 → 多格式下载），尚无任何代码。本方案在其基础上补充技术选型、架构设计、详细实现步骤和测试策略。

---

## 一、技术栈选型

| 层 | 技术 | 理由 |
|---|------|------|
| **后端** | Python 3.12+ / FastAPI | yt-dlp 是 Python 库（`import yt_dlp`），FastAPI 异步能力强、自动生成 Swagger 文档 |
| **前端** | React 18 + Vite + Tailwind CSS | 组件化、构建快、Tailwind 快速构建简洁美观的 UI |
| **视频抓取** | yt-dlp（Python 库导入，而非 subprocess） | 避免进程开销，可直接使用 `extract_info()` + `sanitize_info()` |
| **AI 总结** | Anthropic Claude API（`claude-sonnet-5`） | 质量高、速度快、支持中文；用标题+简介+字幕生成摘要 |
| **音视频合并** | FFmpeg（系统级依赖） | yt-dlp 分离下载音视频流后，需要 FFmpeg 合并为 MP4 / 提取 MP3 |

已有环境：Python 3.12.3、Node.js v24.16.0、npm 11.13.0

---

## 二、项目结构

```
VideoCatcher/
├── backend/
│   ├── main.py                 # FastAPI 入口：CORS、路由注册、启动事件
│   ├── config.py               # 环境变量：ANTHROPIC_API_KEY、CORS Origins、缓存 TTL
│   ├── requirements.txt        # fastapi, uvicorn, yt-dlp, anthropic, python-multipart, python-dotenv
│   ├── .env                    # ANTHROPIC_API_KEY=xxx（gitignore）
│   ├── services/
│   │   ├── video_service.py    # yt-dlp 封装类：extract_info / parse_formats / download / extract_subtitles
│   │   └── ai_service.py       # Claude API 封装类：generate_summary（结构化 JSON 输出）
│   ├── models/
│   │   └── schemas.py          # Pydantic：VideoURLRequest / DownloadRequest / VideoInfoResponse / SummaryResponse
│   └── utils/
│       └── cache.py            # TTLCache：基于 URL hash 的内存缓存，30 分钟过期
├── frontend/
│   ├── index.html
│   ├── package.json            # react, react-dom, axios, lucide-react
│   ├── vite.config.js          # dev server 代理 /api → localhost:8000
│   ├── tailwind.config.js      # 自定义主题色、动画（fadeIn、pulse-slow）
│   └── src/
│       ├── main.jsx
│       ├── App.jsx             # 主组件：状态机驱动渲染
│       ├── index.css           # Tailwind directives + 自定义动画
│       ├── api/
│       │   └── client.js       # axios 实例 + fetchVideoInfo / fetchSummary / downloadVideo
│       ├── components/
│       │   ├── URLInput.jsx         # Hero 区域：大输入框 + 提交按钮
│       │   ├── VideoInfo.jsx        # 封面+标题+作者+播放量（响应式横排/竖排）
│       │   ├── AISummary.jsx        # AI 摘要卡片（左侧紫色边框 + 要点列表）
│       │   ├── DownloadOptions.jsx  # 分类下载卡片网格（视频+音频 / 仅视频 / 仅音频）
│       │   ├── LoadingSkeleton.jsx  # 骨架屏（pulse 动画）
│       │   ├── ErrorMessage.jsx     # 错误提示 + 重试按钮
│       │   └── Footer.jsx           # 免责声明
│       └── hooks/
│           └── useVideoData.js      # 自定义 Hook：管理 info + summary + download 全生命周期
└── downloads/                  # 临时下载目录（gitignore，每次启动清理）
```

---

## 三、API 接口设计

### 3.1 `GET /api/health`
- **响应**：`{ "status": "ok" }` ——用于前端检测后端连通性

### 3.2 `POST /api/video/info`
- **请求**：`{ "url": "...", "refresh": false }`
- **处理**：
  1. 校验 URL 合法性
  2. 查缓存（`refresh=false` 时，URL hash 为 key，TTL 30 分钟）
  3. `youtube_dl = YoutubeDL(opts)` → `ydl.extract_info(url, download=False)` → `ydl.sanitize_info(raw)`
  4. 分类 formats：video+audio / video only / audio only，每类取 top 5
  5. 过滤掉无 URL 的格式（如 storyboard）
  6. 返回结构化数据
- **错误**：无效 URL → 400；提取失败 → 502 + `{ error, detail, retryable }`
- **注意**：`sanitize_info()` 必须调用，原始 info_dict 含不可序列化对象

### 3.3 `POST /api/video/summary`
- **请求**：`{ "url": "...", "refresh": false }`
- **处理**：
  1. 从缓存获取 video info（无则调用 info API）
  2. 尝试提取字幕：优先 `subtitles`（手动）→ `automatic_captions`（自动）→ 中/英文 → 截断 2000 字符
  3. 构造 prompt → 调用 Claude API → 解析 JSON 响应（`{ summary, key_points }`）
  4. 存入 summary 缓存（TTL 1 小时）
- **AI Prompt 设计**：
  ```
  你是一个专业的视频内容总结助手。请根据视频元数据生成中文总结：
  要求：2-3句话总结 + 3-5个要点。严格按JSON格式回复。
  标题：{title}  频道：{uploader}  时长：{duration}
  简介：{description}  字幕：{subtitles}
  ```
- **错误**：API Key 未配置 → 503；调用失败 → 502 + retryable

### 3.4 `POST /api/download`
- **请求**：`{ "url": "...", "format_id": "bestvideo[height<=1080]+bestaudio", "type": "video" }`
- **处理**：
  1. 创建 UUID 临时子目录 `downloads/{uuid}/`
  2. yt-dlp 配置：`outtmpl={dir}/%(title)s.%(ext)s`
  3. 视频：`merge_output_format: 'mp4'`；音频：`FFmpegExtractAudio → mp3 192kbps`
  4. `run_in_executor` 异步执行下载（yt-dlp 是同步的）
  5. 查找输出文件 → `StreamingResponse` 返回文件流
  6. 通过 `BackgroundTasks` 在传输完成后清理临时文件
- **响应头**：`Content-Disposition: attachment; filename="xxx.mp4"`（Unicode 文件名需 URL 编码）
- **错误**：下载失败 → 502 + retryable

---

## 四、前端组件设计

### 4.1 状态机（useVideoData Hook）

```
IDLE ──submitUrl()──▶ LOADING ──info+summary ok──▶ LOADED
                        │                              │
                        └──error──▶ ERROR ──retry()──▶ LOADING
                                                      
LOADED ──download()──▶ DOWNLOADING ──complete──▶ LOADED
```

Hook 暴露：`{ phase, videoInfo, summary, formats, error, downloadingId, submitUrl, retry, reset, download }`

关键实现：
- `submitUrl` 并行发起 info 和 summary 两个请求（用 `Promise.allSettled`，独立失败不互相阻塞）
- 新 URL 提交时用 `AbortController` 取消进行中的旧请求
- download 用 Axios `responseType: 'blob'` + `URL.createObjectURL` 触发浏览器下载

### 4.2 组件明细

| 组件 | 视觉要点 |
|------|---------|
| **URLInput** | Hero 区域，渐变背景（indigo→purple），大圆角输入框，placeholder "粘贴视频链接...支持 YouTube、Bilibili 等 1000+ 网站" |
| **LoadingSkeleton** | `animate-pulse` 骨架屏，矩形占位模拟缩略图+文字布局 |
| **VideoInfo** | 响应式：桌面端左图右文（40/60），移动端竖排；描述默认折叠 3 行，可展开 |
| **AISummary** | 左侧紫色边框强调，✨ 图标 + "AI 智能总结" 标签 + "由 Claude 生成"，要点使用圆点列表 |
| **DownloadOptions** | 分组："视频+音频（推荐）" / "仅视频" / "仅音频"，卡片网格，最佳画质用金色边框突出 |
| **ErrorMessage** | 红色卡片 + 感叹号图标 + 错误详情 + "重试"按钮 |
| **Footer** | "Powered by yt-dlp + Claude AI | 仅供个人学习使用" |

### 4.3 配色方案

```
主色调：    from-indigo-600 to-purple-600（渐变）
主按钮：    bg-indigo-600 hover:bg-indigo-700 text-white
AI 强调：   from-violet-500 to-purple-500
成功：      bg-emerald-500
错误：      bg-red-50 border-red-300 text-red-800
背景：      bg-gray-50
卡片：      bg-white rounded-2xl shadow-md
最佳推荐：  border-2 border-amber-300 bg-amber-50
```

---

## 五、后端核心实现细节

### 5.1 `video_service.py`

```python
class VideoService:
    INFO_OPTS = {'quiet': True, 'no_warnings': True, 'skip_download': True}
    SUBS_OPTS = {'quiet': True, 'skip_download': True, 'writesubtitles': True,
                 'writeautomaticsub': True, 'subtitleslangs': ['zh-Hans', 'zh', 'en']}

    async def extract_info(self, url: str) -> dict:
        """run_in_executor 中执行同步 yt-dlp，返回标准化数据"""
        # 1. ydl.extract_info(url, download=False)
        # 2. _normalize_info(raw) → {id, title, thumbnail, description, ...}
        # 3. _parse_formats(raw['formats']) → 按 vcodec/acodec 分三类

    def _parse_formats(self, formats: list) -> list:
        """过滤无URL的格式，跳过storyboard，按类型分类，每类去重取top5"""
        # video+audio: vcodec!='none' AND acodec!='none'
        # video only:  vcodec!='none' AND acodec=='none'
        # audio only:  vcodec=='none' AND acodec!='none'

    async def extract_subtitles(self, url: str) -> Optional[str]:
        """提取字幕文本，截断至2000字符，失败返回None（不阻塞摘要生成）"""

    async def download(self, url: str, format_id: str) -> tuple[str, str, str]:
        """返回 (file_path, filename, mime_type)，用UUID子目录隔离"""
```

### 5.2 `ai_service.py`

```python
class AIService:
    def __init__(self, api_key: str, model: str = "claude-sonnet-5"):
        self.client = anthropic.Anthropic(api_key=api_key)

    async def generate_summary(self, title, description, uploader, duration, subtitles) -> dict:
        """asyncio.to_thread 调用 Claude → 解析 JSON → 返回 {summary, key_points}"""
        # JSON 解析失败时 fallback：整段文本作为 summary
```

### 5.3 `cache.py` — TTLCache

- `_hash_key(url)` → SHA256 前 16 位
- 内部 `dict[str, tuple[value, expiry_time]]`
- `get()` 自动过期检查
- info 缓存 TTL=1800s，summary 缓存 TTL=3600s

### 5.4 `config.py` — 环境变量

```python
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
VIDEO_INFO_CACHE_TTL = int(os.getenv("VIDEO_INFO_CACHE_TTL", "1800"))
SUMMARY_CACHE_TTL = int(os.getenv("SUMMARY_CACHE_TTL", "3600"))
TEMP_DOWNLOAD_DIR = os.getenv("TEMP_DOWNLOAD_DIR", "./downloads")
```

---

## 六、分步实现计划

### 第 1 步：项目初始化与环境搭建
- 创建完整目录结构
- `pip install fastapi uvicorn yt-dlp anthropic python-multipart python-dotenv`
- Vite 初始化 React 项目，安装 Tailwind CSS、axios、lucide-react
- `vite.config.js` 配置 `/api` 代理到 `localhost:8000`
- `tailwind.config.js` 自定义主题色和动画
- 后端配置 CORS，创建 `.env` 和 `.gitignore`
- **验证**：`uvicorn main:app --reload` 启动成功，FastAPI 文档页可访问

### 第 2 步：后端 — 视频信息提取
- 实现 `config.py`、`cache.py`、`models/schemas.py`
- 实现 `video_service.py`（extract_info + _parse_formats + _normalize_info）
- 在 `main.py` 注册 `GET /api/health` 和 `POST /api/video/info`
- **验证**：curl 测试 YouTube/Bilibili 真实链接，确认返回完整 JSON（title, thumbnail, formats 等）

### 第 3 步：后端 — AI 总结 + 下载
- 实现 `ai_service.py`（generate_summary + 字幕提取）
- 在 `main.py` 注册 `POST /api/video/summary`
- 实现 `video_service.py` 的 `download()` 方法
- 在 `main.py` 注册 `POST /api/download`（StreamingResponse + BackgroundTasks 清理）
- **验证**：curl 三个接口，下载文件确认可播放

### 第 4 步：前端 — 基础框架
- 实现 `api/client.js`（axios 封装 + 错误标准化）
- 实现 `App.jsx`（状态机骨架）、`useVideoData.js` Hook
- 实现 `URLInput.jsx`、`LoadingSkeleton.jsx`、`ErrorMessage.jsx`、`Footer.jsx`
- **验证**：浏览器中输入 URL，观察加载态切换和错误态展示

### 第 5 步：前端 — 结果展示 + 下载
- 实现 `VideoInfo.jsx`（响应式布局、描述折叠）
- 实现 `AISummary.jsx`（打字动画、要点列表）
- 实现 `DownloadOptions.jsx`（分类卡片、下载触发、进度展示）
- 串接完整流程，用 AbortController 处理请求取消
- **验证**：端到端流程 — 输入链接 → 展示信息 → 查看摘要 → 点击下载

### 第 6 步：整体测试与 Bug 修复
- 多平台：YouTube、Bilibili、Twitter/X、Vimeo（至少 4 种）
- 边界情况：无效 URL、私有/已删除视频、直播、超长标题、无字幕、大文件
- 错误处理全覆盖：后端宕机、网络断开、API Key 未配置
- UI 打磨：移动端适配（320~1440px）、hover 动效、加载过渡

---

## 七、关键依赖

```bash
# 后端（pip install）
fastapi uvicorn[standard] yt-dlp anthropic python-multipart python-dotenv

# 前端（npm）
npm create vite@latest . -- --template react
npm install axios lucide-react
npm install -D tailwindcss @tailwindcss/vite

# 系统依赖（单独安装并加入 PATH）
# FFmpeg: https://ffmpeg.org/download.html
# 验证: ffmpeg -version
```

---

## 八、边界情况与注意事项

### yt-dlp 相关
| 场景 | 处理 |
|------|------|
| 地域限制视频 | 捕获 GeoRestrictedError，返回明确提示 |
| 私有/已删除视频 | 返回"视频不存在或已设为私密" |
| 直播流 | 检测 `is_live` 字段，返回"直播内容暂不支持下载" |
| 播放列表 URL | 如检测到 `entries`，取第一个视频或提示输入单视频链接 |
| 格式列表超大（100+） | 每类只返回 top 5，避免响应过大 |
| 文件大小未知 | 用 `filesize_approx` 兜底，都没有则显示"大小未知" |

### Claude API 相关
| 场景 | 处理 |
|------|------|
| API Key 未配置 | 返回 503，前端隐藏摘要区，提示"配置 API 密钥以启用 AI 总结" |
| 限流（429） | 返回 retryable 错误，前端显示"稍后重试" |
| JSON 解析失败 | fallback：整段文本作为 summary |
| 简介超长（10000+ 字） | 截断至 3000 字再发送 |
| 无字幕 | Prompt 中标注"无可用字幕"，Claude 基于标题+简介仍可生成 |

### 下载相关
| 场景 | 处理 |
|------|------|
| 大文件（>1GB） | StreamingResponse 支持；前端 Axios onDownloadProgress 显示进度 |
| 并发下载 | 前端同时只允许一个下载进行中 |
| Unicode 文件名 | Content-Disposition 使用 `urllib.parse.quote` 编码 |
| 临时文件清理 | FastAPI BackgroundTasks + 启动时清理 downloads/ 目录 |
| FFmpeg 未安装 | 启动时检测，输出警告日志 |

### 前端相关
| 场景 | 处理 |
|------|------|
| 快速切换 URL | AbortController 取消旧请求 |
| 移动端 | 响应式布局，描述默认折叠，缩略图 lazy loading |
| 无缩略图 | 显示占位图 |
| 无描述 | 显示"暂无简介" |

---

## 九、验证方案

| 验证项 | 方法 |
|--------|------|
| 后端 API 正确性 | curl 测试三个接口，验证 JSON 结构和错误响应 |
| 前端 UI 完整性 | 浏览器中完整用户流程 |
| 多平台兼容 | YouTube、Bilibili、Twitter/X、Vimeo 各测试 1 个链接 |
| 错误处理 | 无效 URL、私有视频、网络断开、无 API Key |
| 文件完整性 | 下载后播放视频/音频，确认时长和内容正确 |
| AI 摘要质量 | 人工审核 3-5 个不同类型视频的摘要准确性 |
| 移动端适配 | Chrome DevTools 模拟 320/768/1024/1440px |
| 缓存验证 | 同一 URL 第二次请求应该更快返回 |
