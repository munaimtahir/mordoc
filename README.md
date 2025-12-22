# Paperless Modernizer (v1 Frozen)

A schema-first, export-driven, section-tree editor for modernizing legacy university documents.

## v1 is frozen
This repository is scoped to the v1 MVP only. Anything not on the **Include list** is **out of scope** for v1.

## What it does (v1)
- Import **DOCX** → best-effort parse into a **section tree**
- Manual outline fix: rename, promote/demote, reorder, merge
- Section editor with boring blocks: heading, paragraph, list, image (+ minimal inline marks)
- Section workflow: Not started → Draft → In review → Verified (Reopen w/ reason)
- Section-level comments (no anchors)
- Section-only AI presets → produce blocks
- Export **DOCX** via strict template style mapping
- Audit log for key actions

## What it does not do (v1)
- PDF/OCR/scanned docs
- Real-time collaboration / multi-cursor
- Track-changes / suggestion mode
- Block-level comment anchors
- Editable tables
- Rich formatting (fonts/colors/custom spacing)

## Quick start (dev)
### Option A: Docker (recommended)
1. Copy env files:
   - `cp backend/.env.example backend/.env`
   - `cp frontend/.env.example frontend/.env`
2. Run:
   - `docker compose up --build`
3. Open:
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000/api/health/

### Option B: Local (manual)
See `docs/Setup.md`

## Repository layout
- `backend/` Django + DRF API (Celery workers for parse/export jobs)
- `frontend/` React + Vite + TypeScript (3-pane editor UI)
- `docs/` Frozen v1 spec and AI-agent execution pack
- `.github/` Issue templates + CI

## Date
2025-12-22
