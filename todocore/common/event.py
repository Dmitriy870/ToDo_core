import logging
from enum import StrEnum

from common.kafka_producers import KafkaProducer, KafkaTopic

logger = logging.getLogger(__name__)


class EventName(StrEnum):
    GET = "get_"
    GET_ALL = "get_all"
    CREATE = "create_"
    UPDATE = "update_"
    DELETE = "delete_"
    ADD_ON_PROJECT = "add_on_project"
    CHANGE_ROLE_ON_PROJECT = "change_role_on_project"
    DELETE_FROM_PROJECT = "delete_from_project"


class EventManager:
    @staticmethod
    def build_event(
        event_name: EventName,
        model_type: str,
        model_data: dict | None,
        entity_id: str,
        event_type: str = "ModelEvent",
        received_from: str = "analytics",
    ) -> dict:
        return {
            "event_type": event_type,
            "event_name": event_name,
            "received_from": received_from,
            "model_type": model_type,
            "model_data": model_data,
            "entity_id": entity_id,
        }

    @classmethod
    def send_event(
        cls,
        event_name: str | EventName,
        model_type: str,
        topic: KafkaTopic,
        event_type: str,
        model_data: dict | None = None,
        entity_id: str | None = None,
        received_from: str = "analytics",
    ):
        event_payload = cls.build_event(
            event_name=event_name,
            model_type=model_type,
            model_data=model_data,
            event_type=event_type,
            entity_id=entity_id,
            received_from=received_from,
        )
        logger.info("Event file,before produce_message")
        producer = KafkaProducer()
        producer.produce_message(topic, event_payload)
