FROM python:3.13-slim

COPY --from=astral/uv:latest /uv /bin/uv

ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH="/app/.venv/bin:$PATH" HF_HOME=/models
WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-install-project

COPY . .
RUN useradd --system --uid 10001 app && mkdir staticfiles /models && chown app staticfiles /models
USER app

EXPOSE 8000
