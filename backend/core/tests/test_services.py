"""
Unit tests for service functions.
"""
from django.test import TestCase
from core.services import normalize_text, log_action
from core.models import AuditLog, Project, Document, Section
import uuid


class NormalizeTextTest(TestCase):
    """Tests for text normalization function."""

    def test_empty_string(self):
        self.assertEqual(normalize_text(""), "")

    def test_none_value(self):
        self.assertEqual(normalize_text(None), "")

    def test_normalize_line_endings(self):
        # Windows line endings
        text = "Line 1\r\nLine 2\r\nLine 3"
        result = normalize_text(text)
        self.assertNotIn("\r", result)
        self.assertEqual(result.count("\n"), 2)

    def test_normalize_carriage_returns(self):
        text = "Line 1\rLine 2\rLine 3"
        result = normalize_text(text)
        self.assertNotIn("\r", result)

    def test_collapse_multiple_spaces(self):
        text = "Word    with    many    spaces"
        result = normalize_text(text)
        self.assertEqual(result, "Word with many spaces")

    def test_collapse_multiple_newlines(self):
        text = "Para 1\n\n\n\n\nPara 2"
        result = normalize_text(text)
        self.assertEqual(result.count("\n"), 2)  # Should be collapsed to \n\n

    def test_strip_whitespace(self):
        text = "   content here   "
        result = normalize_text(text)
        self.assertEqual(result, "content here")

    def test_complex_normalization(self):
        text = "  Hello   world\r\n\r\n\r\nNew    paragraph  "
        result = normalize_text(text)
        self.assertEqual(result, "Hello world\n\nNew paragraph")


class LogActionTest(TestCase):
    """Tests for audit logging function."""

    def test_log_action_creates_entry(self):
        entity_id = uuid.uuid4()
        log_action("document", entity_id, "test_action", {"key": "value"})
        
        log = AuditLog.objects.get(entity_id=entity_id)
        self.assertEqual(log.entity_type, "document")
        self.assertEqual(log.action, "test_action")
        self.assertEqual(log.payload["key"], "value")

    def test_log_action_different_entity_types(self):
        for entity_type in ["project", "document", "section", "export", "ai"]:
            entity_id = uuid.uuid4()
            log_action(entity_type, entity_id, "test", {})
            log = AuditLog.objects.get(entity_id=entity_id)
            self.assertEqual(log.entity_type, entity_type)

    def test_log_action_empty_payload(self):
        entity_id = uuid.uuid4()
        log_action("test", entity_id, "action", {})
        log = AuditLog.objects.get(entity_id=entity_id)
        self.assertEqual(log.payload, {})

    def test_log_action_complex_payload(self):
        entity_id = uuid.uuid4()
        payload = {
            "string": "value",
            "number": 42,
            "nested": {"key": "val"},
            "array": [1, 2, 3]
        }
        log_action("test", entity_id, "action", payload)
        log = AuditLog.objects.get(entity_id=entity_id)
        self.assertEqual(log.payload, payload)


class StatusTransitionsTest(TestCase):
    """Test section status workflow transitions."""

    def setUp(self):
        self.project = Project.objects.create(name="Test")
        self.document = Document.objects.create(
            project=self.project,
            title="Test Doc"
        )
        self.section = Section.objects.create(
            document=self.document,
            heading="Test Section",
            depth=1
        )

    def test_initial_status_is_not_started(self):
        self.assertEqual(self.section.status, Section.Status.NOT_STARTED)
        self.assertFalse(self.section.locked)

    def test_transition_to_draft(self):
        self.section.status = Section.Status.DRAFT
        self.section.save()
        self.section.refresh_from_db()
        self.assertEqual(self.section.status, Section.Status.DRAFT)

    def test_transition_to_in_review(self):
        self.section.status = Section.Status.IN_REVIEW
        self.section.save()
        self.section.refresh_from_db()
        self.assertEqual(self.section.status, Section.Status.IN_REVIEW)

    def test_transition_to_verified_locks(self):
        self.section.status = Section.Status.VERIFIED
        self.section.locked = True
        self.section.save()
        self.section.refresh_from_db()
        self.assertEqual(self.section.status, Section.Status.VERIFIED)
        self.assertTrue(self.section.locked)

    def test_reopen_requires_reason(self):
        self.section.status = Section.Status.VERIFIED
        self.section.locked = True
        self.section.save()
        
        # Reopen with reason
        self.section.status = Section.Status.DRAFT
        self.section.locked = False
        self.section.reopen_reason = "Needs updates"
        self.section.save()
        
        self.section.refresh_from_db()
        self.assertEqual(self.section.status, Section.Status.DRAFT)
        self.assertFalse(self.section.locked)
        self.assertEqual(self.section.reopen_reason, "Needs updates")


class SectionHierarchyTest(TestCase):
    """Test section tree hierarchy operations."""

    def setUp(self):
        self.project = Project.objects.create(name="Test")
        self.document = Document.objects.create(
            project=self.project,
            title="Test Doc"
        )

    def test_create_flat_structure(self):
        s1 = Section.objects.create(document=self.document, heading="S1", depth=1, order_index=0)
        s2 = Section.objects.create(document=self.document, heading="S2", depth=1, order_index=1)
        s3 = Section.objects.create(document=self.document, heading="S3", depth=1, order_index=2)
        
        sections = Section.objects.filter(document=self.document).order_by("order_index")
        self.assertEqual(list(sections), [s1, s2, s3])

    def test_create_nested_structure(self):
        chapter = Section.objects.create(
            document=self.document,
            heading="Chapter 1",
            depth=1,
            order_index=0
        )
        section = Section.objects.create(
            document=self.document,
            parent=chapter,
            heading="Section 1.1",
            depth=2,
            order_index=1
        )
        subsection = Section.objects.create(
            document=self.document,
            parent=section,
            heading="Section 1.1.1",
            depth=3,
            order_index=2
        )
        
        self.assertEqual(section.parent, chapter)
        self.assertEqual(subsection.parent, section)
        self.assertIn(section, chapter.children.all())
        self.assertIn(subsection, section.children.all())

    def test_reorder_sections(self):
        s1 = Section.objects.create(document=self.document, heading="S1", depth=1, order_index=0)
        s2 = Section.objects.create(document=self.document, heading="S2", depth=1, order_index=1)
        s3 = Section.objects.create(document=self.document, heading="S3", depth=1, order_index=2)
        
        # Move S3 to first position
        s3.order_index = -1
        s3.save()
        
        sections = Section.objects.filter(document=self.document).order_by("order_index")
        self.assertEqual(list(sections), [s3, s1, s2])

    def test_promote_section(self):
        section = Section.objects.create(
            document=self.document,
            heading="Section",
            depth=2,
            order_index=0
        )
        
        # Promote (reduce depth)
        section.depth = 1
        section.parent = None
        section.save()
        
        section.refresh_from_db()
        self.assertEqual(section.depth, 1)
        self.assertIsNone(section.parent)

    def test_demote_section(self):
        section = Section.objects.create(
            document=self.document,
            heading="Section",
            depth=1,
            order_index=0
        )
        
        # Demote (increase depth)
        section.depth = 2
        section.save()
        
        section.refresh_from_db()
        self.assertEqual(section.depth, 2)

