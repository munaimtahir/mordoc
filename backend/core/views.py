from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Count
from .models import Project, Document, Section, SectionContent, Comment, Snapshot, AuditLog, ExportJob, Template
from .serializers import (
    ProjectSerializer, DocumentSerializer, SectionSerializer, SectionContentSerializer,
    CommentSerializer, SnapshotSerializer, AuditLogSerializer, ExportJobSerializer, TemplateSerializer
)
from .block_schema import validate_blocks
from .services import log_action, enforce_lock
from .tasks import parse_docx, export_docx
from .ai import get_provider
from .template_mapping import DEFAULT_MAPPING

@api_view(["GET"])
def health(request):
    return Response({"ok": True})

@api_view(["GET","POST"])
def projects(request):
    if request.method == "GET":
        return Response(ProjectSerializer(Project.objects.all().order_by("-created_at"), many=True).data)
    ser = ProjectSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    obj = ser.save()
    log_action("project", obj.id, "create_project", {"name": obj.name})
    return Response(ProjectSerializer(obj).data, status=201)

@api_view(["POST"])
def upload_document(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    title = request.data.get("title") or "Untitled"
    f = request.FILES.get("file")
    if not f:
        return Response({"error":"file required"}, status=400)
    doc = Document.objects.create(project=project, title=title, source_file=f)
    log_action("document", doc.id, "upload_document", {"title": title})
    parse_docx.delay(str(doc.id))
    return Response(DocumentSerializer(doc).data, status=201)

@api_view(["GET"])
def document_detail(request, document_id):
    doc = get_object_or_404(Document, id=document_id)
    return Response(DocumentSerializer(doc).data)

def _build_tree(sections):
    # v1: parent can be null; build simple nested structure if present
    by_id = {str(s.id): s for s in sections}
    children = {str(s.id): [] for s in sections}
    roots = []
    for s in sections:
        pid = str(s.parent_id) if s.parent_id else None
        if pid and pid in children:
            children[pid].append(s)
        else:
            roots.append(s)
    def node(s):
        return {
            "id": str(s.id),
            "heading": s.heading,
            "status": s.status,
            "locked": s.locked,
            "order_index": s.order_index,
            "depth": s.depth,
            "children": [node(c) for c in sorted(children[str(s.id)], key=lambda x: x.order_index)],
        }
    return [node(s) for s in sorted(roots, key=lambda x: x.order_index)]

@api_view(["GET"])
def document_sections(request, document_id):
    doc = get_object_or_404(Document, id=document_id)
    sections = Section.objects.filter(document=doc)
    return Response({"tree": _build_tree(sections)})

@api_view(["PATCH"])
def section_patch(request, section_id):
    sec = get_object_or_404(Section, id=section_id)

    # lock enforcement for edits affecting content/workflow
    if sec.locked:
        # allow reopen with reason (status change) only
        if request.data.get("status") != Section.Status.DRAFT or not request.data.get("reopen_reason"):
            return Response({"error":"Section locked. Reopen with reason to edit."}, status=400)

    before = {"heading": sec.heading, "parent": str(sec.parent_id) if sec.parent_id else None,
              "order_index": sec.order_index, "status": sec.status, "locked": sec.locked}

    # fields
    if "heading" in request.data:
        sec.heading = request.data["heading"]
    if "parent" in request.data:
        sec.parent_id = request.data["parent"]
    if "order_index" in request.data:
        sec.order_index = int(request.data["order_index"])
    if "depth" in request.data:
        sec.depth = int(request.data["depth"])

    if "status" in request.data:
        new_status = request.data["status"]
        # verify locks
        if new_status == Section.Status.VERIFIED:
            sec.locked = True
        # reopen path
        if sec.locked and new_status == Section.Status.DRAFT:
            sec.locked = False
            sec.reopen_reason = request.data.get("reopen_reason", "")
            log_action("section", sec.id, "reopen_section", {"reason": sec.reopen_reason})
        sec.status = new_status

    sec.save()

    after = {"heading": sec.heading, "parent": str(sec.parent_id) if sec.parent_id else None,
             "order_index": sec.order_index, "status": sec.status, "locked": sec.locked}
    log_action("section", sec.id, "patch_section", {"before": before, "after": after})
    return Response(SectionSerializer(sec).data)

@api_view(["POST"])
def merge_sections(request):
    document_id = request.data.get("documentId")
    source_ids = request.data.get("sourceSectionIds", [])
    target_heading = request.data.get("targetHeading") or "Merged Section"
    if not document_id or len(source_ids) < 2:
        return Response({"error":"documentId and >=2 sourceSectionIds required"}, status=400)
    doc = get_object_or_404(Document, id=document_id)
    sources = list(Section.objects.filter(document=doc, id__in=source_ids).order_by("order_index"))
    if len(sources) < 2:
        return Response({"error":"invalid source sections"}, status=400)

    with transaction.atomic():
        merged_old = "\n\n".join([s.old_content_raw for s in sources]).strip()
        new_sec = Section.objects.create(
            document=doc,
            parent=None,
            order_index=min(s.order_index for s in sources),
            heading=target_heading,
            depth=min(s.depth for s in sources) if sources else 1,
            old_content_raw=merged_old,
            old_content_normalized=merged_old,
            status=Section.Status.NOT_STARTED,
            locked=False,
        )
        SectionContent.objects.create(section=new_sec, schema_version=1, blocks_json={"version":1,"blocks":[]})
        # remove sources (v1 simple). Alternative: mark archived.
        deleted = [str(s.id) for s in sources]
        Section.objects.filter(id__in=source_ids).delete()
        log_action("document", doc.id, "merge_sections", {"deleted": deleted, "created": str(new_sec.id)})
    return Response({"newSectionId": str(new_sec.id)})

@api_view(["GET"])
def section_old(request, section_id):
    sec = get_object_or_404(Section, id=section_id)
    return Response({"old": sec.old_content_raw})

@api_view(["GET","PUT"])
def section_new(request, section_id):
    sec = get_object_or_404(Section, id=section_id)
    if request.method == "GET":
        content = getattr(sec, "content", None)
        if not content:
            SectionContent.objects.create(section=sec, schema_version=1, blocks_json={"version":1,"blocks":[]})
            content = sec.content
        return Response(content.blocks_json)

    # PUT
    if sec.locked:
        return Response({"error":"Section locked. Reopen with reason to edit."}, status=400)
    ok, msg = validate_blocks(request.data)
    if not ok:
        return Response({"error": msg}, status=400)
    content = getattr(sec, "content", None)
    if not content:
        content = SectionContent.objects.create(section=sec, schema_version=1, blocks_json=request.data)
    else:
        content.blocks_json = request.data
        content.schema_version = 1
        content.save()
    if sec.status == Section.Status.NOT_STARTED:
        sec.status = Section.Status.DRAFT
        sec.save(update_fields=["status"])
    log_action("section", sec.id, "save_new_content", {"blocks": len(request.data.get("blocks", []))})
    return Response({"ok": True})

@api_view(["POST"])
def snapshot(request, section_id):
    sec = get_object_or_404(Section, id=section_id)
    reason = request.data.get("reason")
    content = getattr(sec, "content", None)
    if not content:
        return Response({"error":"no content"}, status=400)
    snap = Snapshot.objects.create(section=sec, reason=reason, blocks_json=content.blocks_json)
    log_action("section", sec.id, "snapshot", {"snapshotId": str(snap.id), "reason": reason})
    return Response(SnapshotSerializer(snap).data, status=201)

@api_view(["GET","POST"])
def comments(request, section_id):
    sec = get_object_or_404(Section, id=section_id)
    if request.method == "GET":
        return Response(CommentSerializer(Comment.objects.filter(section=sec).order_by("-created_at"), many=True).data)
    body = request.data.get("body", "").strip()
    if not body:
        return Response({"error":"body required"}, status=400)
    c = Comment.objects.create(section=sec, body=body)
    log_action("section", sec.id, "comment", {"commentId": str(c.id)})
    return Response(CommentSerializer(c).data, status=201)

@api_view(["POST"])
def ai_section(request):
    section_id = request.data.get("sectionId")
    preset = request.data.get("preset", "modernize")
    inputs = request.data.get("inputs", {})
    options = request.data.get("options", {})
    if not section_id:
        return Response({"error":"sectionId required"}, status=400)
    sec = get_object_or_404(Section, id=section_id)
    provider = get_provider()
    blocks = provider.generate_blocks(preset=preset, inputs=inputs, options=options)
    log_action("ai", sec.id, "ai_generate", {"preset": preset})
    return Response(blocks)

@api_view(["POST"])
def export_document(request, document_id):
    doc = get_object_or_404(Document, id=document_id)
    template_id = request.data.get("templateId")
    admin_override = request.data.get("adminOverride", False)
    template = None
    if template_id:
        template = get_object_or_404(Template, id=template_id)
    
    # Check preflight status to determine if admin override is needed
    sections = Section.objects.filter(document=doc)
    status_counts = {
        "not_started": 0,
        "draft": 0,
        "in_review": 0,
        "verified": 0,
        "total": 0
    }
    for s in sections:
        status_counts["total"] += 1
        status_counts[s.status] += 1
    all_verified = status_counts["verified"] == status_counts["total"]
    
    job = ExportJob.objects.create(document=doc, template=template)
    
    # Log export request
    log_payload = {"exportJobId": str(job.id)}
    if admin_override and not all_verified:
        log_payload["adminOverride"] = True
        log_payload["reason"] = "Exporting with unverified sections"
        log_action("document", doc.id, "export_admin_override", log_payload)
    else:
        log_action("document", doc.id, "export_requested", log_payload)
    
    export_docx.delay(str(job.id))
    return Response(ExportJobSerializer(job).data, status=201)

@api_view(["GET"])
def export_detail(request, export_id):
    job = get_object_or_404(ExportJob, id=export_id)
    return Response(ExportJobSerializer(job).data)

@api_view(["GET"])
def document_audit(request, document_id):
    doc = get_object_or_404(Document, id=document_id)
    logs = AuditLog.objects.filter(entity_id=doc.id).order_by("-created_at")[:200]
    return Response(AuditLogSerializer(logs, many=True).data)


@api_view(["GET"])
def project_documents(request, project_id):
    """List all documents for a project."""
    project = get_object_or_404(Project, id=project_id)
    docs = Document.objects.filter(project=project).order_by("-created_at")
    return Response(DocumentSerializer(docs, many=True).data)


@api_view(["GET", "POST"])
def templates(request):
    """List or create templates."""
    if request.method == "GET":
        return Response(TemplateSerializer(Template.objects.all().order_by("-created_at"), many=True).data)
    
    # POST - create template
    name = request.data.get("name", "Custom Template")
    mapping_json = request.data.get("mapping_json", DEFAULT_MAPPING)
    
    template = Template.objects.create(name=name, mapping_json=mapping_json)
    log_action("template", template.id, "create_template", {"name": name})
    return Response(TemplateSerializer(template).data, status=201)


@api_view(["GET"])
def template_detail(request, template_id):
    """Get template details."""
    template = get_object_or_404(Template, id=template_id)
    return Response(TemplateSerializer(template).data)


@api_view(["GET"])
def export_preflight(request, document_id):
    """
    Preflight check before export.
    Returns section status counts and warnings.
    """
    doc = get_object_or_404(Document, id=document_id)
    sections = Section.objects.filter(document=doc)
    
    # Count sections by status
    status_counts = {
        "not_started": 0,
        "draft": 0,
        "in_review": 0,
        "verified": 0,
        "total": 0
    }
    
    for s in sections:
        status_counts["total"] += 1
        status_counts[s.status] += 1
    
    # Generate warnings
    warnings = []
    if status_counts["not_started"] > 0:
        warnings.append(f"{status_counts['not_started']} section(s) have not been started")
    if status_counts["draft"] > 0:
        warnings.append(f"{status_counts['draft']} section(s) are still in draft")
    if status_counts["in_review"] > 0:
        warnings.append(f"{status_counts['in_review']} section(s) are pending review")
    
    all_verified = status_counts["verified"] == status_counts["total"]
    
    return Response({
        "documentId": str(doc.id),
        "title": doc.title,
        "statusCounts": status_counts,
        "allVerified": all_verified,
        "warnings": warnings,
        "canExport": True,  # v1: allow export even if not all verified
    })


@api_view(["GET"])
def section_snapshots(request, section_id):
    """List all snapshots for a section."""
    section = get_object_or_404(Section, id=section_id)
    snapshots = Snapshot.objects.filter(section=section).order_by("-saved_at")
    return Response(SnapshotSerializer(snapshots, many=True).data)


@api_view(["POST"])
def restore_snapshot(request, section_id, snapshot_id):
    """Restore a section to a previous snapshot."""
    section = get_object_or_404(Section, id=section_id)
    snapshot = get_object_or_404(Snapshot, id=snapshot_id, section=section)
    
    if section.locked:
        return Response({"error": "Section is locked. Reopen with reason to restore."}, status=400)
    
    # Save current state as a snapshot before restoring
    content = getattr(section, "content", None)
    if content:
        Snapshot.objects.create(
            section=section,
            reason="Auto-saved before restore",
            blocks_json=content.blocks_json
        )
        # Restore snapshot content
        content.blocks_json = snapshot.blocks_json
        content.save()
    
    log_action("section", section.id, "restore_snapshot", {
        "snapshotId": str(snapshot.id),
        "snapshotReason": snapshot.reason
    })
    
    return Response({"ok": True, "restored": SnapshotSerializer(snapshot).data})
