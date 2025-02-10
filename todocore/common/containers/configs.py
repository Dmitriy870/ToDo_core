from common.config import AuthConfig, EmailConfig, TelegramConfig
from dependency_injector import containers, providers


class AuthConfigContainer(containers.DeclarativeContainer):
    auth_config = providers.Singleton(AuthConfig)


class TgConfigContainer(containers.DeclarativeContainer):
    tg_config = providers.Singleton(TelegramConfig)


class EmailConfigContainer(containers.DeclarativeContainer):
    email_config = providers.Singleton(EmailConfig)
