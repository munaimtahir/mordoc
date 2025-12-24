# Multi-stage build for mordoc (Django + React)
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./

# Build frontend with API base URL and base path
# VITE_API_BASE: API endpoint (defaults to relative /api, works with Keystone/Traefik)
# VITE_BASE: Base path for deployment
#   - For root deployment: / (default)
#   - For Keystone subpath: /{APP_SLUG} (e.g., /mordoc)
#   - Keystone should pass --build-arg VITE_BASE=/{APP_SLUG}
ARG VITE_API_BASE=/api
ARG VITE_BASE=/
ENV VITE_API_BASE=${VITE_API_BASE}
ENV VITE_BASE=${VITE_BASE}
RUN npm run build

# Main application stage
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend code
COPY backend/ /app/

# Copy frontend build to frontend_build/ directory (relative to /app)
# Vite outputs to /frontend/dist by default
COPY --from=frontend-builder /frontend/dist /app/frontend_build/

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["server"]

