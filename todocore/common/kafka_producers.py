import json
import logging
from enum import StrEnum

from common.config import KafkaConfig
from common.utils import CustomJSONEncoder
from confluent_kafka import KafkaError, KafkaException, Producer

kafka_config = KafkaConfig()
logger = logging.getLogger(__name__)


class KafkaTopic(StrEnum):
    MODELS_TOPIC = "models_topic"
    EVENTS_TOPIC = "events_topic"


class KafkaProducer:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "producer"):
            self.producer = Producer(
                {
                    "bootstrap.servers": kafka_config.bootstrap_servers,
                }
            )
            logger.info("Kafka producer initialized.")

    def produce_message(self, topic: str, data: dict):
        try:
            serialized_value = json.dumps(data, cls=CustomJSONEncoder)
            self.producer.produce(topic=topic, value=serialized_value)
            self.producer.flush()
            logger.info(f"Sent message to topic '{topic}': {data}")
        except KafkaException as e:
            if e.args[0].code() == KafkaError._TIMED_OUT:
                logger.error(f"Kafka timeout error: {e}")
            elif e.args[0].code() == KafkaError._ALL_BROKERS_DOWN:
                logger.error(f"No brokers available: {e}")
            else:
                logger.error(f"Kafka error: {e}")
        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
