# The API image (ADR 0023): one FastAPI app, served by uvicorn on Cloud Run's $PORT.
# Built by .github/actions/cloud-run-deploy; versions pinned and looked up when changed.

# ── build: resolve the locked dependencies into /app/.venv ──────────────────
FROM python:3.13.16-slim-trixie AS build
COPY --from=ghcr.io/astral-sh/uv:0.13.4 /uv /bin/uv
# blurhash-python ships no wheel — its C extension compiles here, never in the runtime image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ── runtime: the venv and the code, nothing else ─────────────────────────────
FROM python:3.13.16-slim-trixie
WORKDIR /app
RUN useradd --system --uid 10001 --no-create-home app
COPY --from=build /app/.venv /app/.venv
COPY apps/ apps/
COPY kernel/ kernel/
COPY shared/ shared/
COPY src/ src/
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
# Shell form so $PORT expands; exec so uvicorn gets SIGTERM directly on scale-down.
CMD exec uvicorn apps.api:app --host 0.0.0.0 --port "${PORT:-8080}" --no-access-log
