# AGENT.md — Autonomous Execution Guide

## Mission
Build **Paperless Modernizer v1** exactly as specified in this repository’s frozen docs.

## Non-negotiables (hard guardrails)
- Build ONLY what is in **docs/Goals.md** (v1 include list).
- Do NOT add PDF/OCR, real-time collaboration, suggestion mode, rich formatting, or editable tables.
- Export correctness beats editor features.
- The canonical block schema is authoritative; do not store arbitrary HTML.

## Operating mode
- Prefer small, verifiable increments.
- Keep endpoints and UI minimal but correct.
- Every feature must be demoable with sample DOCX import → edit → verify → export.

## Tooling
- Backend: Django + DRF + Postgres + Celery + Redis
- Frontend: React + Vite + TypeScript
- Storage: local filesystem in dev, pluggable storage in prod

## Definition of Done (v1)
- Import DOCX → section tree visible in UI
- Outline operations: rename/promote/demote/reorder/merge
- Section editor: boring blocks with minimal inline marks
- Status workflow + reopen with reason + audit
- Section comments (no anchors)
- AI presets return blocks and can be applied
- DOCX export generates styled output via template mapping
- Audit endpoint shows key actions
