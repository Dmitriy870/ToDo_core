import logging

from common.containers.client import ClientContainer
from common.containers.configs import (
    AuthConfigContainer,
    CommonConfigContainer,
    EmailConfigContainer,
    TgConfigContainer,
)
from django.apps import AppConfig

logger = logging.getLogger(__name__)

CONTAINERS_INITIALIZED = False


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "common"

    def ready(self):
        global CONTAINERS_INITIALIZED
        if CONTAINERS_INITIALIZED:
            return

        logger.info("Initializing containers...")

        client_container = ClientContainer()
        email_container = EmailConfigContainer()
        tg_container = TgConfigContainer()
        auth_container = AuthConfigContainer()
        common_container = CommonConfigContainer()

        packages = ["common"]

        client_container.wire(packages=packages)
        email_container.wire(packages=packages)
        tg_container.wire(packages=packages)
        auth_container.wire(packages=packages)
        common_container.wire(packages=packages)

        CONTAINERS_INITIALIZED = True

        logger.info("Containers initialized!")
