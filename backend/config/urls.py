from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from pathlib import Path
import os

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve frontend index.html for all non-API routes
# WhiteNoise handles static files (JS/CSS/images) automatically
# We serve index.html from STATIC_ROOT for SPA routing
def serve_frontend(request, path=""):
    return serve(request, "index.html", document_root=settings.STATIC_ROOT)

urlpatterns += [
    re_path(r"^(?!api|admin|static|media).*", serve_frontend, name="frontend"),
]
