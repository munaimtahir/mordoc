# Keystone Deployment Guide

This guide explains how to deploy mordoc using [Keystone](https://github.com/your-username/keystone), a self-hosted deployment control panel with Traefik reverse proxy.

## Prerequisites

1. **Keystone installed and running** on your VPS with Traefik configured
2. **External services** (mordoc requires these):
   - PostgreSQL database (accessible via network)
   - Redis server (for Celery background tasks)

## Deployment Steps

### 1. Prepare External Services

Mordoc requires PostgreSQL and Redis. You have two options:

#### Option A: Use External Services
- Ensure PostgreSQL is accessible (e.g., on the same VPS or a separate database server)
- Ensure Redis is accessible (e.g., on the same VPS or a separate Redis server)

#### Option B: Deploy Services Separately via Keystone
- Deploy PostgreSQL and Redis as separate apps in Keystone first
- Use their internal network addresses when configuring mordoc

### 2. Add Repository in Keystone

1. Log into Keystone UI (via Traefik at `http://<VM_IP>` or direct port `http://<VM_IP>:8080`)
2. Go to **Repositories** section
3. Add a new repository:
   - **Name**: `mordoc`
   - **Git URL**: `https://github.com/your-username/mordoc.git` (or your repo URL)
   - **Branch**: `main` (or your default branch)
   - **GitHub PAT**: (Optional, if repository is private)

### 3. Create App in Keystone

1. Go to **Apps** section
2. Click **Add App**:
   - **App name**: `mordoc`
   - **Repo**: Select the `mordoc` repository you just added
   - **Access mode**: 
     - **PORT** (default): Access via `http://<VM_IP>:<assigned_port>` (9000-9999)
     - **HOST**: Access via Traefik at `http://<VM_IP>/mordoc` or subdomain (requires Traefik labels)
   - **Container port**: `8000` (default)
   - **Health check path**: `/api/health/` (optional but recommended)
   - **Env vars**: Add the following environment variables (as JSON):

#### For PORT Mode (Direct Port Access):
```json
{
  "DJANGO_SECRET_KEY": "your-secret-key-here-change-me",
  "DJANGO_DEBUG": "0",
  "DJANGO_ALLOWED_HOSTS": "*",
  "DATABASE_URL": "postgres://user:password@host:5432/dbname",
  "REDIS_URL": "redis://host:6379/0",
  "MEDIA_ROOT": "/app/media",
  "CORS_ALLOWED_ORIGINS": "http://YOUR_VM_IP:PORT"
}
```

#### For HOST Mode (Traefik Routing):
```json
{
  "DJANGO_SECRET_KEY": "your-secret-key-here-change-me",
  "DJANGO_DEBUG": "0",
  "DJANGO_ALLOWED_HOSTS": "*",
  "DATABASE_URL": "postgres://user:password@host:5432/dbname",
  "REDIS_URL": "redis://host:6379/0",
  "MEDIA_ROOT": "/app/media",
  "DJANGO_FORCE_SCRIPT_NAME": "/mordoc",
  "CORS_ALLOWED_ORIGINS": "http://YOUR_VM_IP"
}
```

**Note**: When using HOST mode with Traefik:
- Set `DJANGO_FORCE_SCRIPT_NAME` to the subpath (e.g., `/mordoc`) if using path-based routing
- Set `CORS_ALLOWED_ORIGINS` without port numbers (Traefik handles routing on port 80)
- The app will be accessible at `http://<VM_IP>/mordoc` (or subdomain if configured)

**Important Environment Variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key (change this!) | `your-secret-key-here` |
| `DJANGO_DEBUG` | Debug mode (use `0` for production) | `0` |
| `DJANGO_ALLOWED_HOSTS` | Allowed hosts (comma-separated) | `*` or specific IPs |
| `DATABASE_URL` | PostgreSQL connection string | `postgres://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://host:6379/0` |
| `MEDIA_ROOT` | Media files storage path | `/app/media` |
| `CORS_ALLOWED_ORIGINS` | CORS allowed origins | `http://YOUR_VM_IP:9000` |

### 4. Deploy

1. Click **Deploy** button next to your mordoc app
2. Wait for deployment to complete (you can view logs in real-time)
3. Once deployed, your app will be accessible at:
   - **PORT mode**: `http://<VM_IP>:<assigned_port>` (port range 9000-9999)
   - **HOST mode**: `http://<VM_IP>/mordoc` (via Traefik, if subpath routing is configured)

**Note**: For HOST mode, ensure Keystone's runner adds Traefik labels to the container. The container must be on the same Docker network as Traefik (`platform` network).

### 5. Seed Templates (Optional)

After first deployment, you may want to seed default templates. You can do this by:

1. Accessing the container shell (if Keystone supports it)
2. Or running a management command during deployment

To add this to the entrypoint, you can modify `docker-entrypoint.sh` or run manually:

```bash
docker exec -it <container_name> python manage.py seed_templates
```

## Architecture

The mordoc Dockerfile creates a single container that:

1. **Builds the frontend** (React + Vite) during Docker build
2. **Serves both frontend and backend** via Django:
   - Frontend static files served via WhiteNoise
   - Backend API at `/api/*`
   - Admin panel at `/admin/`
   - Health check at `/api/health/`

### Traefik Integration

When deployed in **HOST mode** with Traefik:

- **Path-based routing**: App accessible at `http://<VM_IP>/mordoc`
- **Subdomain routing**: App accessible at `http://mordoc.<domain>` (if configured)
- **Static files**: Automatically handled via WhiteNoise with correct base paths
- **CORS**: Configured to work without port numbers
- **Reverse proxy headers**: Django trusts `X-Forwarded-*` headers from Traefik

The app is configured to work behind a reverse proxy and supports:
- Subpath deployment (`DJANGO_FORCE_SCRIPT_NAME`)
- Base path for frontend assets (`VITE_BASE`)
- Proper static/media URL handling

## Celery Worker

**Note**: The current Dockerfile runs only the Django server. Celery worker runs in a separate container in the original `docker-compose.yml`.

For Keystone deployment, you have two options:

1. **Run Celery worker separately** (recommended for production):
   - Deploy a second app in Keystone with the same codebase
   - Set the `CMD` to run the worker: `["worker"]`
   - Share the same `DATABASE_URL` and `REDIS_URL`

2. **Run both in one container** (for development/testing):
   - Modify the Dockerfile to use `CMD ["both"]`
   - This runs both Django server and Celery worker in the same container

To run both in one container, update the Dockerfile CMD:
```dockerfile
CMD ["both"]
```

## Health Check

The health check endpoint is available at `/api/health/` and returns:
```json
{"ok": true}
```

Keystone will use this to verify the app is running correctly.

## Troubleshooting

### App fails to start

1. **Check logs**: View deployment logs in Keystone UI
2. **Database connection**: Verify `DATABASE_URL` is correct and database is accessible
3. **Redis connection**: Verify `REDIS_URL` is correct and Redis is accessible
4. **Port conflicts**: Ensure the assigned port isn't already in use

### Frontend not loading

1. **Static files**: Check that `collectstatic` ran successfully (check logs)
2. **API base URL**: The frontend uses `/api` by default (relative path, works with Traefik)
3. **CORS**: Ensure `CORS_ALLOWED_ORIGINS` includes your app's URL (without port for Traefik)
4. **Subpath routing**: If using HOST mode with subpath, ensure `DJANGO_FORCE_SCRIPT_NAME` matches the Traefik route path
5. **Base path**: Frontend is built with `VITE_BASE` support - ensure it matches your deployment path

### Celery tasks not running

1. **Worker not running**: Deploy a separate worker container (see Celery Worker section)
2. **Redis connection**: Verify `REDIS_URL` is accessible from the worker container

## Environment Variables Reference

All environment variables can be set in Keystone's app configuration. Here's a complete list:

### Required
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string (for Celery)

### Optional (with defaults)
- `DJANGO_SECRET_KEY` - Defaults to `dev-only-secret` (change in production!)
- `DJANGO_DEBUG` - Defaults to `1` (set to `0` for production)
- `DJANGO_ALLOWED_HOSTS` - Defaults to `localhost,127.0.0.1` (use `*` or specific IPs/domains)
- `DJANGO_FORCE_SCRIPT_NAME` - Subpath for deployment (e.g., `/mordoc` for Traefik path routing)
- `MEDIA_ROOT` - Defaults to `/app/media`
- `CORS_ALLOWED_ORIGINS` - Defaults to `http://localhost:5173` (use without port for Traefik, e.g., `http://localhost`)

### Build-time Variables (for Docker build)
- `VITE_API_BASE` - API base URL (defaults to `/api` - relative path works with Traefik)
- `VITE_BASE` - Base path for frontend (defaults to `/`, set to `/mordoc` for subpath deployment)

## Production Considerations

1. **Secret Key**: Always set a strong `DJANGO_SECRET_KEY` in production
2. **Debug Mode**: Set `DJANGO_DEBUG=0` in production
3. **Allowed Hosts**: Use specific IPs or domain names, not `*`
4. **Database**: Use a managed PostgreSQL service for production
5. **Redis**: Use a managed Redis service for production
6. **Media Files**: Consider using cloud storage (S3, etc.) for media files
7. **HTTPS**: Configure Traefik with Let's Encrypt for HTTPS (set `SECURE_PROXY_SSL_HEADER` in settings)
8. **Worker**: Run Celery worker in a separate container for better reliability
9. **Traefik Routing**: Prefer HOST mode with Traefik for cleaner URLs and easier HTTPS setup
10. **Subpath vs Subdomain**: 
    - Subpath (`/mordoc`): Simpler, works with single domain
    - Subdomain (`mordoc.example.com`): Cleaner URLs, requires DNS configuration

## Updating the Application

1. Push changes to your Git repository
2. In Keystone UI, click **Update** next to the mordoc app
3. Keystone will pull latest changes, rebuild, and redeploy automatically

## Rollback

If a deployment fails, you can use the **Rollback** button in Keystone to revert to the previous working version.

