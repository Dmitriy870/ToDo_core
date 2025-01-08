import logging
from smtplib import SMTPException

from aiohttp import ClientError
from asgiref.sync import async_to_sync
from celery import shared_task
from common.service import check_redis_availability, send_notification, send_tg_alert
from django.core.exceptions import ObjectDoesNotExist
from redis import ConnectionError
from task.models import Task

logger = logging.getLogger(__name__)


@shared_task
def send_deadline_notification(task_id):
    """
    Celery task to send deadline notification.
    """
    try:
        task = Task.objects.get(id=task_id)
        send_notification(task)
        task.completed = True
        task.save()
    except ObjectDoesNotExist:
        logger.error(f"Task with id {task_id} does not exist.")
    except SMTPException as e:
        logger.error(f"Failed to send email notification: {e}")
    except ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
    except ClientError as e:
        logger.error(f"Failed to send Telegram alert: {e}")
    except ValueError as e:
        logger.error(f"Invalid input or configuration: {e}")


@shared_task
def check_services():
    """
    Check the availability of external services.
    """
    services = ["redis"]
    for service in services:
        try:
            if service == "redis":
                is_active = check_redis_availability()
            else:
                raise ValueError(f"Service {service} is not supported.")

            if is_active:
                async_to_sync(send_tg_alert)(f"Service {service} is ok!")
            else:
                async_to_sync(send_tg_alert)(f"Service {service} is down!")
        except ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
        except ValueError as e:
            logger.error(f"Unsupported service: {e}", exc_info=True)
        except ClientError as e:
            logger.error(f"Failed to send Telegram alert: {e}", exc_info=True)
