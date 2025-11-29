"""
Task Manager Application Package.
"""

from app.main import app, create_app
from app.config import settings

__all__ = ["app", "create_app", "settings"]
