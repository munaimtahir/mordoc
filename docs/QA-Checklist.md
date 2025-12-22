# QA-Checklist.md — v1

## Import
- [ ] Upload DOCX works
- [ ] Parse completes and section tree is created
- [ ] Old content appears per section

## Outline operations
- [ ] Rename heading
- [ ] Promote/demote changes nesting
- [ ] Reorder persists orderIndex
- [ ] Merge creates new section and preserves old lineage in audit

## Editing
- [ ] Block editor supports heading/paragraph/list/image
- [ ] Inline marks: bold/italic/link preserved in storage
- [ ] Copy Old → New initializes blocks

## Workflow
- [ ] Status transitions work
- [ ] Verify locks section
- [ ] Reopen requires reason and logs audit

## AI
- [ ] Presets run per section
- [ ] Output converts to blocks
- [ ] Apply requires explicit accept

## Export
- [ ] Template style mapping applied
- [ ] DOCX export builds and downloads
- [ ] Export preflight warns if not all verified
- [ ] Admin override logged

## Audit
- [ ] Key actions recorded and retrievable
