import re
from .models import AuditLog, Section

def normalize_text(s: str) -> str:
    s = s or ""
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def log_action(entity_type: str, entity_id, action: str, payload: dict):
    AuditLog.objects.create(entity_type=entity_type, entity_id=entity_id, action=action, payload=payload)

def enforce_lock(section: Section):
    if section.locked:
        raise ValueError("Section is locked (verified). Reopen with reason to edit.")
