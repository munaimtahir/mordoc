"""
Unit tests for block schema validation.
"""
from django.test import TestCase
from core.block_schema import validate_blocks


class BlockSchemaValidationTest(TestCase):
    """Test the block schema validation logic."""

    def test_valid_empty_blocks(self):
        payload = {"version": 1, "blocks": []}
        valid, msg = validate_blocks(payload)
        self.assertTrue(valid)
        self.assertEqual(msg, "ok")

    def test_invalid_version(self):
        payload = {"version": 2, "blocks": []}
        valid, msg = validate_blocks(payload)
        self.assertFalse(valid)
        self.assertIn("version", msg.lower())

    def test_missing_version(self):
        payload = {"blocks": []}
        valid, msg = validate_blocks(payload)
        self.assertFalse(valid)

    def test_missing_blocks(self):
        payload = {"version": 1}
        valid, msg = validate_blocks(payload)
        self.assertFalse(valid)
        self.assertIn("blocks", msg.lower())

    def test_valid_heading_block(self):
        payload = {
            "version": 1,
            "blocks": [
                {"id": "h1", "type": "heading", "level": 1, "text": "Introduction"}
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertTrue(valid)

    def test_heading_invalid_level(self):
        payload = {
            "version": 1,
            "blocks": [
                {"id": "h1", "type": "heading", "level": 7, "text": "Test"}
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertFalse(valid)
        self.assertIn("level", msg.lower())

    def test_heading_level_zero(self):
        payload = {
            "version": 1,
            "blocks": [
                {"id": "h1", "type": "heading", "level": 0, "text": "Test"}
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertFalse(valid)

    def test_valid_paragraph_block(self):
        payload = {
            "version": 1,
            "blocks": [
                {"id": "p1", "type": "paragraph", "text": "This is a paragraph."}
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertTrue(valid)

    def test_valid_paragraph_with_marks(self):
        payload = {
            "version": 1,
            "blocks": [
                {
                    "id": "p1",
                    "type": "paragraph",
                    "text": "This is bold text.",
                    "marks": [
                        {"type": "bold", "range": [8, 12]}
                    ]
                }
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertTrue(valid)

    def test_invalid_mark_type(self):
        payload = {
            "version": 1,
            "blocks": [
                {
                    "id": "p1",
                    "type": "paragraph",
                    "text": "Test",
                    "marks": [
                        {"type": "underline", "range": [0, 4]}
                    ]
                }
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertFalse(valid)
        self.assertIn("mark", msg.lower())

    def test_invalid_mark_range(self):
        payload = {
            "version": 1,
            "blocks": [
                {
                    "id": "p1",
                    "type": "paragraph",
                    "text": "Test",
                    "marks": [
                        {"type": "bold", "range": [0]}  # Invalid range
                    ]
                }
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertFalse(valid)

    def test_link_mark_requires_href(self):
        payload = {
            "version": 1,
            "blocks": [
                {
                    "id": "p1",
                    "type": "paragraph",
                    "text": "Click here",
                    "marks": [
                        {"type": "link", "range": [6, 10]}  # Missing href
                    ]
                }
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertFalse(valid)
        self.assertIn("href", msg.lower())

    def test_valid_link_mark(self):
        payload = {
            "version": 1,
            "blocks": [
                {
                    "id": "p1",
                    "type": "paragraph",
                    "text": "Click here",
                    "marks": [
                        {"type": "link", "range": [6, 10], "href": "https://example.com"}
                    ]
                }
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertTrue(valid)

    def test_valid_bulleted_list(self):
        payload = {
            "version": 1,
            "blocks": [
                {
                    "id": "list1",
                    "type": "list",
                    "style": "bulleted",
                    "items": ["Item 1", "Item 2", "Item 3"]
                }
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertTrue(valid)

    def test_valid_numbered_list(self):
        payload = {
            "version": 1,
            "blocks": [
                {
                    "id": "list1",
                    "type": "list",
                    "style": "numbered",
                    "items": ["First", "Second"]
                }
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertTrue(valid)

    def test_invalid_list_style(self):
        payload = {
            "version": 1,
            "blocks": [
                {
                    "id": "list1",
                    "type": "list",
                    "style": "dashed",  # Invalid
                    "items": ["Item"]
                }
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertFalse(valid)

    def test_list_items_must_be_strings(self):
        payload = {
            "version": 1,
            "blocks": [
                {
                    "id": "list1",
                    "type": "list",
                    "style": "bulleted",
                    "items": ["Valid", 123]  # Invalid item
                }
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertFalse(valid)

    def test_valid_image_block(self):
        payload = {
            "version": 1,
            "blocks": [
                {
                    "id": "img1",
                    "type": "image",
                    "assetId": "asset-123",
                    "caption": "A sample image"
                }
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertTrue(valid)

    def test_image_requires_asset_id(self):
        payload = {
            "version": 1,
            "blocks": [
                {
                    "id": "img1",
                    "type": "image",
                    "caption": "No asset"
                }
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertFalse(valid)
        self.assertIn("assetId", msg)

    def test_unsupported_block_type(self):
        payload = {
            "version": 1,
            "blocks": [
                {"id": "t1", "type": "table", "rows": []}
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertFalse(valid)
        self.assertIn("type", msg.lower())

    def test_duplicate_block_ids(self):
        payload = {
            "version": 1,
            "blocks": [
                {"id": "same", "type": "paragraph", "text": "First"},
                {"id": "same", "type": "paragraph", "text": "Second"}
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertFalse(valid)
        self.assertIn("unique", msg.lower())

    def test_missing_block_id(self):
        payload = {
            "version": 1,
            "blocks": [
                {"type": "paragraph", "text": "No ID"}
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertFalse(valid)
        self.assertIn("id", msg.lower())

    def test_empty_block_id(self):
        payload = {
            "version": 1,
            "blocks": [
                {"id": "", "type": "paragraph", "text": "Empty ID"}
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertFalse(valid)

    def test_multiple_valid_blocks(self):
        payload = {
            "version": 1,
            "blocks": [
                {"id": "h1", "type": "heading", "level": 1, "text": "Title"},
                {"id": "p1", "type": "paragraph", "text": "Introduction text."},
                {"id": "list1", "type": "list", "style": "bulleted", "items": ["A", "B"]},
                {"id": "img1", "type": "image", "assetId": "img-001"}
            ]
        }
        valid, msg = validate_blocks(payload)
        self.assertTrue(valid)
        self.assertEqual(msg, "ok")

    def test_payload_must_be_dict(self):
        valid, msg = validate_blocks([])
        self.assertFalse(valid)
        valid, msg = validate_blocks("string")
        self.assertFalse(valid)
        valid, msg = validate_blocks(None)
        self.assertFalse(valid)

