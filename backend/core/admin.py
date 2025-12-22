from django.contrib import admin
from .models import Project, Document, Section, SectionContent, Comment, Snapshot, AuditLog, ExportJob, Template

admin.site.register(Project)
admin.site.register(Template)
admin.site.register(Document)
admin.site.register(Section)
admin.site.register(SectionContent)
admin.site.register(Comment)
admin.site.register(Snapshot)
admin.site.register(AuditLog)
admin.site.register(ExportJob)
