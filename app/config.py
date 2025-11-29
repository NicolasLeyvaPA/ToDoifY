"""
Configuration module for Task Manager application.
Centralizes all configuration values and environment variables.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings
    APP_NAME: str = "Task Manager API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./tasks.db"
    DATABASE_PATH: str = "tasks.db"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # API settings
    API_PREFIX: str = "/api"
    
    # Pagination defaults
    DEFAULT_PAGE_LIMIT: int = 100
    MAX_PAGE_LIMIT: int = 1000
    
    # Task validation
    TASK_TITLE_MIN_LENGTH: int = 1
    TASK_TITLE_MAX_LENGTH: int = 200
    TASK_DESCRIPTION_MAX_LENGTH: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings (dependency injection friendly)."""
    return settings
