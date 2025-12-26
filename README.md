# Paperless Modernizer (v1)

A schema-first, export-driven, section-tree editor for modernizing legacy university documents.

![CI Status](https://github.com/your-username/mordoc/actions/workflows/ci.yml/badge.svg)

## v1 is frozen

This repository is scoped to the v1 MVP only. Anything not on the **Include list** is **out of scope** for v1.

## What it does (v1)

- ✅ Import **DOCX** → best-effort parse into a **section tree**
- ✅ Manual outline fix: rename, promote/demote, reorder, merge
- ✅ Section editor with boring blocks: heading, paragraph, list, image (+ minimal inline marks)
- ✅ Section workflow: Not started → Draft → In review → Verified (Reopen w/ reason)
- ✅ Section-level comments (no anchors)
- ✅ Section-only AI presets → produce blocks (stub provider)
- ✅ Export **DOCX** via strict template style mapping
- ✅ Audit log for key actions
- ✅ History/Snapshots with restore functionality

## What it does not do (v1)

- ❌ PDF/OCR/scanned docs
- ❌ Real-time collaboration / multi-cursor
- ❌ Track-changes / suggestion mode
- ❌ Block-level comment anchors
- ❌ Editable tables
- ❌ Rich formatting (fonts/colors/custom spacing)

## Screenshots

The application features a 3-pane layout:
- **Left**: Projects, Documents, and Section Outline with operations
- **Center**: Split view with Original content and Block Editor
- **Right**: AI Tools, Comments, History, and Audit tabs

## Quick Start (Development)

### Prerequisites

- Docker Desktop
- Git

### Option A: Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/mordoc.git
   cd mordoc
   ```

2. **Copy environment files:**
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```

3. **Start all services:**
   ```bash
   docker compose up --build
   ```

4. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000/api/health/
   - Django Admin: http://localhost:8000/admin/

5. **Seed default templates (optional):**
   ```bash
   docker compose exec backend python manage.py seed_templates
   ```

### Option B: Local Development

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgres://paperless:paperless@localhost:5432/paperless"
export REDIS_URL="redis://localhost:6379/0"
export DJANGO_SECRET_KEY="dev-secret-key"
export DJANGO_DEBUG="1"

# Run migrations
python manage.py migrate

# Seed templates
python manage.py seed_templates

# Start server
python manage.py runserver
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Repository Layout

```
├── backend/               # Django + DRF API
│   ├── config/           # Django settings
│   ├── core/             # Main application
│   │   ├── models.py     # Data models
│   │   ├── views.py      # API endpoints
│   │   ├── tasks.py      # Celery background tasks
│   │   ├── block_schema.py    # Block validation
│   │   ├── template_mapping.py # DOCX export mapping
│   │   └── tests/        # Unit & integration tests
│   ├── Dockerfile        # Backend container
│   └── worker.Dockerfile # Celery worker container
├── frontend/             # React + Vite + TypeScript
│   └── src/
│       └── ui/
│           ├── App.tsx   # Main application
│           └── styles.css # Styling
├── docs/                 # Documentation
│   ├── Goals.md         # v1 scope (frozen)
│   ├── Architecture.md  # System design
│   ├── API.md          # REST endpoints
│   ├── BlockSchema.md  # Canonical block schema
│   └── DEVELOPMENT_PLAN.md # Implementation roadmap
└── docker-compose.yml   # Docker orchestration
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects` | List all projects |
| POST | `/api/projects` | Create project |
| POST | `/api/projects/:id/documents` | Upload DOCX |
| GET | `/api/projects/:id/documents/list` | List project documents |
| GET | `/api/documents/:id` | Get document details |
| GET | `/api/documents/:id/sections` | Get section tree |
| GET | `/api/documents/:id/audit` | Get audit logs |
| GET | `/api/documents/:id/export/preflight` | Export preflight check |
| POST | `/api/documents/:id/export` | Start export job |
| PATCH | `/api/sections/:id` | Update section (rename/status/reorder) |
| POST | `/api/sections/merge` | Merge sections |
| GET | `/api/sections/:id/old` | Get original content |
| GET/PUT | `/api/sections/:id/new` | Get/update block content |
| POST | `/api/sections/:id/snapshot` | Create snapshot |
| GET | `/api/sections/:id/snapshots` | List snapshots |
| POST | `/api/sections/:id/snapshots/:sid/restore` | Restore snapshot |
| GET/POST | `/api/sections/:id/comments` | List/create comments |
| POST | `/api/ai/section` | Run AI preset |
| GET | `/api/templates` | List templates |
| GET | `/api/exports/:id` | Get export job status |

## Block Schema

The editor uses a canonical block schema (v1):

```json
{
  "version": 1,
  "blocks": [
    { "id": "h1", "type": "heading", "level": 1, "text": "Title" },
    { "id": "p1", "type": "paragraph", "text": "Content", "marks": [] },
    { "id": "list1", "type": "list", "style": "bulleted", "items": ["A", "B"] },
    { "id": "img1", "type": "image", "assetId": "...", "caption": "..." }
  ]
}
```

Supported inline marks: `bold`, `italic`, `link`

## Testing

### Backend Tests

```bash
cd backend
python manage.py test core.tests --verbosity=2
```

### Frontend Build

```bash
cd frontend
npm run build
```

## Development Workflow

1. Upload a DOCX document
2. Wait for parsing to complete
3. Select a section from the outline
4. Edit content using the block editor
5. Use AI presets to help modernize content
6. Add comments for reviewers
7. Progress through status workflow: Not Started → Draft → In Review → Verified
8. Export to DOCX when all sections are verified

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | Required |
| `DJANGO_DEBUG` | Debug mode | `1` |
| `DJANGO_ALLOWED_HOSTS` | Allowed hosts | `localhost,127.0.0.1` |
| `DATABASE_URL` | PostgreSQL connection | Required |
| `REDIS_URL` | Redis connection | Required |
| `CORS_ALLOWED_ORIGINS` | CORS origins | `http://localhost:5173` |
| `MEDIA_ROOT` | Media storage path | `/app/media` |

### Frontend (`frontend/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE` | Backend API URL | `http://localhost:8000/api` |

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## Deployment

### Keystone Deployment

Mordoc is **fully compatible** with [Keystone](https://github.com/your-username/keystone) for path-based deployment.

**Quick Start**: See [KEYSTONE_QUICK_START.md](KEYSTONE_QUICK_START.md)  
**Full Report**: See [KEYSTONE_COMPATIBILITY_REPORT.md](KEYSTONE_COMPATIBILITY_REPORT.md)  
**Test Plan**: See [docs/KEYSTONE_TEST_PLAN.md](docs/KEYSTONE_TEST_PLAN.md)

**Key Features**:
- ✅ Works at subpaths (e.g., `http://VPS_IP/mordoc/`)
- ✅ Traefik reverse proxy compatible
- ✅ Single container deployment
- ✅ WhiteNoise for static files
- ✅ Automated migrations and setup
- ✅ Health check endpoint: `/api/health/`

**Required Environment Variables**:
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis for Celery
- `DJANGO_SECRET_KEY` - Security key
- `DJANGO_FORCE_SCRIPT_NAME` - Your app slug (e.g., `/mordoc`)
- `DJANGO_ALLOWED_HOSTS` - Your VPS IP/domain
- `CORS_ALLOWED_ORIGINS` - Your VPS IP

The Dockerfile at the root builds both frontend and backend into a single container optimized for Keystone deployment.

## License

MIT

---

**Date:** 2025-12-22  
**Version:** 1.0.0
