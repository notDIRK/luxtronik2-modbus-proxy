# Multi-stage build for luxtronik2-modbus-proxy
# Base image: python:3.12-slim (manylinux wheels install instantly, no compilation)

# --- Builder stage ---
FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir --prefix=/install .

# --- Runtime stage ---
FROM python:3.12-slim

# Install tini for proper signal handling (SIGTERM forwarding, zombie reaping)
RUN apt-get update && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --uid 1000 proxy

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Default config path (user mounts their config.yaml here)
ENV LUXTRONIK_CONFIG_PATH=/app/config.yaml

USER proxy

EXPOSE 502

# tini as PID 1 for signal handling
ENTRYPOINT ["tini", "--"]
CMD ["luxtronik2-modbus-proxy", "--config", "/app/config.yaml"]
