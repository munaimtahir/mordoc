from celery import shared_task
from django.core.files.base import ContentFile
from django.db import transaction
from docx import Document as DocxDocument
import io
from .models import Document, Section, SectionContent, ExportJob
from .services import normalize_text, log_action
from .template_mapping import create_styled_docx, DEFAULT_MAPPING


@shared_task
def parse_docx(document_id: str):
    doc = Document.objects.get(id=document_id)
    doc.parse_status = Document.ParseStatus.RUNNING
    doc.save(update_fields=["parse_status"])

    try:
        d = DocxDocument(doc.source_file.path)
        # Best-effort parse: Heading styles become sections
        # Enhanced: detect parent-child relationships based on heading levels
        section_stack = []  # Stack to track parent sections by depth
        order = 0
        
        with transaction.atomic():
            Section.objects.filter(document=doc).delete()

            for para in d.paragraphs:
                text = (para.text or "").strip()
                if not text:
                    continue
                style = (para.style.name if para.style else "") or ""
                is_heading = style.lower().startswith("heading")
                
                if is_heading:
                    depth = 1
                    # Try to parse heading level
                    try:
                        depth = int(style.split()[-1])
                    except Exception:
                        depth = 1
                    
                    # Determine parent based on depth
                    parent = None
                    while section_stack and section_stack[-1]["depth"] >= depth:
                        section_stack.pop()
                    if section_stack:
                        parent = section_stack[-1]["section"]
                    
                    current_section = Section.objects.create(
                        document=doc,
                        parent=parent,
                        order_index=order,
                        heading=text,
                        depth=depth,
                        old_content_raw="",
                        old_content_normalized="",
                    )
                    SectionContent.objects.create(
                        section=current_section,
                        schema_version=1,
                        blocks_json={"version": 1, "blocks": []}
                    )
                    
                    # Push to stack for potential children
                    section_stack.append({"section": current_section, "depth": depth})
                    order += 1
                else:
                    # Non-heading paragraph - append to current section
                    if not section_stack:
                        # Create a default section for content before first heading
                        default_section = Section.objects.create(
                            document=doc,
                            parent=None,
                            order_index=order,
                            heading="(Untitled)",
                            depth=1,
                            old_content_raw="",
                            old_content_normalized="",
                        )
                        SectionContent.objects.create(
                            section=default_section,
                            schema_version=1,
                            blocks_json={"version": 1, "blocks": []}
                        )
                        section_stack.append({"section": default_section, "depth": 1})
                        order += 1
                    
                    current_section = section_stack[-1]["section"]
                    current_section.old_content_raw += text + "\n\n"
                    current_section.save(update_fields=["old_content_raw"])

            # Normalize all sections
            for s in Section.objects.filter(document=doc):
                s.old_content_normalized = normalize_text(s.old_content_raw)
                s.save(update_fields=["old_content_normalized"])

        doc.parse_status = Document.ParseStatus.DONE
        doc.save(update_fields=["parse_status"])
        log_action("document", doc.id, "parse_done", {
            "sections": Section.objects.filter(document=doc).count()
        })
    except Exception as e:
        doc.parse_status = Document.ParseStatus.FAILED
        doc.save(update_fields=["parse_status"])
        log_action("document", doc.id, "parse_failed", {"error": str(e)})
        raise


@shared_task
def export_docx(export_job_id: str):
    """
    Export document to DOCX using template style mapping.
    
    Uses Template.mapping_json if a template is selected, otherwise uses DEFAULT_MAPPING.
    Implements must-match-exact template styling as per Goals.md requirement.
    """
    job = ExportJob.objects.get(id=export_job_id)
    job.status = ExportJob.Status.RUNNING
    job.save(update_fields=["status"])

    try:
        doc = job.document
        
        # Get template mapping
        mapping = DEFAULT_MAPPING
        if job.template and job.template.mapping_json:
            # Merge template mapping with defaults
            template_mapping = job.template.mapping_json
            mapping = {
                "styles": {**DEFAULT_MAPPING["styles"], **template_mapping.get("styles", {})},
                "fonts": {**DEFAULT_MAPPING["fonts"], **template_mapping.get("fonts", {})},
                "spacing": {**DEFAULT_MAPPING["spacing"], **template_mapping.get("spacing", {})},
                "margins": {**DEFAULT_MAPPING["margins"], **template_mapping.get("margins", {})},
            }
        
        # Collect sections data for export
        sections = Section.objects.filter(document=doc).order_by("order_index")
        sections_data = []
        
        for s in sections:
            blocks_json = {"version": 1, "blocks": []}
            if hasattr(s, "content") and s.content.blocks_json:
                blocks_json = s.content.blocks_json
            
            sections_data.append({
                "heading": s.heading or "Section",
                "depth": s.depth,
                "blocks_json": blocks_json,
            })
        
        # Create styled document using template mapping
        out = create_styled_docx(sections_data, mapping)
        
        # Save to file
        bio = io.BytesIO()
        out.save(bio)
        bio.seek(0)
        filename = f"export_{doc.id}.docx"
        job.output_file.save(filename, ContentFile(bio.read()), save=True)
        job.status = ExportJob.Status.DONE
        job.save(update_fields=["status", "output_file"])
        log_action("export", job.id, "export_done", {
            "file": job.output_file.name,
            "template": str(job.template_id) if job.template_id else None,
            "sections_count": len(sections_data)
        })
    except Exception as e:
        job.status = ExportJob.Status.FAILED
        job.error = str(e)
        job.save(update_fields=["status", "error"])
        log_action("export", job.id, "export_failed", {"error": str(e)})
        raise
