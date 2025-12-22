import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("paperless")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Broker via REDIS_URL
app.conf.broker_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
app.conf.result_backend = os.getenv("REDIS_URL", "redis://redis:6379/0")
