# Traefik Integration Update - Summary

This document summarizes the changes made to prepare mordoc for deployment via Keystone with Traefik reverse proxy support.

## Changes Made

### 1. Django Settings (`backend/config/settings.py`)

#### Reverse Proxy Support
- **Added**: `USE_X_FORWARDED_HOST = True` - Trusts X-Forwarded-Host header from Traefik
- **Added**: `SECURE_PROXY_SSL_HEADER` placeholder - Can be set for HTTPS support

#### Subpath Deployment Support
- **Added**: `FORCE_SCRIPT_NAME` support - Allows deployment at subpaths (e.g., `/mordoc`)
- **Updated**: `STATIC_URL` and `MEDIA_URL` - Automatically prepend subpath if `FORCE_SCRIPT_NAME` is set
- **Example**: If `DJANGO_FORCE_SCRIPT_NAME=/mordoc`, static files are served at `/mordoc/static/`

#### CORS Configuration
- **Updated**: CORS origins parsing - Handles comma-separated values properly
- **Updated**: Documentation - Notes that origins should not include port numbers when using Traefik
- **Example**: Use `http://localhost` instead of `http://localhost:5173` when behind Traefik

### 2. Frontend Configuration (`frontend/vite.config.ts`)

- **Added**: `base` configuration - Supports subpath deployment via `VITE_BASE` environment variable
- **Default**: `/` (root path)
- **Example**: Set `VITE_BASE=/mordoc` for subpath deployment

### 3. Dockerfile

- **Updated**: Build arguments - Added `VITE_BASE` build argument
- **Default**: `VITE_BASE=/` (root path)
- **Usage**: Can be overridden during build for subpath deployment

### 4. Documentation (`docs/KEYSTONE_DEPLOYMENT.md`)

#### Added Sections:
- **HOST Mode Deployment**: Instructions for Traefik-based routing
- **PORT vs HOST Mode**: Comparison and use cases
- **Environment Variables**: Updated with Traefik-specific settings
- **Troubleshooting**: Added Traefik-specific troubleshooting steps

#### Key Updates:
- Environment variable examples for both PORT and HOST modes
- CORS configuration notes for Traefik
- Subpath vs subdomain routing guidance
- HTTPS configuration notes

## Deployment Modes

### PORT Mode (Legacy)
- **Access**: `http://<VM_IP>:<port>` (9000-9999)
- **Use Case**: Direct port access, no reverse proxy
- **CORS**: Include port in origins (e.g., `http://localhost:9000`)

### HOST Mode (Traefik)
- **Access**: `http://<VM_IP>/mordoc` (subpath) or `http://mordoc.<domain>` (subdomain)
- **Use Case**: Clean URLs, single entry point, easier HTTPS setup
- **CORS**: No port in origins (e.g., `http://localhost`)
- **Requirements**: 
  - Container on `platform` Docker network
  - Traefik labels configured (by Keystone runner)
  - `DJANGO_FORCE_SCRIPT_NAME` set for subpath routing

## Environment Variables for Traefik

### Required for HOST Mode:
```json
{
  "DJANGO_FORCE_SCRIPT_NAME": "/mordoc",
  "CORS_ALLOWED_ORIGINS": "http://YOUR_VM_IP"
}
```

### Optional:
- `SECURE_PROXY_SSL_HEADER`: Set to `('HTTP_X_FORWARDED_PROTO', 'https')` for HTTPS
- `VITE_BASE`: Build-time variable for frontend base path (defaults to `/`)

## Files Changed

### Modified Files:
- `backend/config/settings.py` - Reverse proxy and subpath support
- `frontend/vite.config.ts` - Base path configuration
- `Dockerfile` - Build arguments for subpath
- `docs/KEYSTONE_DEPLOYMENT.md` - Comprehensive Traefik documentation

## Testing

To test Traefik integration locally:

1. **Build with subpath**:
   ```bash
   docker build --build-arg VITE_BASE=/mordoc -t mordoc:traefik .
   ```

2. **Run with subpath environment**:
   ```bash
   docker run -p 8000:8000 \
     -e DJANGO_FORCE_SCRIPT_NAME=/mordoc \
     -e CORS_ALLOWED_ORIGINS=http://localhost \
     -e DATABASE_URL="..." \
     -e REDIS_URL="..." \
     mordoc:traefik
   ```

3. **Access via reverse proxy** (if Traefik is running):
   - App should be accessible at `http://localhost/mordoc`
   - Static files at `http://localhost/mordoc/static/`
   - API at `http://localhost/mordoc/api/`

## Next Steps

1. **Keystone Runner Update**: Ensure Keystone's runner adds Traefik labels when deploying in HOST mode:
   ```yaml
   traefik.enable=true
   traefik.http.routers.mordoc.rule=PathPrefix(`/mordoc`)
   traefik.http.routers.mordoc.entrypoints=web
   traefik.http.services.mordoc.loadbalancer.server.port=8000
   ```

2. **Network Configuration**: Ensure deployed containers are on the `platform` network

3. **HTTPS Setup**: Configure Traefik with Let's Encrypt and update `SECURE_PROXY_SSL_HEADER` in settings

## Compatibility

- ✅ **Backward Compatible**: PORT mode still works as before
- ✅ **Forward Compatible**: Ready for Traefik HOST mode deployment
- ✅ **Flexible**: Supports both subpath and subdomain routing
- ✅ **Production Ready**: Includes HTTPS support configuration

