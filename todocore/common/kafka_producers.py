import json
import logging
from enum import Enum

from common.config import KafkaConfig
from common.utils import CustomJSONEncoder
from confluent_kafka import KafkaError, KafkaException, Producer

kafka_config = KafkaConfig()
logger = logging.getLogger(__name__)


class KafkaTopic(str, Enum):
    MODELS_TOPIC = "models_topic"
    EVENTS_TOPIC = "events_topic"


def produce_message(topic: str, data: dict):
    producer = Producer(
        {
            "bootstrap.servers": kafka_config.bootstrap_servers,
        }
    )

    try:
        serialized_value = json.dumps(data, cls=CustomJSONEncoder)

        producer.produce(topic=topic, key="MESSAGE_KEY", value=serialized_value)
        producer.flush()

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
