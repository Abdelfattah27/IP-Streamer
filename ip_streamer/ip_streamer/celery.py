import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ip_streamer.settings")

app = Celery("ip_streamer")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
