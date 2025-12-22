# BlockSchema.md — v1 Canonical Schema

## Container
```json
{ "version": 1, "blocks": [] }
```

## Blocks
### heading
- id: string
- type: "heading"
- level: 1..6
- text: string
- marks: InlineMark[] (optional)

### paragraph
- id: string
- type: "paragraph"
- text: string
- marks: InlineMark[] (optional)

### list
- id: string
- type: "list"
- style: "bulleted" | "numbered"
- items: string[]

### image
- id: string
- type: "image"
- assetId: string
- caption: string (optional)

## InlineMark (v1 minimal)
- { type: "bold", range: [start, end] }
- { type: "italic", range: [start, end] }
- { type: "link", range: [start, end], href: string }

## Rules
- No arbitrary HTML.
- Plain text + marks only.
- Stable block IDs.
- Export relies on this schema.
