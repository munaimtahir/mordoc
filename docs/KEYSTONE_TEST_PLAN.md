# Keystone Compatibility Test Plan

This document provides a comprehensive test plan to verify that mordoc works correctly when deployed via Keystone with path-based routing.

## Overview

Keystone uses Traefik reverse proxy with PATH-BASED routing. When accessing an app:
- **Browser URL**: `http://VPS_IP/{APP_SLUG}/...` (e.g., `http://1.2.3.4/mordoc/`)
- **Container receives**: Requests with `{APP_SLUG}` stripped (appears as `/`)
- **Critical requirement**: All browser-side URLs must work relative to `/{APP_SLUG}/`

## Test Categories

### 1. Local Development Test (Root Path)

**Purpose**: Ensure changes don't break local development workflow

**Setup**:
```bash
cd mordoc
docker compose up --build
```

**Tests**:
- [ ] Frontend loads at `http://localhost:5173/`
- [ ] Backend API responds at `http://localhost:8000/api/health/`
- [ ] Django admin accessible at `http://localhost:8000/admin/`
- [ ] Can create project via UI
- [ ] Can upload document via UI
- [ ] Static files (CSS/JS) load correctly (check browser DevTools Network tab)

**Expected**: All tests pass, no 404 errors

---

### 2. Docker Single-Container Test (Root Path)

**Purpose**: Verify production Docker build works at root path

**Setup**:
```bash
# Build with default settings (root path)
docker build -t mordoc:test .

# Run with test database
docker run -d --name mordoc-test -p 8000:8000 \
  -e DATABASE_URL="sqlite:////app/test.db" \
  -e REDIS_URL="redis://localhost:6379/0" \
  -e DJANGO_SECRET_KEY="test-key-123" \
  -e DJANGO_DEBUG=1 \
  -e DJANGO_ALLOWED_HOSTS="*" \
  mordoc:test

# Wait for startup
sleep 10
```

**Tests**:
- [ ] Health check: `curl http://localhost:8000/api/health/`
- [ ] Frontend loads: Open `http://localhost:8000/` in browser
- [ ] Static assets load (check Network tab for `/static/` files)
- [ ] Index.html served for non-API routes: `curl http://localhost:8000/projects`
- [ ] API endpoints work: `curl http://localhost:8000/api/projects`

**Cleanup**:
```bash
docker stop mordoc-test && docker rm mordoc-test
```

**Expected**: All tests pass, app fully functional at root path

---

### 3. Keystone Simulation Test (Subpath)

**Purpose**: Simulate Keystone's path-based routing with Traefik

#### Option A: Using Test Traefik Setup (Recommended)

**Setup**:

Create `test-traefik/docker-compose.traefik.yml`:
```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
    ports:
      - "80:80"
      - "8080:8080"  # Traefik dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - platform

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: paperless
      POSTGRES_USER: paperless
      POSTGRES_PASSWORD: paperless
    networks:
      - platform
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    networks:
      - platform

  mordoc:
    build:
      context: ..
      args:
        VITE_BASE: /mordoc  # Build with subpath support
    environment:
      DATABASE_URL: postgres://paperless:paperless@db:5432/paperless
      REDIS_URL: redis://redis:6379/0
      DJANGO_SECRET_KEY: test-secret-key-change-me
      DJANGO_DEBUG: "0"
      DJANGO_ALLOWED_HOSTS: "*"
      DJANGO_FORCE_SCRIPT_NAME: /mordoc  # Critical for subpath
      CORS_ALLOWED_ORIGINS: http://localhost
    networks:
      - platform
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.mordoc.rule=PathPrefix(`/mordoc`)"
      - "traefik.http.routers.mordoc.entrypoints=web"
      - "traefik.http.services.mordoc.loadbalancer.server.port=8000"
      - "traefik.http.middlewares.mordoc-stripprefix.stripprefix.prefixes=/mordoc"
      - "traefik.http.routers.mordoc.middlewares=mordoc-stripprefix"
    depends_on:
      - db
      - redis

networks:
  platform:
    driver: bridge

volumes:
  postgres_data:
```

**Start Test Environment**:
```bash
cd test-traefik
docker compose -f docker-compose.traefik.yml up --build -d
# Wait for services to start
sleep 30
```

**Tests**:

1. **Frontend loads under subpath**:
   - [ ] Open `http://localhost/mordoc/` in browser
   - [ ] Page loads without errors
   - [ ] No 404s in Network tab

2. **Static files load correctly**:
   - [ ] Open browser DevTools → Network tab
   - [ ] Verify assets load from `/mordoc/static/...` or similar
   - [ ] No requests to `/static/` at VPS root

3. **API calls work**:
   - [ ] `curl http://localhost/mordoc/api/health/` returns `{"ok": true}`
   - [ ] `curl http://localhost/mordoc/api/projects` returns `[]`

4. **Navigation stays within subpath**:
   - [ ] Create a project via UI
   - [ ] Verify browser URL stays as `http://localhost/mordoc/...`
   - [ ] Click through UI elements
   - [ ] URL should never jump to `http://localhost/...` (without /mordoc)

5. **SPA routing works**:
   - [ ] Navigate to a project in UI
   - [ ] Copy the URL (e.g., `http://localhost/mordoc/`)
   - [ ] Open in new tab or refresh page
   - [ ] App loads correctly (not 404)

6. **API calls from frontend work**:
   - [ ] Create project via UI (tests POST /api/projects)
   - [ ] Upload document (tests POST with FormData)
   - [ ] View document sections (tests GET /api/documents/:id/sections)
   - [ ] Check Network tab: all API calls go to `/mordoc/api/...`

7. **Media files (if any)**:
   - [ ] Upload document with images
   - [ ] Verify media URLs work under subpath

**Cleanup**:
```bash
docker compose -f docker-compose.traefik.yml down -v
```

#### Option B: Using nginx Reverse Proxy (Alternative)

If Traefik is not available, use nginx:

Create `test-nginx/nginx.conf`:
```nginx
events {
    worker_connections 1024;
}

http {
    upstream mordoc {
        server mordoc:8000;
    }

    server {
        listen 80;
        
        location /mordoc/ {
            proxy_pass http://mordoc/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $host;
        }
    }
}
```

Create `test-nginx/docker-compose.nginx.yml`:
```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - mordoc
    networks:
      - testnet

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: paperless
      POSTGRES_USER: paperless
      POSTGRES_PASSWORD: paperless
    networks:
      - testnet

  redis:
    image: redis:7-alpine
    networks:
      - testnet

  mordoc:
    build:
      context: ..
      args:
        VITE_BASE: /mordoc
    environment:
      DATABASE_URL: postgres://paperless:paperless@db:5432/paperless
      REDIS_URL: redis://redis:6379/0
      DJANGO_SECRET_KEY: test-secret
      DJANGO_DEBUG: "0"
      DJANGO_ALLOWED_HOSTS: "*"
      DJANGO_FORCE_SCRIPT_NAME: /mordoc
      CORS_ALLOWED_ORIGINS: http://localhost
    networks:
      - testnet
    depends_on:
      - db
      - redis

networks:
  testnet:
    driver: bridge
```

Run same tests as Option A.

---

### 4. Negative Pattern Check

**Purpose**: Ensure no dangerous hardcoded paths remain

**Search patterns that MUST NOT appear in browser-side code**:

```bash
cd /home/runner/work/mordoc/mordoc

# Check frontend for absolute paths (should return nothing or only safe cases)
grep -r 'href="/' frontend/src/
grep -r 'src="/' frontend/src/
grep -r "fetch('/" frontend/src/
grep -r 'fetch("/' frontend/src/

# Check HTML files
grep 'href="/' frontend/index.html
grep 'src="/' frontend/index.html
```

**Allowed exceptions**:
- External URLs (e.g., `href="https://..."`)
- URLs constructed dynamically with base path

**Expected**: No hardcoded root-absolute paths in browser code

---

### 5. Environment Variable Test Matrix

Test different environment configurations:

| Test Case | DJANGO_FORCE_SCRIPT_NAME | VITE_BASE (build) | Expected Result |
|-----------|-------------------------|-------------------|-----------------|
| Local Dev | (empty) | / | Works at root |
| Docker Root | (empty) | / | Works at root |
| Keystone Subpath | /mordoc | /mordoc | Works at /mordoc |
| Custom Subpath | /myapp | /myapp | Works at /myapp |

---

## Automated Test Suite

### Backend Tests

Run existing Django tests to ensure no regressions:

```bash
cd backend
python manage.py test core.tests --verbosity=2
```

**Expected**: All tests pass

### Frontend Build Test

Verify frontend builds correctly with different base paths:

```bash
cd frontend

# Test 1: Root path build
VITE_BASE=/ npm run build
# Check: dist/index.html should have correct paths

# Test 2: Subpath build
VITE_BASE=/mordoc npm run build
# Check: dist/index.html should have /mordoc prefix where needed
```

---

## Success Criteria

The application is considered **Keystone-ready** when:

✅ **All local development tests pass** (no regression)
✅ **Docker single-container tests pass** (production build works at root)
✅ **Keystone simulation tests pass** (all functionality works under subpath)
✅ **No dangerous patterns found** (no hardcoded root-absolute paths)
✅ **Environment variable matrix tests pass** (flexible configuration)
✅ **Automated tests pass** (no regressions in backend logic)

---

## Known Limitations

- **WebSockets**: Not tested (app doesn't use WebSockets currently)
- **Real Keystone Environment**: Final verification requires actual Keystone deployment
- **HTTPS**: Test plan uses HTTP; HTTPS should work the same with proper SECURE_PROXY_SSL_HEADER

---

## Troubleshooting

### Issue: Static files 404 under subpath

**Check**:
- Is `DJANGO_FORCE_SCRIPT_NAME` set correctly?
- Is `VITE_BASE` used during Docker build?
- Run `docker exec <container> ls /app/staticfiles` to verify files collected

### Issue: API calls go to root instead of subpath

**Check**:
- Frontend API_BASE should be `/api` (relative), not `http://...`
- Inspect browser Network tab for actual URLs called

### Issue: SPA routes 404 on refresh

**Check**:
- Django catch-all route in `config/urls.py` should serve `index.html`
- `WHITENOISE_INDEX_FILE = True` in settings

### Issue: CORS errors

**Check**:
- `CORS_ALLOWED_ORIGINS` should match the browser's origin
- For Keystone: `http://VPS_IP` (no port, no path)
- `CORS_ALLOW_CREDENTIALS = True` should be set

---

## Test Execution Log

Use this section to record test results:

```
Date: _______________
Tester: _______________

[ ] Local Development Test - PASS/FAIL
[ ] Docker Single-Container Test - PASS/FAIL  
[ ] Keystone Simulation Test - PASS/FAIL
[ ] Negative Pattern Check - PASS/FAIL
[ ] Environment Variable Matrix - PASS/FAIL
[ ] Automated Tests - PASS/FAIL

Notes:
_______________________________
_______________________________
```

---

## Deployment Checklist for Keystone

When deploying to actual Keystone:

- [ ] Repository added to Keystone
- [ ] App created with slug (e.g., "mordoc")
- [ ] Environment variables configured:
  - [ ] `DATABASE_URL`
  - [ ] `REDIS_URL`
  - [ ] `DJANGO_SECRET_KEY` (changed from default!)
  - [ ] `DJANGO_DEBUG=0`
  - [ ] `DJANGO_ALLOWED_HOSTS` (VPS IP or domain)
  - [ ] `DJANGO_FORCE_SCRIPT_NAME=/{APP_SLUG}`
  - [ ] `CORS_ALLOWED_ORIGINS` (VPS IP without port)
- [ ] Build arguments configured:
  - [ ] `VITE_BASE=/{APP_SLUG}`
- [ ] Health check configured: `/api/health/`
- [ ] App deployed successfully
- [ ] Access app at `http://VPS_IP/{APP_SLUG}/`
- [ ] Verify all test cases from simulation

---

**Last Updated**: 2025-12-24
**Version**: 1.0
