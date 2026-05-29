from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    db_driver: str = "postgresql+asyncpg"
    db_host: str = Field(validation_alias="POSTGRES_HOST")
    db_port: int = Field(validation_alias="POSTGRES_PORT")
    db_user: str = Field(validation_alias="POSTGRES_USER")
    db_password: SecretStr = Field(validation_alias="POSTGRES_PASSWORD")
    db_name: str = Field(validation_alias="POSTGRES_DB")

    rabbitmq_host: str = Field(validation_alias="RABBITMQ_HOST")
    rabbitmq_port: int = Field(validation_alias="RABBITMQ_PORT")
    rabbitmq_user: str = Field(validation_alias="RABBITMQ_USER")
    rabbitmq_password: SecretStr = Field(validation_alias="RABBITMQ_PASSWORD")
    rabbitmq_vhost: str = Field(default="", validation_alias="RABBITMQ_VHOST")

    api_key: SecretStr = Field(validation_alias="API_KEY")

    dispatch_interval_seconds: int = Field(default=5)
    log_queue_maxsize: int = Field(default=10000)

    @property
    def database_url(self) -> str:
        return (
            f"{self.db_driver}://{self.db_user}:{self.db_password.get_secret_value()}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password.get_secret_value()}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}/{self.rabbitmq_vhost}"
        )

    @property
    def log_format(self) -> str:
        return "%(name)s\t[%(funcName)s:%(lineno)s]\t%(asctime)s\t[%(levelname)s]\t%(message)s"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
