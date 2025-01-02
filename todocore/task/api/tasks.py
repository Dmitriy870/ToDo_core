import asyncio

from celery import shared_task
from common.service import (
    check_kafka_availability,
    check_redis_availability,
    send_notification,
    send_tg_alert,
)
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


@shared_task
def check_services():
    """
    Check the availability of external services.
    """
    is_active = None
    services = ["redis", "kafka"]
    for service in services:
        if service == "redis":
            is_active = check_redis_availability()
        elif service == "kafka":
            is_active = asyncio.run(check_kafka_availability())
        else:
            raise ValueError("Service {} is not supported.".format(service))

    if is_active:
        send_tg_alert(f"Service {services} is ok!")
    else:
        send_tg_alert(f"Service {services} is down!")
