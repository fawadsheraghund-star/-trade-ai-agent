FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies (ffmpeg for audio, build tools for some Python packages)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ffmpeg \
       build-essential \
       git \
       libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements if present and install, otherwise install a sensible default set
COPY requirements.txt ./

RUN pip install --upgrade pip setuptools wheel
RUN if [ -f requirements.txt ]; then \
      pip install --no-cache-dir -r requirements.txt; \
    else \
      pip install --no-cache-dir uvicorn[standard] fastapi python-telegram-bot==20.3 ccxt pandas pandas-ta httpx transformers openai aiofiles; \
    fi

# Copy application code
COPY . /app

# Expose port used by FastAPI
EXPOSE 8000

# Default envs (can be overridden at deploy/runtime)
ENV PORT=8000

# Run the FastAPI app. Telegram bot will be started by main in background thread.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
