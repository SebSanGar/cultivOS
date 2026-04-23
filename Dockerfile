# ---------- frontend build stage ----------
FROM node:20-slim AS frontend-builder

WORKDIR /build
COPY frontend-v2/package*.json ./
RUN npm ci
COPY frontend-v2 .
RUN npm run build

# ---------- python build stage ----------
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- runtime stage ----------
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY src/ src/
COPY --from=frontend-builder /build/out frontend/
COPY scripts/ scripts/

ENV PYTHONPATH=/app/src:/app
ENV PORT=8000

CMD python -m uvicorn cultivos.app:create_app --factory --host 0.0.0.0 --port $PORT
