"""
Test configuration and fixtures for Task Manager tests.
"""

import os
import pytest
import tempfile
from typing import Generator

from fastapi.testclient import TestClient

from app.main import create_app
from app.database import SQLiteTaskRepository, set_repository, reset_repository
from app.config import settings


@pytest.fixture(scope="function")
def test_db_path() -> Generator[str, None, None]:
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture(scope="function")
def test_repository(test_db_path: str) -> Generator[SQLiteTaskRepository, None, None]:
    """Create a test repository with a temporary database."""
    repo = SQLiteTaskRepository(db_path=test_db_path)
    set_repository(repo)
    yield repo
    reset_repository()


@pytest.fixture(scope="function")
def client(test_repository: SQLiteTaskRepository) -> Generator[TestClient, None, None]:
    """Create a test client with a fresh database."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_task_data() -> dict:
    """Sample task data for testing."""
    return {
        "title": "Test Task",
        "description": "Test Description",
        "priority": "high",
        "due_date": "2025-12-31"
    }


@pytest.fixture
def sample_task_minimal() -> dict:
    """Minimal task data for testing."""
    return {"title": "Minimal Task"}
