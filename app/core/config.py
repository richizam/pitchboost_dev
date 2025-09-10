# config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "pitchboost-api-gateway"
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_IN: str = "aith.messages.processing"
    KAFKA_TOPIC_OUT: str = "aith.messages.result"
    KAFKA_CLIENT_ID: str = "pitchboost-gateway"

    # Database (Postgres)
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "postgres"

    # Free tier / credits
    FREE_CREDITS: int = 5

    # Audio validation
    AUDIO_MAX_SECONDS: int = 420
    AUDIO_MAX_CONTENT_LENGTH: int = 50 * 1024 * 1024  # 50 MB

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
