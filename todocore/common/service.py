import logging
from smtplib import SMTPException

import aiohttp
from common.config import AppConfig
from django.core.mail import send_mail
from redis import Redis

config = AppConfig()

logger = logging.getLogger(__name__)


def send_notification(task_info):
    """
    Send an email notification about the task deadline.
    """
    try:
        user_email = "rbinans@gmail.com"
        subject = "Дедлайн задачи"
        message = f""" 
        Дедлайн задачи наступит через час.

        Информация о задаче
        - Название: {task_info.title}
        - Описание: {task_info.description}
        - Дедлайн: {task_info.deadline}
        - Ответственный: {task_info.assignee}"""  # noqa

        send_mail(
            subject,
            message,
            config.email.default_email,
            [user_email],
            fail_silently=False,
        )
        logger.info(f"Notification sent to {user_email}.")
    except SMTPException as e:
        logger.error(f"Error sending notification: {e}", exc_info=True)


async def send_tg_alert(message):
    """
    Send a Telegram alert.
    """
    bot_token = config.telegram.token
    chat_id = config.telegram.chat_id
    url = f"{config.telegram.url}bot{bot_token}/sendMessage"  # noqa
    payload = {"chat_id": chat_id, "text": message}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.info("Message sent successfully!")
                else:
                    logger.error(f"Error: {response.status}, {await response.json()}")
    except aiohttp.ClientError as e:
        logger.error(f"Error sending Telegram message: {e}", exc_info=True)


def check_redis_availability():
    """
    Check if Redis is available.
    """
    try:
        client = Redis(
            host=config.redis.host,
            port=config.redis.port,
            db=config.redis.db,
            socket_connect_timeout=3,
        )
        client.ping()
        return True
    except ConnectionError as e:
        logger.error(f"Redis is unavailable: {e}", exc_info=True)
        return False
