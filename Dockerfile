# ============================================================
# GirlBackend - FastAPI 后端 Docker 镜像
# 使用 uv 管理依赖，内置 Chromium 支持 KDocs 抓取
# ============================================================

FROM python:3.11-slim

# ── 系统依赖 ──────────────────────────────────────────────
# chromium: DrissionPage 无头浏览器抓取 KDocs
# fonts-noto-cjk: 中文海报渲染
# libgomp1: pillow / openpyxl 等运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    fonts-noto-cjk \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# DrissionPage 需要的 Chrome 路径
ENV CHROMIUM_BIN=/usr/bin/chromium

# ── uv 包管理器 ────────────────────────────────────────────
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# ── 工作目录 ──────────────────────────────────────────────
WORKDIR /app

# ── 依赖层（利用 Docker 缓存） ──────────────────────────
# 先只复制依赖文件，这样源码改动不会触发重新安装
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ── 源码层 ────────────────────────────────────────────────
COPY . .

# 此时再安装项目本身（可编辑安装，或者 sync 补齐）
RUN uv sync --frozen --no-dev

# ── 静态文件目录 ──────────────────────────────────────────
RUN mkdir -p static/avatars static/qrcode static/banner

# ── 运行时 ────────────────────────────────────────────────
EXPOSE 8000

# 启动：uv run 确保 .venv 二进制在 PATH 中
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]