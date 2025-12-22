# Development Plan — v1 Finalized

**Date:** 2025-12-22  
**Status:** Scaffold Complete → Implementation Phase

## Executive Summary

The Paperless Modernizer v1 scaffold is **structurally complete** with all core models, API endpoints, and basic UI scaffolding in place. The project is ready for feature implementation and UI enhancement phases.

---

## Current Status Assessment

### ✅ Backend — COMPLETE (Scaffold)

#### Models & Database
- ✅ All v1 models implemented (`Project`, `Document`, `Section`, `SectionContent`, `Comment`, `Snapshot`, `AuditLog`, `ExportJob`, `Template`)
- ✅ Relationships and constraints defined
- ✅ Status enums and choices implemented

#### API Endpoints
- ✅ All REST endpoints from `docs/API.md` implemented:
  - Projects: GET, POST
  - Documents: POST upload, GET detail, GET sections tree, GET audit
  - Sections: PATCH (rename/reorder/promote/demote/status), POST merge, GET/PUT content
  - Comments: GET, POST
  - AI: POST section generation
  - Export: POST request, GET status
  - Snapshots: POST
- ✅ Block schema validation (`block_schema.py`)
- ✅ Audit logging service (`services.py`)

#### Background Tasks
- ✅ DOCX parsing worker (`parse_docx`) — basic implementation
- ✅ DOCX export worker (`export_docx`) — stub with placeholder flattening
- ✅ Celery configuration

#### Infrastructure
- ✅ Django + DRF setup
- ✅ PostgreSQL configuration
- ✅ Redis/Celery broker setup
- ✅ Docker Compose orchestration
- ✅ CORS configuration

### ⚠️ Backend — NEEDS IMPROVEMENT

1. **DOCX Parsing** (`tasks.py:parse_docx`)
   - Current: Basic heading detection, flat structure
   - Needed: Better parent-child detection, preserve nested structure
   - Status: Functional but needs enhancement

2. **DOCX Export** (`tasks.py:export_docx`)
   - Current: Stub with basic flattening
   - Needed: Template style mapping implementation (`Template.mapping_json`) with must-match-exact strictness
   - Status: Placeholder only

3. **Missing Environment Files**
   - Need: `backend/.env.example`
   - Need: `frontend/.env.example`

4. **Database Migrations**
   - Need: Initial migration files
   - Need: Migration documentation

5. **Admin Interface**
   - Current: Basic Django admin registration
   - Needed: Enhanced admin for debugging/managing entities

### ✅ Frontend — BASIC SCAFFOLD

#### Implemented
- ✅ 3-pane layout (Projects/Documents | Editor | Right Panel)
- ✅ Project creation and selection
- ✅ Document upload (DOCX)
- ✅ Section tree display
- ✅ Old/New split view (JSON editor for blocks)
- ✅ AI Tools panel (stub presets)
- ✅ Comments panel (basic CRUD)
- ✅ Basic API integration

#### ⚠️ Frontend — CRITICAL GAPS

1. **Block Editor**
   - Current: JSON textarea editor
   - Needed: Proper visual block editor (heading/paragraph/list/image) with inline marks
   - Priority: **HIGH** — Core v1 feature

2. **Outline Operations UI**
   - Current: Read-only tree display
   - Needed:
     - Rename section (inline edit)
     - Promote/demote (change depth/parent)
     - Reorder (drag-drop or up/down buttons)
     - Merge sections (multi-select + merge action)
   - Priority: **HIGH** — Core v1 feature

3. **Workflow Status UI**
   - Current: Status displayed but not editable
   - Needed:
     - Status dropdown/buttons (Not started → Draft → In review → Verified)
     - Lock indicator and behavior
     - Reopen modal (requires reason)
   - Priority: **HIGH** — Core v1 feature

4. **History Panel**
   - Current: Placeholder text
   - Needed: Snapshots list, restore functionality
   - Priority: **MEDIUM**

5. **Export UI**
   - Current: Not implemented
   - Needed:
     - Export button/modal
     - Template selection
     - Preflight checks (warn if not all verified)
     - Download link when ready
   - Priority: **HIGH** — Core v1 feature

6. **Audit Log UI**
   - Current: Endpoint exists, no UI
   - Needed: Audit log viewer (document-level)
   - Priority: **MEDIUM**

7. **Document List**
   - Current: Manual document ID entry
   - Needed: List documents by project
   - Priority: **MEDIUM**

---

## Implementation Roadmap

**Note:** Export correctness is prioritized over editor features. Phases are ordered accordingly.

### Phase 1: Export Foundation (Week 1-2)

#### 1.1 Template Mapping & Export Backend
- [ ] Backend: Implement template style mapping (`Template.mapping_json` → DOCX styles)
- [ ] Backend: Enhance `export_docx` task with proper formatting
- [ ] Backend: Create default templates (1-2 predefined) with must-match-exact style mappings
- [ ] Backend: Template mapping JSON schema documentation
- [ ] Backend: Validate template mapping strictness (must-match-exact official template)

**Acceptance Criteria:**
- Template mapping implementation:
  - Given Template A, Heading level 1 uses DOCX style X, paragraph uses style Y, lists use numbering definition Z
  - Template strictness: must-match-exact (as per Goals.md requirement)
  - Export generates properly styled DOCX matching official template exactly
- At least one template available with complete style mapping
- Template mapping works for export with exact style matching

#### 1.2 Export UI
- [ ] Frontend: Export button/modal
- [ ] Frontend: Template selection dropdown
- [ ] Frontend: Preflight checks (verify status counts)
- [ ] Frontend: Download link when export completes

**Acceptance Criteria:**
- Export UI functional
- Template selection works
- Preflight warns if sections not verified
- Download works
- Exported DOCX matches official template exactly (must-match-exact)

### Phase 2: Editor Features (Week 2-3)

#### 2.1 Block Editor Component
- [ ] Create `BlockEditor` component
- [ ] Implement block types: heading, paragraph, list, image
- [ ] Implement inline marks: bold, italic, link
- [ ] Replace JSON editor in center panel
- [ ] Ensure schema compliance (`block_schema.py`)

**Acceptance Criteria:**
- Visual editing of blocks (not JSON)
- Inline formatting toolbar
- Schema validation on save
- Copy Old → New initializes blocks correctly

#### 2.2 Outline Operations
- [ ] Inline rename (double-click or edit button)
- [ ] Promote/demote buttons (change depth)
- [ ] Reorder controls (up/down arrows or drag-drop)
- [ ] Multi-select for merge
- [ ] Merge confirmation dialog

**Acceptance Criteria:**
- All operations persist via PATCH endpoint
- Tree updates immediately
- Audit log entries created

#### 2.3 Workflow Status UI
- [ ] Status dropdown/buttons in section header
- [ ] Lock indicator (visual + disabled state)
- [ ] Reopen modal (requires reason textarea)
- [ ] Status transition validation

**Acceptance Criteria:**
- Status changes persist
- Lock prevents content edits
- Reopen requires reason and logs audit

### Phase 3: Polish & Enhancements (Week 3)

#### 3.1 History Panel
- [ ] List snapshots for selected section
- [ ] Display snapshot reason and timestamp
- [ ] Restore snapshot functionality (optional for v1)

**Acceptance Criteria:**
- Snapshots visible in History tab
- Can view snapshot content

#### 3.2 Document List Enhancement
- [ ] Add `GET /api/projects/:id/documents` endpoint (if missing)
- [ ] Display documents list in left panel
- [ ] Show parse status per document

**Acceptance Criteria:**
- Documents list visible per project
- Parse status updates in real-time

#### 3.3 DOCX Parsing Improvements
- [ ] Better parent-child detection (nested headings)
- [ ] Preserve document structure hierarchy
- [ ] Handle edge cases (no headings, malformed DOCX)

**Acceptance Criteria:**
- Nested sections parsed correctly
- Tree structure matches document outline

### Phase 4: Testing & QA (Week 4)

#### 4.1 Backend Tests
- [ ] Unit tests: section tree operations
- [ ] Unit tests: merge behavior
- [ ] Unit tests: status transitions
- [ ] Unit tests: block schema validation
- [ ] Integration tests: DOCX parse → export cycle

#### 4.2 Frontend Tests (Optional)
- [ ] Component tests for BlockEditor
- [ ] E2E checklist (manual QA acceptable for v1)

#### 4.3 QA Checklist Execution
- [ ] Run through `docs/QA-Checklist.md`
- [ ] Fix critical bugs
- [ ] Document known limitations

### Phase 5: DevOps & Documentation (Week 4)

#### 5.1 Environment Setup
- [ ] Create `backend/.env.example`
- [ ] Create `frontend/.env.example`
- [ ] Document environment variables

#### 5.2 Database Migrations
- [ ] Generate initial migrations
- [ ] Test migration path
- [ ] Document migration commands

#### 5.3 CI/CD Setup
- [ ] Backend linting (ruff)
- [ ] Backend tests
- [ ] Frontend linting (eslint)
- [ ] Frontend build check
- [ ] Docker image builds (optional)

#### 5.4 Documentation
- [ ] Update README with setup instructions
- [ ] Document API endpoints (OpenAPI/Swagger optional)
- [ ] Create user guide (basic)

---

## Technical Debt & Future Considerations

### Known Limitations (v1 Acceptable)
1. **AI Provider**: Currently stubbed. Replace `StubProvider` with real provider when ready.
2. **Authentication**: Not implemented (v1 scope allows anonymous access for demo)
3. **Image Assets**: Upload/storage not fully implemented (placeholder)
4. **Real-time Updates**: Parse/export status polling (not WebSocket)
5. **Error Handling**: Basic error messages (can be enhanced)

### Out of Scope (v1 Frozen)
- PDF import, OCR, scanned docs
- Real-time collaboration
- Track-changes / suggestion mode
- Block-level comment anchors
- Editable tables
- Rich formatting (fonts/colors/custom spacing)

---

## Definition of Done (v1 MVP)

A feature is "done" when:

1. ✅ **Backend**: Endpoint implemented, tested, documented
2. ✅ **Frontend**: UI component implemented, integrated with API
3. ✅ **Schema**: Block schema validation passes
4. ✅ **Audit**: Key actions logged
5. ✅ **Export**: Can export to DOCX with template mapping
6. ✅ **QA**: Passes relevant checklist items

### End-to-End Demo Flow
1. Upload DOCX → parse completes → section tree visible
2. Rename/promote/demote/reorder sections → tree updates
3. Select section → edit blocks → save → status changes
4. Add comments → visible in panel
5. Run AI preset → apply blocks → save
6. Change status to Verified → section locks
7. Export DOCX → download → verify styling

---

## Priority Matrix

| Feature | Priority | Effort | Dependencies |
|---------|----------|--------|--------------|
| Template Mapping & Export Backend | HIGH | High | None |
| Export UI | HIGH | Medium | Export backend |
| Block Editor | HIGH | High | None |
| Outline Ops | HIGH | Medium | None |
| Workflow Status | HIGH | Low | None |
| History Panel | MEDIUM | Low | None |
| Document List | MEDIUM | Low | Backend endpoint |
| Audit Log UI | MEDIUM | Low | None |
| DOCX Parse Enhance | MEDIUM | Medium | None |
| Tests | MEDIUM | High | All features |

---

## Next Steps (Immediate)

1. **Create environment files** (`backend/.env.example`, `frontend/.env.example`)
2. **Generate database migrations** (`python manage.py makemigrations`)
3. **Start Phase 1.1**: Template Mapping & Export Backend (prioritizing export correctness)
4. **Set up development environment** (verify Docker Compose works)

---

## Notes

- This plan respects the **frozen v1 scope** from `docs/Goals.md`
- All features must align with `docs/BlockSchema.md` canonical schema
- **Export correctness is prioritized over editor features** — phases are ordered accordingly
- Template strictness: **must-match-exact** official template (as per Goals.md)
- Keep changes small and testable
- Follow `docs/AGENT.md` operating principles

---

**Last Updated:** 2025-12-22  
**Review Status:** Ready for implementation

