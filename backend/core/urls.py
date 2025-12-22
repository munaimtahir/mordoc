from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health),
    
    # Projects
    path("projects", views.projects),
    path("projects/<uuid:project_id>/documents", views.upload_document),
    path("projects/<uuid:project_id>/documents/list", views.project_documents),
    
    # Documents
    path("documents/<uuid:document_id>", views.document_detail),
    path("documents/<uuid:document_id>/sections", views.document_sections),
    path("documents/<uuid:document_id>/audit", views.document_audit),
    path("documents/<uuid:document_id>/export", views.export_document),
    path("documents/<uuid:document_id>/export/preflight", views.export_preflight),

    # Sections
    path("sections/<uuid:section_id>", views.section_patch),
    path("sections/merge", views.merge_sections),
    path("sections/<uuid:section_id>/old", views.section_old),
    path("sections/<uuid:section_id>/new", views.section_new),
    path("sections/<uuid:section_id>/snapshot", views.snapshot),
    path("sections/<uuid:section_id>/snapshots", views.section_snapshots),
    path("sections/<uuid:section_id>/snapshots/<uuid:snapshot_id>/restore", views.restore_snapshot),
    path("sections/<uuid:section_id>/comments", views.comments),

    # AI
    path("ai/section", views.ai_section),

    # Templates
    path("templates", views.templates),
    path("templates/<uuid:template_id>", views.template_detail),

    # Exports
    path("exports/<uuid:export_id>", views.export_detail),
]
