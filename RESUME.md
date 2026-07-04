# VideoCatcher — 项目简历内容

## 项目概述

**VideoCatcher** 是一款全栈视频下载与AI内容分析平台，支持 1000+ 网站（YouTube、Bilibili、TikTok、抖音等）的视频信息提取、多格式下载、AI 智能总结、思维导图生成和视频问答功能。

- **GitHub**: https://github.com/liyeaii/VideoCatcher
- **在线演示**: https://liyeaii.github.io/VideoCatcher/

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | React 19, Vite 8, Tailwind CSS 4, Axios, Lucide React |
| **后端** | Python 3.12, FastAPI, Uvicorn, yt-dlp, Playwright, httpx |
| **AI 集成** | Anthropic SDK (Claude), OpenAI SDK (DeepSeek), 双Provider自动切换 |
| **部署** | GitHub Pages（前端）, Render Docker（后端）, GitHub Actions CI/CD |
| **工程化** | Docker, Git, NPM Scripts, Vite Proxy |

---

## 简历描述（项目经历）

### 版本一：通用版（建议放在「项目经历」栏目）

**VideoCatcher — 全栈视频下载与AI分析平台**  
*2025.07 — 至今*  
*个人项目*

- 基于 **React 19 + Vite 8 + Tailwind CSS 4** 构建响应式单页应用，实现视频信息的可视化展示、多格式下载选项及 AI 总结面板，支持桌面端/移动端自适应布局
- 使用 **Python FastAPI** 搭建后端服务，集成 **yt-dlp** 引擎实现 1000+ 网站的视频元数据提取与下载，通过 **Playwright** 无头浏览器突破抖音等平台的 JS 签名反爬机制
- 集成 **Claude / DeepSeek** 双 AI Provider，实现视频字幕智能总结、关键要点提炼、思维导图生成和基于视频内容的自由问答功能，支持 API Key 自动识别与 Provider 自动切换
- 设计 **前后端分离架构**，前端部署至 **GitHub Pages**，后端 Docker 化部署至 **Render Cloud**，通过 **GitHub Actions** 实现推送即部署的 CI/CD 流水线
- 实现跨域图片代理、流式文件下载、TTL 内存缓存等机制，优化用户体验与服务性能

---

### 版本二：技术重点版（适合强调技术深度的岗位）

**VideoCatcher — 多平台视频解析与AI内容引擎**

- **前端架构**：React 19 Composition API 模式自定义 Hooks（`useVideoData`）管理复杂异步状态流（idle → loading → loaded → error），实现视频信息/AI总结/字幕/问答的并行请求与取消控制
- **后端核心**：FastAPI 异步服务 + yt-dlp 引擎，针对 Bilibili 平台实现签名算法逆向（`a_bogus` 参数）突破反爬，通过 Playwright Chromium 拦截抖音 `aweme/detail` API 响应获取无水印视频
- **AI 能力**：自研多Provider抽象层（`AIService`），统一封装 Claude 与 DeepSeek SDK，通过 Prompt Engineering 实现结构化 JSON 输出（总结/要点/思维导图），支持基于视频字幕的上下文问答
- **工程化**：Docker 一键部署（含 FFmpeg 视频合并），Vite Proxy 本地开发代理，Axios 请求拦截器统一错误处理，AbortController 请求取消，blob 流式下载与 Content-Disposition 文件名解析

---

## 核心功能

- 视频链接解析：支持 YouTube、Bilibili、TikTok、抖音 等 1000+ 网站
- 多格式下载：视频+音频 / 仅视频 / 仅音频，可自选清晰度
- AI 智能总结：基于视频字幕自动生成摘要 + 关键要点
- AI 思维导图：将视频内容结构化为层级思维导图
- AI 视频问答：基于视频字幕内容的自由提问
- 字幕提取：自动获取并展示视频字幕

---

## 项目亮点 / 技术难点

1. **多平台适配**：统一抽象 `VideoService` 处理不同平台逻辑，抖音通过 Playwright 浏览器拦截 API 绕过 JS 签名，Bilibili 实现 `a_bogus` 参数算法
2. **AI 双Provider设计**：`AIService` 自动识别 API Key 前缀（`sk-ant` → Claude, `sk-` → DeepSeek），无缝切换 Provider
3. **前后端分离部署**：前端静态资源部署 GitHub Pages，后端 Docker 部署 Render，通过环境变量配置 API 地址，Vite Proxy 解决本地开发跨域
4. **流式下载体验**：`StreamingResponse` + `Content-Length` + Axios `onDownloadProgress` 实现实时进度反馈
5. **图片防盗链代理**：后端代理外部图片资源，绕过 Bilibili 等平台的 Referer 防盗链限制
