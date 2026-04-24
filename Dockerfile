FROM python:3.13-slim AS builder

WORKDIR /app

COPY requirements.setup.txt .
RUN python -m pip install --no-cache-dir -r requirements.setup.txt

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_PREFERENCE=only-system
ENV UV_FROZEN=true

COPY pyproject.toml uv.lock ./

# BuildKitのキャッシュマウント（--mount=type=cache）を削除し、通常のRUNに変更
RUN uv sync --frozen --no-install-project --no-dev --no-editable

COPY . /app

# こちらも同様にキャッシュマウントを削除
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.13-slim

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app app
RUN mkdir -p /app && chown -R app:app /app
RUN mkdir -p /app/secrets && chown -R app:app /app/secrets

COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH"

ENV UV_CACHE_DIR=/app/.uv_cache
RUN mkdir -p /app/.uv_cache && chown -R app:app /app/.uv_cache

# --- SSE サーバーの設定 ---
ENV MCP_TRANSPORT=sse
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000
EXPOSE 8000
# -------------------------

USER app

ENTRYPOINT ["uv", "run", "vais-mcp"]
CMD