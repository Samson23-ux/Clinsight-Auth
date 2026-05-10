from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_encoding="utf-8")

    # environment
    ENVIRONMENT: str

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

    # JWT
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_TIME: int
    REFRESH_TOKEN_EXPIRE_TIME: int
    ACCESS_TOKEN_SECRET_KEY: str
    REFRESH_TOKEN_SECRET_KEY: str

    # session
    SESSION_SECRET_KEY: str

    # redis
    REDIS_URL: str

settings: Settings = Settings()
