# VideoCatcher 部署配置指南

## 概览

```
┌──────────────────────────────────────────────────┐
│                    部署架构                        │
├──────────────┬───────────────────────────────────┤
│   前端       │  Vercel（React + Vite）            │
│   后端       │  Railway（Python FastAPI）          │
│   数据库     │  无（内存缓存，无需外部 DB）         │
└──────────────┴───────────────────────────────────┘
```

---

## 一、Railway 后端部署

### 1.1 项目结构

```
VideoCatcher/
├── backend/           ← Railway Root Directory
│   ├── Dockerfile     ← Railway 自动检测
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── services/
│   └── models/
├── frontend/           ← Vercel Root Directory
└── vercel.json
```

### 1.2 Railway Settings 面板配置

在 Railway Dashboard → 项目 → **Settings**：

| 设置项 | 值 |
|--------|-----|
| **Root Directory** | `backend` |
| **Build Method** | `Dockerfile`（自动检测） |
| **Watch Paths** | `backend/**` |

### 1.3 Railway Variables（环境变量）

在 Railway Dashboard → 项目 → **Variables** → **New Variable**：

> ⚠️ 删除 `.env` 文件中 `AI_API_KEY` 的值，用 Railway Variables 替代。`.env` 仅用于本地开发。

```bash
# ============================================
# 全量 Variables — 逐一添加到 Railway
# ============================================

# ── AI 服务 ──
AI_API_KEY=sk-7fa5bb4871044fc6989766ae063be68c
AI_PROVIDER=auto

# ── AI 模型（可选，留空使用默认）──
# DeepSeek 默认: deepseek-chat
# Claude 默认:   claude-sonnet-4-20250514
AI_MODEL=

# ── 跨域请求 ──
CORS_ORIGINS=*

# ── 缓存时间（秒）──
VIDEO_INFO_CACHE_TTL=1800
SUMMARY_CACHE_TTL=3600

# ── 临时下载目录 ──
TEMP_DOWNLOAD_DIR=./downloads

# ── Bilibili Cookie（解锁高清下载）──
BILIBILI_COOKIE=SESSDATA=572583bc%2C1798515750%2Cbd1a6%2A72CjAykKJ1NyTgIx5hZrWXl5inSYPae22-f_ZqEMKllyG6J26NQqpjzaWZCGsjDL_cErgSVkM2czRPYUFlM3duUmlrN0Q2NDdsa05wWnJtSUdEVU1LdVIxMWZSQW9Ydl81SmJpTUJUZmtHbDlxSzJjbFBrT2l4bWpsa2M1UmZsUGdVN2hveW43cnVRIIEC
```

### 1.4 逐项粘贴对照表

打开 Railway → 项目 → **Variables** 面板，逐个添加：

| Name | Value |
|------|-------|
| `AI_API_KEY` | `sk-7fa5bb4871044fc6989766ae063be68c` |
| `AI_PROVIDER` | `auto` |
| `AI_MODEL` | （留空） |
| `CORS_ORIGINS` | `*` |
| `VIDEO_INFO_CACHE_TTL` | `1800` |
| `SUMMARY_CACHE_TTL` | `3600` |
| `TEMP_DOWNLOAD_DIR` | `./downloads` |
| `BILIBILI_COOKIE` | `SESSDATA=572583bc%2C1798515750%2Cbd1a6%2A72CjAykKJ1NyTgIx5hZrWXl5inSYPae22-f_ZqEMKllyG6J26NQqpjzaWZCGsjDL_cErgSVkM2czRPYUFlM3duUmlrN0Q2NDdsa05wWnJtSUdEVU1LdVIxMWZSQW9Ydl81SmJpTUJUZmtHbDlxSzJjbFBrT2l4bWpsa2M1UmZsUGdVN2hveW43cnVRIIEC` |

### 1.5 验证部署

部署完成后，Railway 会生成一个域名，形如：
```
https://videocatcher-production-xxxx.up.railway.app
```

验证后端健康状态：
```bash
curl https://your-app.up.railway.app/api/health
# 返回: {"status":"ok"}
```

---

## 二、Vercel 前端部署

### 2.1 vercel.json（项目根目录）

```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://你的Railway域名.up.railway.app/api/$1"
    }
  ]
}
```

### 2.2 Vercel 配置

在 Vercel 导入项目时：

| 字段 | 值 |
|------|-----|
| **Framework Preset** | `Vite` |
| **Root Directory** | `frontend` |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |

### 2.3 Vercel Environment Variables

| Name | Value |
|------|-------|
| _无需额外变量_ | 前端通过 `/api` 代理到 Railway |

---

## 三、部署后检查清单

- [ ] Railway 后端健康检查：`/api/health` 返回 `{"status":"ok"}`
- [ ] Vercel 前端正常加载首页
- [ ] 粘贴 YouTube 链接能正常解析
- [ ] 粘贴 Bilibili 链接能正常解析
- [ ] 粘贴抖音链接能正常解析
- [ ] AI 总结功能正常
- [ ] 下载功能正常
- [ ] `vercel.json` 中的 `destination` 已更新为真实的 Railway 域名

---

## 四、本地开发 vs 生产环境

| | 本地 | 生产 |
|------|------|------|
| 前端端口 | `http://localhost:5173` | Vercel 域名 |
| 后端端口 | `http://localhost:8000` | Railway 域名 |
| API 代理 | `vite.config.js` proxy | `vercel.json` rewrites |
| Cookie | Edge 浏览器自动获取 | 无浏览器（Playwright headless） |
| AI Key | `.env` 文件 | Railway Variables 面板 |

---

## 五、常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| Railway 构建失败 | Chromium 下载超时 | 在 Railway 增加构建超时时间（设置 > 600s） |
| 抖音解析返回 null | 视频地域限制 (`core_dep`) | 需要中国大陆 IP |
| 下载接口超时 | 免费版内存不足 | 升级到 Railway Pro（512MB+ RAM） |
| CORS 错误 | `CORS_ORIGINS` 未包含前端域名 | 改为 `*` 或添加具体域名 |
| AI 总结不可用 | `AI_API_KEY` 未设置 | 检查 Railway Variables 是否正确填写 |
