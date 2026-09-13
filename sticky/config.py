import os
from enum import StrEnum
from typing import Literal

from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    development = "development"
    production = "production"
    testing = "testing"


env = Environment(os.getenv("STICKY_ENV", Environment.development))
if env == Environment.testing:
    env_file = ".env.testing"
else:
    env_file = ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="STICKY_",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_file=env_file,
        extra="allow",
    )

    ENV: Environment = Environment.development
    LOG_LEVEL: str = "DEBUG"

    STICKER_PACK_NAME: str = "synca_by_examplebot"  # mast end with `_by_<bot_username>`
    STICKER_PACK_TITLE: str = "Sticky Gifts"
    STICKER_PACK_OWNER_ID: int = 0  # user id of the sticker pack owner

    # Telegram bot
    BOT_TOKEN: str = ""
    BOT_WEBHOOK_URL: str = ""
    BOT_WEBHOOK_PATH: str = "/bot/webhook"
    BOT_WEBHOOK_SECRET_TOKEN: str | None = None

    # Database
    POSTGRES_USER: str = "sticky"
    POSTGRES_PWD: str = "sticky"
    POSTGRES_DATABASE: str = "sticky_dev"
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432
    DATABASE_POOL_SIZE: int = 5
    DATABASE_POOL_RECYCLE_SECONDS: int = 600  # 10 minutes
    DATABASE_COMMAND_TIMEOUT_SECONDS: float = 30.0

    def get_postgres_dsn(self, driver: Literal["asyncpg", "psycopg2"]) -> str:
        return str(
            PostgresDsn.build(
                scheme=f"postgresql+{driver}",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PWD,
                host=self.POSTGRES_HOST,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DATABASE,
            )
        )

    def is_development(self) -> bool:
        return self.is_environment({Environment.development})

    def is_production(self) -> bool:
        return self.is_environment({Environment.production})

    def is_testing(self) -> bool:
        return self.is_environment({Environment.testing})

    def is_environment(self, environments: set[Environment]) -> bool:
        return self.ENV in environments

    @field_validator("BOT_WEBHOOK_URL", mode="before")
    @classmethod
    def remove_trailing_slash(cls, v: str) -> str:
        if isinstance(v, str):
            return v.rstrip("/")
        return v


settings = Settings()
