# ============================================
# VideoCatcher 开发容器
# 隔离 Python 3.12 + Node.js 22 + FFmpeg 环境
# ============================================
FROM python:3.12-slim

# ============================================
# 系统依赖安装
# ============================================
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    git \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# 安装 Node.js 22 LTS（前端 Vite 8 需要 Node 20+）
# ============================================
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && node --version && npm --version

# ============================================
# 创建非 root 用户（安全最佳实践）
# ============================================
RUN useradd -m -s /bin/bash developer \
    && mkdir -p /workspace \
    && chown developer:developer /workspace

# ============================================
# 预装 Python 依赖（加速首次启动）
# ============================================
COPY --chown=developer:developer backend/requirements.txt /tmp/requirements.txt
RUN pip install --user -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# ============================================
# 预装 Node.js 依赖（加速首次启动）
# ============================================
COPY --chown=developer:developer frontend/package.json frontend/package-lock.json /tmp/frontend/
RUN cd /tmp/frontend && npm install \
    && rm -rf /tmp/frontend

# ============================================
# 切换到非 root 用户
# ============================================
USER developer
WORKDIR /workspace

# 暴露端口
EXPOSE 8000 5173

CMD ["bash"]
