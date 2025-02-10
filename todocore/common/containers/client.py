from common.config import RedisConfig
from dependency_injector import containers, providers
from redis import Redis


class RedisClient(Redis):
    def __init__(self, config: RedisConfig):
        super().__init__(host=config.host, port=config.port, db=config.db)


class ClientContainer(containers.DeclarativeContainer):
    config = providers.Singleton(RedisConfig)

    redis_client = providers.Factory(
        RedisClient,
        config=config,
    )
