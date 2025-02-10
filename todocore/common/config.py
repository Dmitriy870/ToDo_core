import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class RedisConfig:
    url: str = os.getenv("REDIS_URL")
    host: str = os.getenv("REDIS_HOST")
    port: int = int(os.getenv("REDIS_PORT"))
    db: int = int(os.getenv("REDIS_DB"))


@dataclass
class KafkaConfig:
    bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS")


@dataclass
class TelegramConfig:
    token: str = os.getenv("TELEGRAM_TOKEN", "7734496041:AAEMj0n5jq_uFdgrJARH0g4iyTjMsHXfWxc")
    chat_id: int = int(os.getenv("TELEGRAM_CHAT_ID"))
    url: str = os.getenv("TELEGRAM_URL")


@dataclass
class EmailConfig:
    default_email: str = os.getenv("DEFAULT_FROM_EMAIL")


@dataclass
class AuthConfig:
    url: str = os.getenv("AUTH_SERVICE_URL")
