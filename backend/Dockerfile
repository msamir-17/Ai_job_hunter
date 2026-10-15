FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies including curl for container healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Install Python dependencies first for efficient layer caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code and migrations
COPY alembic.ini /app/
COPY alembic /app/alembic
COPY app /app/app
COPY tests /app/tests

# Set ownership to non-root appuser
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Default entrypoint runs FastAPI API server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
