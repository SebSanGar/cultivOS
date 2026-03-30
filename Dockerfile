# ---------- build stage ----------
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- runtime stage ----------
FROM python:3.12-slim

RUN groupadd -r cultivos && useradd -r -g cultivos cultivos

WORKDIR /app

COPY --from=builder /install /usr/local
COPY src/ src/
COPY frontend/ frontend/

ENV PYTHONPATH=/app/src
ENV PORT=8000

USER cultivos

CMD python -m uvicorn cultivos.app:create_app --factory --host 0.0.0.0 --port $PORT
