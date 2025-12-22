"""
Unit tests for core models.
"""
import uuid
from django.test import TestCase
from core.models import (
    Project, Document, Section, SectionContent, 
    Comment, Snapshot, AuditLog, ExportJob, Template
)


class ProjectModelTest(TestCase):
    def test_create_project(self):
        project = Project.objects.create(
            name="Test Project",
            description="Test description"
        )
        self.assertIsInstance(project.id, uuid.UUID)
        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.description, "Test description")
        self.assertIsNotNone(project.created_at)

    def test_project_str(self):
        project = Project.objects.create(name="Test Project")
        self.assertIn("Test Project", str(project.name))


class DocumentModelTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")

    def test_create_document(self):
        doc = Document.objects.create(
            project=self.project,
            title="Test Document",
        )
        self.assertIsInstance(doc.id, uuid.UUID)
        self.assertEqual(doc.title, "Test Document")
        self.assertEqual(doc.parse_status, Document.ParseStatus.PENDING)

    def test_parse_status_choices(self):
        self.assertIn("pending", Document.ParseStatus.values)
        self.assertIn("running", Document.ParseStatus.values)
        self.assertIn("done", Document.ParseStatus.values)
        self.assertIn("failed", Document.ParseStatus.values)


class SectionModelTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.document = Document.objects.create(
            project=self.project,
            title="Test Document"
        )

    def test_create_section(self):
        section = Section.objects.create(
            document=self.document,
            heading="Introduction",
            depth=1,
            order_index=0
        )
        self.assertIsInstance(section.id, uuid.UUID)
        self.assertEqual(section.heading, "Introduction")
        self.assertEqual(section.status, Section.Status.NOT_STARTED)
        self.assertFalse(section.locked)

    def test_section_hierarchy(self):
        parent = Section.objects.create(
            document=self.document,
            heading="Chapter 1",
            depth=1,
            order_index=0
        )
        child = Section.objects.create(
            document=self.document,
            parent=parent,
            heading="Section 1.1",
            depth=2,
            order_index=1
        )
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())

    def test_status_choices(self):
        self.assertIn("not_started", Section.Status.values)
        self.assertIn("draft", Section.Status.values)
        self.assertIn("in_review", Section.Status.values)
        self.assertIn("verified", Section.Status.values)

    def test_section_locking(self):
        section = Section.objects.create(
            document=self.document,
            heading="Test",
            depth=1
        )
        section.status = Section.Status.VERIFIED
        section.locked = True
        section.save()
        
        section.refresh_from_db()
        self.assertTrue(section.locked)
        self.assertEqual(section.status, Section.Status.VERIFIED)


class SectionContentModelTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.document = Document.objects.create(
            project=self.project,
            title="Test Document"
        )
        self.section = Section.objects.create(
            document=self.document,
            heading="Test Section",
            depth=1
        )

    def test_create_section_content(self):
        content = SectionContent.objects.create(
            section=self.section,
            schema_version=1,
            blocks_json={"version": 1, "blocks": []}
        )
        self.assertEqual(content.section, self.section)
        self.assertEqual(content.schema_version, 1)

    def test_blocks_json_structure(self):
        blocks = {
            "version": 1,
            "blocks": [
                {"id": "1", "type": "paragraph", "text": "Hello"}
            ]
        }
        content = SectionContent.objects.create(
            section=self.section,
            blocks_json=blocks
        )
        self.assertEqual(len(content.blocks_json["blocks"]), 1)
        self.assertEqual(content.blocks_json["blocks"][0]["type"], "paragraph")


class CommentModelTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.document = Document.objects.create(
            project=self.project,
            title="Test Document"
        )
        self.section = Section.objects.create(
            document=self.document,
            heading="Test Section",
            depth=1
        )

    def test_create_comment(self):
        comment = Comment.objects.create(
            section=self.section,
            body="This is a comment"
        )
        self.assertIsInstance(comment.id, uuid.UUID)
        self.assertEqual(comment.body, "This is a comment")
        self.assertEqual(comment.status, Comment.Status.OPEN)


class SnapshotModelTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.document = Document.objects.create(
            project=self.project,
            title="Test Document"
        )
        self.section = Section.objects.create(
            document=self.document,
            heading="Test Section",
            depth=1
        )

    def test_create_snapshot(self):
        snapshot = Snapshot.objects.create(
            section=self.section,
            reason="Before major edit",
            blocks_json={"version": 1, "blocks": []}
        )
        self.assertIsInstance(snapshot.id, uuid.UUID)
        self.assertEqual(snapshot.reason, "Before major edit")
        self.assertIsNotNone(snapshot.saved_at)


class TemplateModelTest(TestCase):
    def test_create_template(self):
        template = Template.objects.create(
            name="Standard Academic",
            mapping_json={
                "styles": {"heading1": "Heading 1"}
            }
        )
        self.assertIsInstance(template.id, uuid.UUID)
        self.assertEqual(template.name, "Standard Academic")
        self.assertIn("styles", template.mapping_json)


class ExportJobModelTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.document = Document.objects.create(
            project=self.project,
            title="Test Document"
        )

    def test_create_export_job(self):
        job = ExportJob.objects.create(
            document=self.document
        )
        self.assertIsInstance(job.id, uuid.UUID)
        self.assertEqual(job.status, ExportJob.Status.PENDING)
        self.assertIsNone(job.template)


class AuditLogModelTest(TestCase):
    def test_create_audit_log(self):
        log = AuditLog.objects.create(
            entity_type="document",
            entity_id=uuid.uuid4(),
            action="upload_document",
            payload={"title": "Test"}
        )
        self.assertIsInstance(log.id, uuid.UUID)
        self.assertEqual(log.action, "upload_document")
        self.assertIsNotNone(log.created_at)

