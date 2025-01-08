import os
from datetime import timedelta

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "todo__core.settings")

app = Celery("todo__core")

app.config_from_object("django.conf:settings", namespace="CELERY")


app.conf.beat_schedule = {
    "check-services-task": {
        "task": "task.api.tasks.check_services",
        "schedule": timedelta(minutes=30),
    },
}

app.autodiscover_tasks()
