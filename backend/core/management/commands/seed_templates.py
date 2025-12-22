"""
Management command to seed default templates.
Run with: python manage.py seed_templates
"""
from django.core.management.base import BaseCommand
from core.models import Template
from core.template_mapping import DEFAULT_MAPPING


TEMPLATES = [
    {
        "name": "Standard Academic",
        "mapping_json": {
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
                "lineSpacing": 1.5
            },
            "margins": {
                "top": 1440,
                "bottom": 1440,
                "left": 1440,
                "right": 1440
            }
        }
    },
    {
        "name": "Modern Policy",
        "mapping_json": {
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
                "heading": {"name": "Calibri", "size": 16, "bold": True},
                "body": {"name": "Calibri", "size": 11, "bold": False}
            },
            "spacing": {
                "beforeHeading": 18,
                "afterHeading": 6,
                "beforeParagraph": 0,
                "afterParagraph": 8,
                "lineSpacing": 1.15
            },
            "margins": {
                "top": 1440,
                "bottom": 1440,
                "left": 1800,
                "right": 1800
            }
        }
    }
]


class Command(BaseCommand):
    help = 'Seeds default templates for DOCX export'

    def handle(self, *args, **options):
        created_count = 0
        
        for template_data in TEMPLATES:
            template, created = Template.objects.get_or_create(
                name=template_data["name"],
                defaults={"mapping_json": template_data["mapping_json"]}
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created template: {template.name}'))
            else:
                self.stdout.write(f'Template already exists: {template.name}')
        
        self.stdout.write(self.style.SUCCESS(f'Done. Created {created_count} new templates.'))

