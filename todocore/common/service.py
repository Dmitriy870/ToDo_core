import logging
from smtplib import SMTPException

import aiohttp
from common.config import EmailConfig, TelegramConfig
from common.containers.client import ClientContainer
from common.containers.configs import EmailConfigContainer, TgConfigContainer
from dependency_injector.wiring import Provide, inject
from django.core.mail import send_mail
from redis import Redis

logger = logging.getLogger(__name__)


@inject
def send_notification(
    task_info, config_email: EmailConfig = Provide[EmailConfigContainer.email_config]
):
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
            config_email.default_email,
            [user_email],
            fail_silently=False,
        )
        logger.info(f"Notification sent to {user_email}.")
    except SMTPException as e:
        logger.error(f"Error sending notification: {e}", exc_info=True)


@inject
async def send_tg_alert(message, config_tg: TelegramConfig = Provide[TgConfigContainer.tg_config]):
    """
    Send a Telegram alert.
    """
    bot_token = config_tg.token
    chat_id = config_tg.chat_id
    url = f"{config_tg.url}bot{bot_token}/sendMessage"  # noqa
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


@inject
def check_redis_availability(redis_client: Redis = Provide[ClientContainer.redis_client]):
    """
    Check if Redis is available.
    """
    try:
        redis_client.ping()
        return True
    except ConnectionError as e:
        logger.error(f"Redis is unavailable: {e}", exc_info=True)
        return False
