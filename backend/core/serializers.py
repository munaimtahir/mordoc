from rest_framework import serializers
from .models import Project, Document, Section, SectionContent, Comment, Snapshot, AuditLog, ExportJob, Template

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "description", "created_at"]

class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = ["id", "name", "mapping_json", "created_at"]

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "project", "title", "source_file", "parse_status", "template", "created_at"]

class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ["id", "document", "parent", "order_index", "heading", "depth",
                  "old_content_raw", "status", "locked", "reopen_reason", "updated_at"]

class SectionContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SectionContent
        fields = ["section", "schema_version", "blocks_json"]

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "section", "body", "status", "created_at"]

class SnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snapshot
        fields = ["id", "section", "reason", "blocks_json", "saved_at"]

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ["id", "entity_type", "entity_id", "action", "payload", "created_at"]

class ExportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExportJob
        fields = ["id", "document", "template", "status", "output_file", "error", "created_at"]
