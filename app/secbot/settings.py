from pydantic import BaseSettings, PostgresDsn


class SecbotSettings(BaseSettings):
    postgres_dsn: PostgresDsn

    class Config:
        env_prefix = "secbot_"


settings = SecbotSettings()
