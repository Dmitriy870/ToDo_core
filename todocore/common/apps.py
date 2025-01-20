import logging

from common.containers.client import ClientContainer
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "common"

    def ready(self):

        logger.info("Initializing containers...")

        client_container = ClientContainer()
        client_container.wire(packages=["common"])

        logger.info("Containers initialized!")
