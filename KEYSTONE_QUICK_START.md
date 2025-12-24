# Quick Deployment Guide for Keystone

This is a quick reference for deploying Mordoc via Keystone. For detailed information, see [KEYSTONE_COMPATIBILITY_REPORT.md](KEYSTONE_COMPATIBILITY_REPORT.md).

## Prerequisites

- Keystone control panel installed
- PostgreSQL database available
- Redis instance available
- VPS with Docker support

## Step 1: Add Repository

1. In Keystone, go to **Repositories**
2. Click **Add Repository**
3. Enter: `https://github.com/munaimtahir/mordoc`
4. Click **Save**

## Step 2: Create App

1. Go to **Apps**
2. Click **Create App**
3. Fill in:
   - **Name**: Mordoc (or your preferred name)
   - **Slug**: `mordoc` (or your preferred slug - this will be your URL path)
   - **Repository**: Select the repository you just added
   - **Branch**: `main` (or your target branch)

## Step 3: Configure Build Arguments

In the **Build Configuration** section:

```yaml
VITE_BASE: /mordoc  # Must match your app slug
VITE_API_BASE: /api
```

**Important**: Replace `/mordoc` with `/{YOUR_APP_SLUG}`

## Step 4: Configure Environment Variables

In the **Environment Variables** section:

### Required Variables

```bash
# Database
DATABASE_URL=postgres://user:password@hostname:5432/database_name

# Redis (for Celery background tasks)
REDIS_URL=redis://hostname:6379/0

# Django Security
DJANGO_SECRET_KEY=<generate-random-50-character-string>
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=YOUR_VPS_IP,your-domain.com

# Keystone Subpath Configuration
DJANGO_FORCE_SCRIPT_NAME=/mordoc  # Must match your app slug

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://YOUR_VPS_IP
```

### Optional Variables

```bash
# Media Storage
MEDIA_ROOT=/app/media

# If using HTTPS (recommended for production)
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')
```

### How to Generate SECRET_KEY

```python
# In Python:
import secrets
print(secrets.token_urlsafe(50))
```

Or use: https://djecrety.ir/

## Step 5: Configure Container

- **Internal Port**: `8000`
- **Health Check Endpoint**: `/api/health/`
- **Command**: `server` (default, already set in Dockerfile)

## Step 6: Deploy

1. Click **Deploy**
2. Wait for build to complete (3-5 minutes)
3. Wait for container to start
4. Check health status

## Step 7: Verify Deployment

### Check Health Endpoint

```bash
curl http://YOUR_VPS_IP/mordoc/api/health/
```

Expected response:
```json
{"ok": true}
```

### Access Application

Open in browser:
```
http://YOUR_VPS_IP/mordoc/
```

You should see the Mordoc application UI.

### Check Static Files

Open browser DevTools → Network tab and verify:
- No 404 errors for static files
- Assets load from `/mordoc/static/...`
- API calls go to `/mordoc/api/...`

## Step 8: Create Admin User (First Time Only)

```bash
# SSH into your VPS or use Keystone's container terminal
docker exec -it <container-name> python manage.py createsuperuser
```

Then access admin at: `http://YOUR_VPS_IP/mordoc/admin/`

## Troubleshooting

### Issue: Health check fails

**Solution**: Check logs in Keystone dashboard. Common causes:
- Database connection failed (verify DATABASE_URL)
- Redis connection failed (verify REDIS_URL)
- Migrations not running (check entrypoint script logs)

### Issue: 404 on static files

**Solution**:
1. Verify `VITE_BASE` build arg matches app slug
2. Verify `DJANGO_FORCE_SCRIPT_NAME` env var matches app slug
3. Rebuild the application

### Issue: CORS errors in browser

**Solution**:
1. Verify `CORS_ALLOWED_ORIGINS` includes your VPS IP (no port, no path)
2. Example: `CORS_ALLOWED_ORIGINS=http://192.168.1.100` ✅
3. Not: `CORS_ALLOWED_ORIGINS=http://192.168.1.100:8000/mordoc` ❌

### Issue: API calls go to wrong URL

**Solution**: Verify `VITE_API_BASE=/api` (relative path) in build args

### Issue: Page refresh gives 404

**Solution**: This should work automatically. If not:
1. Verify Django catch-all route exists in `config/urls.py`
2. Verify `WHITENOISE_INDEX_FILE=True` in settings
3. Check application logs

## Environment Variable Reference Card

Copy and customize this template:

```bash
# === REQUIRED ===
DATABASE_URL=postgres://mordoc_user:CHANGE_ME@db-host:5432/mordoc_db
REDIS_URL=redis://redis-host:6379/0
DJANGO_SECRET_KEY=CHANGE_ME_TO_RANDOM_50_CHARS
DJANGO_ALLOWED_HOSTS=YOUR_VPS_IP
DJANGO_FORCE_SCRIPT_NAME=/mordoc
CORS_ALLOWED_ORIGINS=http://YOUR_VPS_IP

# === RECOMMENDED FOR PRODUCTION ===
DJANGO_DEBUG=0
MEDIA_ROOT=/app/media

# === OPTIONAL (HTTPS) ===
# SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')
```

## Build Arguments Reference Card

```yaml
VITE_BASE: /mordoc  # Change to match your app slug
VITE_API_BASE: /api  # Keep as is
```

## Post-Deployment Checklist

- [ ] Health check returns `{"ok": true}`
- [ ] Application loads at `http://VPS_IP/{slug}/`
- [ ] No 404 errors in browser console
- [ ] Can create a project via UI
- [ ] Can upload a document via UI
- [ ] Admin panel accessible at `http://VPS_IP/{slug}/admin/`
- [ ] Created superuser account

## Updating the Application

To deploy a new version:

1. Push changes to your repository
2. In Keystone, go to your app
3. Click **Redeploy** or **Update**
4. Wait for build and deployment
5. Verify health check

## Backup Recommendations

### Database Backups

```bash
# Backup
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

### Media Files Backup

```bash
# Backup media directory
docker exec <container> tar -czf /tmp/media-backup.tar.gz /app/media/
docker cp <container>:/tmp/media-backup.tar.gz ./media-backup.tar.gz
```

## Monitoring

### Health Check Monitoring

Set up periodic health checks:
```bash
*/5 * * * * curl -f http://YOUR_VPS_IP/mordoc/api/health/ || alert
```

### Log Monitoring

View logs via Keystone dashboard or:
```bash
docker logs -f <container-name>
```

## Support

- **Documentation**: See `docs/` directory
- **Test Plan**: `docs/KEYSTONE_TEST_PLAN.md`
- **Full Report**: `KEYSTONE_COMPATIBILITY_REPORT.md`
- **Issues**: GitHub Issues page

## Quick Reference URLs

Replace `YOUR_VPS_IP` and `mordoc` with your values:

- **App**: `http://YOUR_VPS_IP/mordoc/`
- **API Health**: `http://YOUR_VPS_IP/mordoc/api/health/`
- **Admin**: `http://YOUR_VPS_IP/mordoc/admin/`
- **Traefik Dashboard** (if accessible): `http://YOUR_VPS_IP:8080/`

---

**Last Updated**: 2025-12-24  
**Version**: 1.0  
**Status**: Ready for Production
