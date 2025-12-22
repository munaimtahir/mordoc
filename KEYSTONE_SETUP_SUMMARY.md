# Keystone Deployment Setup - Summary

This document summarizes the changes made to prepare mordoc for deployment via Keystone.

## Changes Made

### 1. Root Dockerfile (`Dockerfile`)
- **Created**: Multi-stage Docker build
  - Stage 1: Builds React frontend using Node.js
  - Stage 2: Sets up Python/Django backend
  - Copies frontend build to `/app/frontend_build/`
  - Configures `VITE_API_BASE=/api` during frontend build (relative path)
  - Exposes port 8000

### 2. Docker Entrypoint (`docker-entrypoint.sh`)
- **Created**: Bash script that:
  - Waits for database connection (if DATABASE_URL is set)
  - Runs Django migrations
  - Collects static files (includes frontend build)
  - Seeds templates (if needed)
  - Starts Django server (default) or Celery worker, or both

### 3. Django Settings (`backend/config/settings.py`)
- **Updated**: 
  - Added WhiteNoise middleware for static file serving
  - Configured `STATICFILES_DIRS` to include frontend build directory
  - Set `STATIC_ROOT` for collected static files
  - Added `WHITENOISE_INDEX_FILE = True` for SPA support

### 4. Django URLs (`backend/config/urls.py`)
- **Updated**: 
  - Added catch-all route to serve frontend `index.html` for SPA routing
  - Excludes API, admin, static, and media paths

### 5. Requirements (`backend/requirements.txt`)
- **Updated**: Added `whitenoise>=6.7,<7.0` for static file serving

### 6. Documentation
- **Created**: `docs/KEYSTONE_DEPLOYMENT.md` with comprehensive deployment guide
- **Updated**: `README.md` with deployment section

### 7. Docker Ignore (`.dockerignore`)
- **Created**: Excludes unnecessary files from Docker build context

## Architecture

The application now runs as a single container that:

1. **Builds frontend** during Docker build (React + Vite)
2. **Serves frontend** via Django/WhiteNoise as static files
3. **Serves backend API** at `/api/*`
4. **Handles SPA routing** by serving `index.html` for all non-API routes

## Required Environment Variables

When deploying via Keystone, configure these environment variables:

### Required
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string (for Celery)

### Recommended
- `DJANGO_SECRET_KEY` - Django secret key (change from default!)
- `DJANGO_DEBUG=0` - Disable debug mode in production
- `DJANGO_ALLOWED_HOSTS` - Allowed hosts (comma-separated)
- `MEDIA_ROOT=/app/media` - Media files storage
- `CORS_ALLOWED_ORIGINS` - CORS allowed origins

## Deployment Flow

1. Keystone clones the repository
2. Docker builds the image (frontend + backend)
3. Keystone runs the container with:
   - Port mapping (9000-9999 range)
   - Environment variables (configured in Keystone UI)
4. Container starts:
   - Runs migrations
   - Collects static files
   - Seeds templates
   - Starts Django server on port 8000
5. App accessible at `http://<VM_IP>:<assigned_port>`

## Health Check

Health check endpoint: `/api/health/`

Returns: `{"ok": true}`

Configure this in Keystone app settings for automatic health verification.

## Celery Worker

**Current setup**: Only Django server runs by default (`CMD ["server"]`)

**Options for Celery**:

1. **Separate container** (recommended):
   - Deploy same codebase as second app
   - Set CMD to `["worker"]`
   - Share DATABASE_URL and REDIS_URL

2. **Same container**:
   - Change Dockerfile CMD to `["both"]`
   - Runs both Django and Celery in one container

## Testing Locally

You can test the Docker build locally:

```bash
# Build the image
docker build -t mordoc:test .

# Run with environment variables
docker run -p 8000:8000 \
  -e DATABASE_URL="postgres://user:pass@host:5432/db" \
  -e REDIS_URL="redis://host:6379/0" \
  -e DJANGO_SECRET_KEY="test-secret" \
  mordoc:test
```

## Files Changed/Created

### New Files
- `Dockerfile` (root)
- `docker-entrypoint.sh`
- `.dockerignore`
- `docs/KEYSTONE_DEPLOYMENT.md`
- `KEYSTONE_SETUP_SUMMARY.md` (this file)

### Modified Files
- `backend/config/settings.py`
- `backend/config/urls.py`
- `backend/requirements.txt`
- `README.md`

## Next Steps

1. Test the Docker build locally
2. Push changes to your repository
3. Add repository in Keystone
4. Configure app with environment variables
5. Deploy!

For detailed instructions, see [docs/KEYSTONE_DEPLOYMENT.md](docs/KEYSTONE_DEPLOYMENT.md).

