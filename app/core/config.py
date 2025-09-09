#config.py
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

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
