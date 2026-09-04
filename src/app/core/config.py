from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field
from typing import Optional

class RedisConfig(BaseModel):
    redis_host: str = Field(alias="REDIS_HOST")
    redis_port: int = Field(alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    
    redis_username: Optional[str] = Field(default=None, alias="REDIS_USERNAME")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")

    @property
    def redis_url(self):
        if self.redis_username and self.redis_password:
            return f"redis://{self.redis_username}:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        elif self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

class Settings(BaseSettings):
    """Application configuration settings."""
    
    ENVIRONMENT: str

    # Image
    ALLOWED_IMAGE_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp"}
    MAX_IMAGE_DIMENSION: int = 2048          # resize target
    MIN_IMAGE_DIMENSION: int = 100           # reject tiny images
    MAX_IMAGE_DIMENSION_LIMIT: int = 8000    # reject absurdly large images outright

    MAX_FILE_SIZE_MB: int = 5
    AI_REQUEST_TIMEOUT_SECONDS: int = 60

    # Logger
    DEBUG: bool
    LOG_TO_FILE: bool
    
    # Redis
    REDIS_CONFIG: RedisConfig

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # CORS
    @property
    def ALLOWED_ORIGINS(self) -> list[str]:
        if self.ENVIRONMENT == "prod":
            return [
                "https://frontend-leaf-lens.vercel.app",
            ]

        return [
            "http://localhost",
            "http://localhost:3000",
        ]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        case_sensitive=True,
    )
        
@lru_cache
def get_settings() -> Settings:
    return Settings()

config = get_settings()