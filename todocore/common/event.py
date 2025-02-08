import logging
from enum import Enum

from common.kafka_producers import produce_message

logger = logging.getLogger(__name__)


class EventName(str, Enum):
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
        event_name: str,
        model_type: str,
        model_data: dict | None,
        entity_id: str,
        event_type: str = "ModelEvent",
        received_by: str = "analytics",
    ) -> dict:

        return {
            "event_type": event_type,
            "event_name": event_name,
            "received_by": received_by,
            "model_type": model_type,
            "model_data": model_data,
            "entity_id": entity_id,
        }

    @classmethod
    def send_event(
        cls,
        event_name: str,
        model_type: str,
        topic: str,
        model_data: dict | None = None,
        entity_id: str | None = None,
        received_by: str = "analytics",
    ):

        event_payload = cls.build_event(
            event_name=event_name,
            model_type=model_type,
            model_data=model_data,
            entity_id=entity_id,
            received_by=received_by,
        )
        logger.info("Event file,before produce_message")
        produce_message(topic, event_payload)
