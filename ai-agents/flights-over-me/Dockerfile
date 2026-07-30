FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY flights_over_me ./flights_over_me
COPY frontend ./frontend

EXPOSE 8000

# Honour FOM_PORT if set; default 8000.
CMD ["sh", "-c", "uvicorn flights_over_me.main:app --host 0.0.0.0 --port ${FOM_PORT:-8000}"]
