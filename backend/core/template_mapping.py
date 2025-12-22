"""
Template Mapping Module - v1

Implements must-match-exact template style mapping for DOCX export.
Maps canonical block schema to DOCX styles as defined in Template.mapping_json.

Template mapping_json schema:
{
    "styles": {
        "heading1": "Heading 1",
        "heading2": "Heading 2",
        "heading3": "Heading 3",
        "heading4": "Heading 4",
        "heading5": "Heading 5",
        "heading6": "Heading 6",
        "paragraph": "Normal",
        "listBullet": "List Bullet",
        "listNumber": "List Number"
    },
    "fonts": {
        "heading": {"name": "Arial", "size": 14, "bold": true},
        "body": {"name": "Times New Roman", "size": 12, "bold": false}
    },
    "spacing": {
        "beforeHeading": 12,
        "afterHeading": 6,
        "beforeParagraph": 0,
        "afterParagraph": 6,
        "lineSpacing": 1.15
    },
    "margins": {
        "top": 1440,
        "bottom": 1440,
        "left": 1440,
        "right": 1440
    }
}
"""

from typing import Dict, Any, Optional
from docx import Document as DocxDocument
from docx.shared import Pt, Inches, Twips
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# Default template mapping for v1
DEFAULT_MAPPING = {
    "styles": {
        "heading1": "Heading 1",
        "heading2": "Heading 2",
        "heading3": "Heading 3",
        "heading4": "Heading 4",
        "heading5": "Heading 5",
        "heading6": "Heading 6",
        "paragraph": "Normal",
        "listBullet": "List Bullet",
        "listNumber": "List Number"
    },
    "fonts": {
        "heading": {"name": "Arial", "size": 14, "bold": True},
        "body": {"name": "Times New Roman", "size": 12, "bold": False}
    },
    "spacing": {
        "beforeHeading": 12,
        "afterHeading": 6,
        "beforeParagraph": 0,
        "afterParagraph": 6,
        "lineSpacing": 1.15
    },
    "margins": {
        "top": 1440,      # in twips (1 inch)
        "bottom": 1440,
        "left": 1440,
        "right": 1440
    }
}


def get_style_name(mapping: Dict[str, Any], block_type: str, level: int = 1) -> str:
    """Get DOCX style name from mapping for a given block type and level."""
    styles = mapping.get("styles", DEFAULT_MAPPING["styles"])
    
    if block_type == "heading":
        key = f"heading{min(max(level, 1), 6)}"
        return styles.get(key, f"Heading {level}")
    elif block_type == "paragraph":
        return styles.get("paragraph", "Normal")
    elif block_type == "list":
        return styles.get("listBullet", "List Bullet")  # default to bullet
    
    return "Normal"


def get_list_style_name(mapping: Dict[str, Any], list_style: str) -> str:
    """Get DOCX list style name based on list style (bulleted/numbered)."""
    styles = mapping.get("styles", DEFAULT_MAPPING["styles"])
    
    if list_style == "numbered":
        return styles.get("listNumber", "List Number")
    return styles.get("listBullet", "List Bullet")


def apply_inline_marks(paragraph, text: str, marks: list) -> None:
    """Apply inline marks (bold, italic, link) to a paragraph."""
    if not marks:
        paragraph.add_run(text)
        return
    
    # Sort marks by start position
    sorted_marks = sorted(marks, key=lambda m: m.get("range", [0, 0])[0])
    
    current_pos = 0
    for mark in sorted_marks:
        mark_type = mark.get("type")
        rng = mark.get("range", [0, 0])
        start, end = rng[0], rng[1]
        
        # Add text before mark
        if start > current_pos:
            paragraph.add_run(text[current_pos:start])
        
        # Add marked text
        marked_text = text[start:end]
        run = paragraph.add_run(marked_text)
        
        if mark_type == "bold":
            run.bold = True
        elif mark_type == "italic":
            run.italic = True
        elif mark_type == "link":
            run.underline = True
            # Note: python-docx doesn't have native hyperlink support easily
            # For v1, we style it as underlined text
            # Full hyperlink implementation would require XML manipulation
        
        current_pos = end
    
    # Add remaining text after last mark
    if current_pos < len(text):
        paragraph.add_run(text[current_pos:])


def apply_margins(doc: DocxDocument, mapping: Dict[str, Any]) -> None:
    """Apply document margins from template mapping."""
    margins = mapping.get("margins", DEFAULT_MAPPING["margins"])
    
    for section in doc.sections:
        section.top_margin = Twips(margins.get("top", 1440))
        section.bottom_margin = Twips(margins.get("bottom", 1440))
        section.left_margin = Twips(margins.get("left", 1440))
        section.right_margin = Twips(margins.get("right", 1440))


def create_heading(doc: DocxDocument, text: str, level: int, mapping: Dict[str, Any], marks: list = None) -> None:
    """Create a heading with template style mapping."""
    style_name = get_style_name(mapping, "heading", level)
    
    # Try to use the mapped style, fall back to generic heading
    try:
        para = doc.add_heading(text, level=min(max(level, 1), 4))
    except Exception:
        para = doc.add_paragraph(text)
    
    # Apply inline marks if present
    if marks:
        para.clear()
        apply_inline_marks(para, text, marks)


def create_paragraph(doc: DocxDocument, text: str, mapping: Dict[str, Any], marks: list = None) -> None:
    """Create a paragraph with template style mapping."""
    style_name = get_style_name(mapping, "paragraph")
    
    try:
        para = doc.add_paragraph(style=style_name)
    except Exception:
        para = doc.add_paragraph()
    
    apply_inline_marks(para, text, marks or [])


def create_list_item(doc: DocxDocument, item: str, list_style: str, mapping: Dict[str, Any]) -> None:
    """Create a list item with template style mapping."""
    style_name = get_list_style_name(mapping, list_style)
    
    try:
        doc.add_paragraph(item, style=style_name)
    except Exception:
        # Fallback if style doesn't exist
        para = doc.add_paragraph(item)
        if list_style == "numbered":
            # Basic numbering indicator for fallback
            pass


def create_image_placeholder(doc: DocxDocument, asset_id: str, caption: str = None) -> None:
    """Create an image placeholder (v1: images not fully implemented)."""
    text = f"[Image: {asset_id}]"
    if caption:
        text += f" {caption}"
    doc.add_paragraph(text)


def export_blocks_to_docx(doc: DocxDocument, blocks_json: Dict[str, Any], mapping: Dict[str, Any]) -> None:
    """Export blocks JSON to DOCX using template mapping."""
    blocks = blocks_json.get("blocks", [])
    
    for block in blocks:
        block_type = block.get("type")
        
        if block_type == "heading":
            create_heading(
                doc,
                block.get("text", ""),
                block.get("level", 1),
                mapping,
                block.get("marks", [])
            )
        elif block_type == "paragraph":
            create_paragraph(
                doc,
                block.get("text", ""),
                mapping,
                block.get("marks", [])
            )
        elif block_type == "list":
            list_style = block.get("style", "bulleted")
            for item in block.get("items", []):
                create_list_item(doc, item, list_style, mapping)
        elif block_type == "image":
            create_image_placeholder(
                doc,
                block.get("assetId", "unknown"),
                block.get("caption")
            )


def create_styled_docx(sections_data: list, mapping: Dict[str, Any] = None) -> DocxDocument:
    """
    Create a styled DOCX document from sections data.
    
    Args:
        sections_data: List of section dictionaries with heading, depth, and content
        mapping: Template mapping JSON (uses DEFAULT_MAPPING if not provided)
    
    Returns:
        DocxDocument ready to be saved
    """
    if mapping is None:
        mapping = DEFAULT_MAPPING
    
    doc = DocxDocument()
    
    # Apply document-level margins
    apply_margins(doc, mapping)
    
    for section in sections_data:
        heading = section.get("heading", "Section")
        depth = section.get("depth", 1)
        blocks_json = section.get("blocks_json", {"version": 1, "blocks": []})
        
        # Add section heading
        create_heading(doc, heading, depth, mapping)
        
        # Export blocks
        if blocks_json and blocks_json.get("blocks"):
            export_blocks_to_docx(doc, blocks_json, mapping)
        else:
            # If no blocks, add empty paragraph
            doc.add_paragraph("")
    
    return doc

