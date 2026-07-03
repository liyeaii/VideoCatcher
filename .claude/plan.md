# VideoCatcher 继续实施方案

## Context

项目已有完整的后端架构（FastAPI + yt-dlp + Claude AI）和前端基础设施（React 19 + Vite + Tailwind CSS 4）。后端存在 3 个关键 Bug，前端缺 4 个核心组件和主页面集成。需按 core feature 粒度完成并用 git 保存。

## 实施步骤

### 步骤 1：Git 初始化 + 首次提交
- `git init`，首次提交包含所有现有代码
- **Git commit**: "初始化 VideoCatcher 项目"

### 步骤 2：修复后端 Bug（核心功能：API 稳定性）
- 修复 `config.py`: `claude-sonnet-5` → `claude-sonnet-4-20250514`
- 修复 `services/ai_service.py`: 字幕提取改为从 yt-dlp info 的 subtitles/automatic_captions 获取字幕 URL，用 httpx 下载
- 修复 `services/video_service.py`: `temp_dir` 使用 `os.path.abspath()`
- 修复 `models/schemas.py`: 移除未使用的 `HttpUrl`
- 修复 `requirements.txt`: 移除未使用的 `aiofiles`
- **Git commit**: "修复后端关键 Bug"

### 步骤 3：实现前端核心组件（核心功能：视频展示+AI摘要+下载）
- 新建 `VideoInfo.jsx`、`AISummary.jsx`、`DownloadOptions.jsx`、`Footer.jsx`
- 重写 `App.jsx` 集成所有组件
- 替换 `App.css`
- **Git commit**: "实现前端核心组件"

### 步骤 4：端到端验证
- 启动前后端，真实链接测试
- **Git commit**: "端到端测试通过"

## 验证方案
- 后端: `cd backend && uvicorn main:app --reload --port 8000`
- 前端: `cd frontend && npm run dev`
- 浏览器访问 `http://localhost:5173`
