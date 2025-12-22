import uuid
from django.db import models

class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

class Template(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    # Minimal v1: JSON style mapping info
    mapping_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

class Document(models.Model):
    class ParseStatus(models.TextChoices):
        PENDING = "pending"
        RUNNING = "running"
        DONE = "done"
        FAILED = "failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=255)
    source_file = models.FileField(upload_to="uploads/")
    parse_status = models.CharField(max_length=16, choices=ParseStatus.choices, default=ParseStatus.PENDING)
    template = models.ForeignKey(Template, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Section(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started"
        DRAFT = "draft"
        IN_REVIEW = "in_review"
        VERIFIED = "verified"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="sections")
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children")
    order_index = models.IntegerField(default=0)
    heading = models.CharField(max_length=500, blank=True, default="")
    depth = models.IntegerField(default=0)
    old_content_raw = models.TextField(blank=True, default="")
    old_content_normalized = models.TextField(blank=True, default="")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NOT_STARTED)
    locked = models.BooleanField(default=False)
    reopen_reason = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

class SectionContent(models.Model):
    section = models.OneToOneField(Section, on_delete=models.CASCADE, related_name="content")
    schema_version = models.IntegerField(default=1)
    blocks_json = models.JSONField(default=dict)

class Comment(models.Model):
    class Status(models.TextChoices):
        OPEN = "open"
        RESOLVED = "resolved"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

class Snapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="snapshots")
    reason = models.TextField(blank=True, null=True)
    blocks_json = models.JSONField(default=dict)
    saved_at = models.DateTimeField(auto_now_add=True)

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_type = models.CharField(max_length=64)
    entity_id = models.UUIDField()
    action = models.CharField(max_length=128)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

class ExportJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        RUNNING = "running"
        DONE = "done"
        FAILED = "failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="exports")
    template = models.ForeignKey(Template, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    output_file = models.FileField(upload_to="exports/", null=True, blank=True)
    error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
