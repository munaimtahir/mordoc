# TASKS.md — v1 Implementation Checklist

**Status:** Scaffold Complete → Implementation Phase  
**See `docs/DEVELOPMENT_PLAN.md` for detailed roadmap**

## Backend
- [x] Django project scaffold + DRF
- [x] Models: Project, Document, Section, SectionContent, Comment, Snapshot, AuditLog, ExportJob, Template
- [x] Upload endpoint (DOCX) + storage
- [x] Parse worker: DOCX -> sections + old content (basic implementation)
- [x] Section tree endpoints
- [x] Outline ops: rename, reorder, promote/demote, merge (API endpoints)
- [x] Content endpoints (new blocks) + schema validation
- [x] Workflow status transitions + lock + reopen reason (API endpoints)
- [x] Comments endpoints
- [x] AI endpoint (stub provider) + preset prompt contract
- [x] Export job + worker: build DOCX using template mapping (stub implementation)
- [x] Audit endpoint
- [ ] **TODO:** Enhance DOCX parsing (nested structure detection)
- [ ] **TODO:** Implement template style mapping in export
- [ ] **TODO:** Generate database migrations
- [ ] **TODO:** Create `.env.example` files

## Frontend
- [x] Project list + creation
- [x] Documents upload UI + parse status (basic)
- [x] 3-pane workspace layout
- [ ] **TODO:** Outline tree UI with operations (rename/promote/demote/reorder/merge)
- [x] Split view Old/New
- [ ] **TODO:** Block editor (boring blocks) + inline marks (currently JSON editor)
- [x] Comments panel (basic)
- [ ] **TODO:** History panel (snapshots list) - endpoint exists, UI not wired
- [x] AI Tools panel with presets (stub)
- [ ] **TODO:** Export modal + preflight checks
- [ ] **TODO:** Workflow status UI (status transitions, lock, reopen)
- [ ] **TODO:** Document list by project (endpoint may need addition)
- [ ] **TODO:** Audit log viewer

## DevOps
- [x] Docker Compose: postgres + redis + backend + worker + frontend
- [ ] **TODO:** CI: backend lint/tests + frontend lint/build
- [x] Environment file templates (`.env.example`)
