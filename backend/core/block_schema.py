from typing import Any, Dict, List, Tuple

ALLOWED_BLOCK_TYPES = {"heading", "paragraph", "list", "image"}
ALLOWED_MARK_TYPES = {"bold", "italic", "link"}
ALLOWED_LIST_STYLES = {"bulleted", "numbered"}

def validate_blocks(payload: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(payload, dict):
        return False, "Payload must be an object"
    if payload.get("version") != 1:
        return False, "Unsupported schema version"
    blocks = payload.get("blocks")
    if not isinstance(blocks, list):
        return False, "blocks must be a list"
    ids = set()
    for b in blocks:
        if not isinstance(b, dict):
            return False, "block must be an object"
        bid = b.get("id")
        if not isinstance(bid, str) or not bid:
            return False, "block.id required"
        if bid in ids:
            return False, "block.id must be unique"
        ids.add(bid)
        btype = b.get("type")
        if btype not in ALLOWED_BLOCK_TYPES:
            return False, f"Unsupported block type: {btype}"
        if btype in ("heading", "paragraph"):
            if not isinstance(b.get("text", ""), str):
                return False, "text must be string"
            marks = b.get("marks", [])
            if marks is None:
                marks = []
            if not isinstance(marks, list):
                return False, "marks must be list"
            for m in marks:
                if not isinstance(m, dict):
                    return False, "mark must be object"
                if m.get("type") not in ALLOWED_MARK_TYPES:
                    return False, "unsupported mark type"
                rng = m.get("range")
                if not (isinstance(rng, list) and len(rng) == 2 and all(isinstance(x, int) for x in rng)):
                    return False, "mark.range must be [start,end] ints"
                if m.get("type") == "link":
                    if not isinstance(m.get("href", ""), str) or not m.get("href"):
                        return False, "link mark requires href"
        if btype == "heading":
            lvl = b.get("level")
            if not isinstance(lvl, int) or not (1 <= lvl <= 6):
                return False, "heading.level must be 1..6"
        if btype == "list":
            if b.get("style") not in ALLOWED_LIST_STYLES:
                return False, "list.style must be bulleted|numbered"
            items = b.get("items")
            if not (isinstance(items, list) and all(isinstance(i, str) for i in items)):
                return False, "list.items must be list of strings"
        if btype == "image":
            if not isinstance(b.get("assetId", ""), str) or not b.get("assetId"):
                return False, "image.assetId required"
            if "caption" in b and b["caption"] is not None and not isinstance(b["caption"], str):
                return False, "image.caption must be string"
    return True, "ok"
