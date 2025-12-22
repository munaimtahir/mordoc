# API.md — v1 REST

## Projects
- POST /api/projects
- GET /api/projects

## Documents
- POST /api/projects/:id/documents (multipart upload)
- GET /api/documents/:id
- GET /api/documents/:id/sections (tree)
- GET /api/documents/:id/audit

## Sections (structure + workflow)
- PATCH /api/sections/:id
  - rename, parentId, orderIndex, status, reopenReason
- POST /api/sections/merge
  - { documentId, sourceSectionIds[], targetHeading? } -> newSectionId

## Content
- GET /api/sections/:id/old
- GET /api/sections/:id/new
- PUT /api/sections/:id/new
- POST /api/sections/:id/snapshot

## Comments
- GET /api/sections/:id/comments
- POST /api/sections/:id/comments
- PATCH /api/comments/:id

## AI
- POST /api/ai/section
  - { sectionId, preset, inputs, options } -> blocks (schema v1)

## Export
- POST /api/documents/:id/export
  - { templateId } -> exportJobId
- GET /api/exports/:id
