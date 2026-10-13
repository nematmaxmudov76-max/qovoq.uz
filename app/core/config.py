from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Root directory: blog_api/
ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    SECRET_KEY: str 
    ALGORITHM: str 
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    REDIS_HOST: str 
    REDIS_PORT: int 

    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str 

    APP_TITLE: str = "Blog API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool 


settings = Settings()
