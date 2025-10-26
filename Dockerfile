# Dockerfile
FROM python:3.12-slim

# Avoid interactive tzdata prompts & speed up pip
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for pillow (and some scientific libs); very small footprint on slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better layer cache)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy app source
COPY . .

# Cloud Run provides $PORT; default to 8080 for local runs
ENV PORT=8080

# Start the server
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
