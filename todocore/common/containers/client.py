from common.config import AppConfig
from dependency_injector import containers, providers
from redis import Redis


class ClientContainer(containers.DeclarativeContainer):
    config = providers.Singleton(AppConfig)

    redis_client = providers.Factory(
        Redis,
        host=config().redis.host,
        port=config().redis.port,
        db=config().redis.db,
    )
