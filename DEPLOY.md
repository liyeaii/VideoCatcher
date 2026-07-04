# VideoCatcher 部署配置指南

## 概览

```
┌──────────────────────────────────────────────────┐
│                    部署架构                        │
├──────────────┬───────────────────────────────────┤
│   前端       │  GitHub Pages（React + Vite）      │
│   后端       │  本地运行或自托管（Python FastAPI）  │
│   数据库     │  无（内存缓存，无需外部 DB）         │
└──────────────┴───────────────────────────────────┘
```

---

## 一、GitHub Pages 前端部署

### 1.1 项目结构

```
VideoCatcher/
├── frontend/              ← GitHub Pages 构建目录
│   ├── src/
│   ├── dist/              ← 构建产物（部署到 Pages）
│   ├── vite.config.js
│   └── package.json
├── backend/               ← Python FastAPI（需单独部署）
├── .github/workflows/
│   └── deploy.yml         ← 自动部署工作流
└── vercel.json
```

### 1.2 自动部署（GitHub Actions）

推送代码到 `main` 分支后，GitHub Actions 自动：
1. 安装依赖 → 构建前端 → 部署到 GitHub Pages

部署成功后访问：`https://liyeaii.github.io/VideoCatcher/`

### 1.3 GitHub Actions Variable（可选）

在 GitHub 仓库 → Settings → Secrets and variables → Actions → Variables：

| Name | Value | 说明 |
|------|-------|------|
| `VITE_API_BASE_URL` | `https://你的后端域名` | 生产环境 API 地址 |

如不设置，前端 API 请求会使用相对路径 `/api`（需要后端在同一域名下）。

---

## 二、后端部署（自托管）

后端（Python FastAPI）需要单独部署，GitHub Pages 只能托管静态文件。

### 2.1 本地运行

```bash
cd backend
pip install -r requirements.txt
python main.py
# 后端运行在 http://localhost:8000
```

### 2.2 环境变量

后端需要以下环境变量（通过 `.env` 文件或系统环境变量设置）：

```bash
AI_API_KEY=your-api-key
AI_PROVIDER=auto
AI_MODEL=
CORS_ORIGINS=*
VIDEO_INFO_CACHE_TTL=1800
SUMMARY_CACHE_TTL=3600
TEMP_DOWNLOAD_DIR=./downloads
BILIBILI_COOKIE=your-cookie
```

---

## 三、部署后检查清单

- [ ] GitHub Pages 前端正常加载首页
- [ ] 后端健康检查：`/api/health` 返回 `{"status":"ok"}`
- [ ] 粘贴 YouTube 链接能正常解析
- [ ] 粘贴 Bilibili 链接能正常解析
- [ ] 粘贴抖音链接能正常解析
- [ ] AI 总结功能正常
- [ ] 下载功能正常

---

## 四、本地开发 vs 生产环境

| | 本地 | 生产 |
|------|------|------|
| 前端端口 | `http://localhost:5173` | GitHub Pages 域名 |
| 后端端口 | `http://localhost:8000` | 自托管域名 |
| API 代理 | `vite.config.js` proxy | 直接请求后端或反向代理 |
| AI Key | `.env` 文件 | 后端环境变量 |

---

## 五、常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| API 请求失败 | 后端未运行或 CORS 未配置 | 确保后端运行并设置 `CORS_ORIGINS=*` |
| 抖音解析返回 null | 视频地域限制 (`core_dep`) | 需要中国大陆 IP |
| 下载接口超时 | 后端内存不足 | 升级后端服务器配置 |
| AI 总结不可用 | `AI_API_KEY` 未设置 | 检查后端环境变量 |
