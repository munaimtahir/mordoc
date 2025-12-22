# QA-Checklist.md — v1

## Import
- [x] Upload DOCX works
- [x] Parse completes and section tree is created
- [x] Old content appears per section

## Outline operations
- [x] Rename heading
- [x] Promote/demote changes nesting
- [x] Reorder persists orderIndex
- [x] Merge creates new section and preserves old lineage in audit

## Editing
- [x] Block editor supports heading/paragraph/list/image
- [x] Inline marks: bold/italic/link preserved in storage
- [x] Copy Old → New initializes blocks

## Workflow
- [x] Status transitions work
- [x] Verify locks section
- [x] Reopen requires reason and logs audit

## AI
- [x] Presets run per section
- [x] Output converts to blocks
- [x] Apply requires explicit accept

## Export
- [x] Template style mapping applied
- [x] DOCX export builds and downloads
- [x] Export preflight warns if not all verified
- [~] Admin override logged (export is logged, but no explicit "admin override" flag)

## Audit
- [x] Key actions recorded and retrievable

---
**Last Audit:** 2025-12-22  
**Status:** 20/21 items complete (95%)  
**See:** `docs/QA-AUDIT-REPORT.md` for detailed verification
