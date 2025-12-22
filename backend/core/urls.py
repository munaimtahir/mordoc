from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health),
    path("projects", views.projects),
    path("projects/<uuid:project_id>/documents", views.upload_document),
    path("documents/<uuid:document_id>", views.document_detail),
    path("documents/<uuid:document_id>/sections", views.document_sections),
    path("documents/<uuid:document_id>/audit", views.document_audit),

    path("sections/<uuid:section_id>", views.section_patch),
    path("sections/merge", views.merge_sections),
    path("sections/<uuid:section_id>/old", views.section_old),
    path("sections/<uuid:section_id>/new", views.section_new),
    path("sections/<uuid:section_id>/snapshot", views.snapshot),
    path("sections/<uuid:section_id>/comments", views.comments),

    path("ai/section", views.ai_section),

    path("documents/<uuid:document_id>/export", views.export_document),
    path("exports/<uuid:export_id>", views.export_detail),
]
