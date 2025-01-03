import os
from dataclasses import dataclass, field

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
    token: str = os.getenv("TELEGRAM_TOKEN")
    chat_id: int = int(os.getenv("TELEGRAM_CHAT_ID"))


@dataclass
class EmailConfig:
    default_email: str = os.getenv("DEFAULT_FROM_EMAIL")


@dataclass
class AppConfig:
    redis: RedisConfig = field(default_factory=RedisConfig)
    kafka: KafkaConfig = field(default_factory=KafkaConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    email: EmailConfig = field(default_factory=EmailConfig)


config = AppConfig()
