from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class E2ESettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="tests/e2e/.env.e2e", env_file_encoding="utf-8", extra="ignore"
    )

    base_url: str = Field(default="http://web:8000", validation_alias="BASE_URL")
    api_key: str = Field(validation_alias="API_KEY")
