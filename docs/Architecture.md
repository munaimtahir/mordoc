# Architecture.md — v1

## Core concept
Every document becomes a **tree of sections**. Each section has:
- `oldContent` (read-only, extracted from DOCX)
- `newContent` (block JSON following canonical schema)
- workflow status + lock/verify
- comments (section-level)
- snapshots + audit

## Components
### Frontend (React)
- 3-pane workspace:
  - Left: outline tree + operations (rename/reorder/promote/demote/merge)
  - Center: split view (Old | New) with boring block editor
  - Right: AI Tools | Comments | History | QA

### Backend (Django + DRF)
- REST API
- Background jobs:
  - DOCX parse
  - DOCX export
- Storage:
  - uploads + exported versions + image assets

### Data stores
- PostgreSQL for entities (documents, sections, comments, audit)
- Redis for Celery broker/cache/locks (dev)

## Export-first principle
Export constraints drive:
- what editor can produce
- what block schema permits
- what templates/styles are mapped

## Template mapping
**Template strictness: must-match-exact** (as per Goals.md requirement — must-match official template)

### Acceptance criteria
Given Template A:
- Heading level 1 uses DOCX style X
- Paragraph uses style Y
- Lists use numbering definition Z
- All style mappings must exactly match the official template

Templates define DOCX styles and mappings with must-match-exact strictness. Export generates DOCX that matches the official template exactly.

## AI integration
Section-only. Presets return blocks or markdown that is converted to blocks.
Human acceptance required before applying.
