"""
Unit tests for configuration module.
"""

import pytest
import os

from app.config import Settings, settings, get_settings


class TestSettings:
    """Tests for Settings class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = Settings()
        
        assert config.APP_NAME == "Task Manager API"
        assert config.APP_VERSION == "2.0.0"
        assert config.DEBUG is False
        assert config.HOST == "0.0.0.0"
        assert config.PORT == 8000
        assert config.API_PREFIX == "/api"
    
    def test_database_defaults(self):
        """Test database default configuration."""
        config = Settings()
        
        assert config.DATABASE_PATH == "tasks.db"
        assert "sqlite" in config.DATABASE_URL.lower()
    
    def test_pagination_defaults(self):
        """Test pagination default configuration."""
        config = Settings()
        
        assert config.DEFAULT_PAGE_LIMIT == 100
        assert config.MAX_PAGE_LIMIT == 1000
    
    def test_task_validation_defaults(self):
        """Test task validation configuration."""
        config = Settings()
        
        assert config.TASK_TITLE_MIN_LENGTH == 1
        assert config.TASK_TITLE_MAX_LENGTH == 200
        assert config.TASK_DESCRIPTION_MAX_LENGTH == 1000


class TestGetSettings:
    """Tests for get_settings function."""
    
    def test_get_settings_returns_settings(self):
        """Test get_settings returns Settings instance."""
        result = get_settings()
        
        assert isinstance(result, Settings)
    
    def test_get_settings_returns_global_instance(self):
        """Test get_settings returns the global instance."""
        result = get_settings()
        
        assert result is settings
