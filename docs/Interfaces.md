# Interfaces.md — v1

## Canonical block schema (v1)
See `docs/BlockSchema.md`

## Template mapping interface
- A template defines DOCX styles and mappings:
  - Heading levels → DOCX style names
  - Paragraph → DOCX style
  - List bullets/numbered → list style
  - Header/footer assets + page numbering

**Template strictness: must-match-exact** (as per Goals.md requirement — must-match official template)

v1 supports selecting from 1–2 predefined templates. Each template must exactly match the official template's style definitions.
