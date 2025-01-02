import os

from aiokafka import AIOKafkaConsumer
from django.core.mail import send_mail
from dotenv import load_dotenv
from redis import Redis
from requests import post

# Загрузите переменные из .env
load_dotenv()


def send_notification():
    try:
        user_email = "rbinans@gmail.com"
        subject = "Дедлайн задачи"
        message = "Дедлайн задачи наступит через час."

        # Отправка письма
        send_mail(
            subject,
            message,
            os.getenv("DEFAULT_FROM_EMAIL"),
            [user_email],
            fail_silently=False,
        )

        print(f"Уведомление отправлено на {user_email}.")
    except Exception as e:
        print(f"Ошибка при отправке уведомления: {e}")


def send_tg_alert(message):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https: //api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    response = post(url, json=payload)
    if response.status_code == 200:
        print("Сообщение успешно отправлено!")
    else:
        print(f"Ошибка: {response.status_code}, {response.json()}")


def check_redis_availability():
    """
    Check if Redis is available.
    """
    try:
        client = Redis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT")),
            db=int(os.getenv("REDIS_DB")),  #
            socket_connect_timeout=3,
        )
        client.ping()
        return True
    except Exception as e:
        print(f"Redis is down: {e}")
        return False


async def check_kafka_availability():
    """
    Check if Kafka is available using aiokafka.
    """
    try:
        consumer = AIOKafkaConsumer(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
            request_timeout_ms=3000,  #
        )
        await consumer.start()
        await consumer.stop()
        return True
    except Exception as e:
        print(f"Kafka is down: {e}")
        return False
