# ==========================================================================
# DevOps Health Dashboard — production image
# Multi-stage build, non-root user, gunicorn entrypoint, container healthcheck
# ==========================================================================

FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files & enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies (curl needed for the container healthcheck)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create a non-root user and hand over ownership of the app + writable dirs
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser \
    && mkdir -p /app/logs \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Gunicorn production entrypoint — 4 workers, 2 threads each, 60s timeout
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", \
     "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
