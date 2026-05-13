from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_encoding="utf-8")

    # environment
    ENVIRONMENT: str = "development"

    # api details
    API_PREFIX: str = "/api"
    API_TITLE: str = "Clinsights Auth"
    API_VERSION: str = "v1.0"

    # async db
    ASYNC_DB_URL: str

    # sync db
    SYNC_DB_URL: str

    # test db
    ASYNC_TEST_DB_URL: str

    # Argon2
    ARGON2_PASSWORD_PEPPER: str

    # OAuth2
    CLIENT_ID: str
    CLIENT_SECRET: str
    OAUTH2_ALGORITHM: str = "RS256"

    # JWT
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_TIME: int = 3
    REFRESH_TOKEN_EXPIRE_TIME: int = 1
    ACCESS_TOKEN_SECRET_KEY: str
    REFRESH_TOKEN_SECRET_KEY: str

    # session
    SESSION_SECRET_KEY: str

    # redis
    REDIS_URL: str

    # email creds
    API_EMAIL: str
    API_EMAIL_PASSWORD: str

    # SMTP
    SMTP_PORT: int = 465

    # RabbitMQ
    API_BROKER: str

settings: Settings = Settings()
