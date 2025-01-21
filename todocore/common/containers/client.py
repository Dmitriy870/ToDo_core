from common.config import RedisConfig
from dependency_injector import containers, providers
from redis import Redis


class ClientContainer(containers.DeclarativeContainer):
    config = providers.Singleton(RedisConfig)

    redis_client = providers.Factory(
        Redis,
        host=config().host,
        port=config().port,
        db=config().db,
    )
