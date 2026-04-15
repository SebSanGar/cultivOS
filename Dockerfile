# ---------- build stage ----------
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- runtime stage ----------
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY src/ src/
COPY frontend/ frontend/
COPY scripts/ scripts/

ENV PYTHONPATH=/app/src:/app
ENV PORT=8000

CMD python -m uvicorn cultivos.app:create_app --factory --host 0.0.0.0 --port $PORT
