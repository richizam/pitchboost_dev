from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "pitchboost-api-gateway"
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"

settings = Settings()
