from celery import shared_task
from common.service import send_notification
from task.models import Task


@shared_task
def send_deadline_notification(task_id):
    """
    Celery task to send deadline notification.
    """
    task = Task.objects.get(id=task_id)
    send_notification()
    task.completed = True
    task.save()
