# FastAPI API for Railway (and any Docker host). Next.js stays on Vercel (apps/web).
FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY skills ./skills

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

ENV PYTHONPATH=/app

# Railway sets PORT at runtime
CMD ["sh", "-c", "exec uvicorn src.web.app:app --host 0.0.0.0 --port ${PORT:-8013}"]
