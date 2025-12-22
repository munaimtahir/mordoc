# DataModel.md — v1

## Entities

### Project
- id (uuid)
- name
- description
- created_by, created_at

### Document
- id (uuid)
- project_id
- title
- source_file_path
- parse_status (pending/running/done/failed)
- template_id
- created_by, created_at

### Section
- id (uuid)
- document_id
- parent_id (nullable)
- order_index (int)
- heading (string)
- depth (int)
- old_content_raw (text)
- old_content_normalized (text)
- status (not_started/draft/in_review/verified)
- locked (bool)
- reopen_reason (nullable text)
- updated_by, updated_at

### SectionContent
- section_id (pk/fk)
- schema_version (int=1)
- blocks_json (json)

### Comment
- id (uuid)
- section_id
- author_id
- body
- status (open/resolved)
- created_at

### Snapshot
- id (uuid)
- section_id
- saved_by
- reason (nullable)
- blocks_json (json)
- saved_at

### AuditLog
- id (uuid)
- entity_type (project/document/section/export/ai)
- entity_id (uuid)
- action (string)
- actor_id
- payload (json)
- created_at
