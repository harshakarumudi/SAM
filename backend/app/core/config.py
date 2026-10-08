import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Agriculture Monitoring System"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./agri_dev.db")

    # JWT Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "agri_secure_production_secret_key_change_in_prod_1234567890")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # MQTT Configuration
    MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    MQTT_USER: str = os.getenv("MQTT_USER", "backend_service")
    MQTT_PASSWORD: str = os.getenv("MQTT_PASSWORD", "backend_secure_mqtt_pass")
    MQTT_CLIENT_ID: str = os.getenv("MQTT_CLIENT_ID", "agri_backend_core")
    MQTT_KEEPALIVE: int = 60

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    LOGIN_RATE_LIMIT_PER_MINUTE: int = int(os.getenv("LOGIN_RATE_LIMIT_PER_MINUTE", "10"))

    # Actuator & Watchdog Safety Controls
    MAX_PUMP_RUNTIME_SECONDS: int = int(os.getenv("MAX_PUMP_RUNTIME_SECONDS", "600"))  # 10 mins
    SENSOR_WATCHDOG_TIMEOUT_SECONDS: int = int(os.getenv("SENSOR_WATCHDOG_TIMEOUT_SECONDS", "60"))  # 60s

    # Weather
    WEATHER_API_KEY: str | None = os.getenv("WEATHER_API_KEY", "")
    WEATHER_LOCATION: str = os.getenv("WEATHER_LOCATION", "Farm_Sector_Alpha")

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"


settings = Settings()
