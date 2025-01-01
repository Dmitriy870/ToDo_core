import os
from datetime import timedelta

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "todo__core.settings")

app = Celery("todo__core")


app.config_from_object("django.conf:settings", namespace="CELERY")


app.autodiscover_tasks()

# Периодические задачи (Celery Beat)
app.conf.beat_schedule = {
    # Пример периодической задачи (если нужно)
    "example-periodic-task": {
        "task": "task.api.tasks.send_deadline_notification",  # Путь к задаче
        "schedule": timedelta(minutes=30),  # Запускать каждые 30 минут
    },
}
