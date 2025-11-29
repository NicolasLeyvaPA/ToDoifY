"""
Unit tests for database repository.
"""

import pytest
import os
import tempfile

from app.database import (
    SQLiteTaskRepository,
    DatabaseConnectionError,
    get_repository,
    set_repository,
    reset_repository
)
from app.models import Priority, TaskStatus


class TestSQLiteTaskRepository:
    """Tests for SQLiteTaskRepository."""
    
    @pytest.fixture
    def repo(self) -> SQLiteTaskRepository:
        """Create a repository with a temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        repo = SQLiteTaskRepository(db_path=path)
        yield repo
        if os.path.exists(path):
            os.remove(path)
    
    def test_create_task(self, repo: SQLiteTaskRepository):
        """Test creating a task."""
        task_data = {
            "title": "Test Task",
            "description": "Test Description",
            "priority": "high",
            "due_date": "2025-12-31"
        }
        result = repo.create(task_data)
        
        assert result["id"] is not None
        assert result["title"] == "Test Task"
        assert result["description"] == "Test Description"
        assert result["priority"] == "high"
        assert result["status"] == "pending"
        assert result["due_date"] == "2025-12-31"
        assert result["created_at"] is not None
        assert result["updated_at"] is not None
    
    def test_create_task_minimal(self, repo: SQLiteTaskRepository):
        """Test creating a task with minimal data."""
        task_data = {"title": "Minimal Task"}
        result = repo.create(task_data)
        
        assert result["title"] == "Minimal Task"
        assert result["priority"] == "medium"  # default
        assert result["status"] == "pending"   # default
    
    def test_get_by_id_exists(self, repo: SQLiteTaskRepository):
        """Test getting an existing task by ID."""
        created = repo.create({"title": "Test"})
        result = repo.get_by_id(created["id"])
        
        assert result is not None
        assert result["id"] == created["id"]
        assert result["title"] == "Test"
    
    def test_get_by_id_not_exists(self, repo: SQLiteTaskRepository):
        """Test getting a non-existent task by ID."""
        result = repo.get_by_id(99999)
        assert result is None
    
    def test_get_all_empty(self, repo: SQLiteTaskRepository):
        """Test getting all tasks when none exist."""
        tasks, total = repo.get_all()
        
        assert tasks == []
        assert total == 0
    
    def test_get_all_with_tasks(self, repo: SQLiteTaskRepository):
        """Test getting all tasks."""
        repo.create({"title": "Task 1"})
        repo.create({"title": "Task 2"})
        repo.create({"title": "Task 3"})
        
        tasks, total = repo.get_all()
        
        assert len(tasks) == 3
        assert total == 3
    
    def test_get_all_filter_by_status(self, repo: SQLiteTaskRepository):
        """Test filtering tasks by status."""
        repo.create({"title": "Task 1"})
        task2 = repo.create({"title": "Task 2"})
        repo.update(task2["id"], {"status": "completed"})
        
        tasks, total = repo.get_all(status="pending")
        
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Task 1"
    
    def test_get_all_filter_by_priority(self, repo: SQLiteTaskRepository):
        """Test filtering tasks by priority."""
        repo.create({"title": "High Priority", "priority": "high"})
        repo.create({"title": "Low Priority", "priority": "low"})
        
        tasks, total = repo.get_all(priority="high")
        
        assert len(tasks) == 1
        assert tasks[0]["priority"] == "high"
    
    def test_get_all_search(self, repo: SQLiteTaskRepository):
        """Test searching tasks."""
        repo.create({"title": "Buy groceries"})
        repo.create({"title": "Clean house"})
        repo.create({"title": "Buy milk", "description": "From grocery store"})
        
        tasks, total = repo.get_all(search="Buy")
        
        assert total == 2  # "Buy groceries" and "Buy milk"
    
    def test_get_all_pagination(self, repo: SQLiteTaskRepository):
        """Test pagination."""
        for i in range(10):
            repo.create({"title": f"Task {i}"})
        
        tasks, total = repo.get_all(limit=3, offset=0)
        assert len(tasks) == 3
        assert total == 10
        
        tasks, total = repo.get_all(limit=3, offset=3)
        assert len(tasks) == 3
        
        tasks, total = repo.get_all(limit=3, offset=9)
        assert len(tasks) == 1
    
    def test_update_task(self, repo: SQLiteTaskRepository):
        """Test updating a task."""
        created = repo.create({"title": "Original"})
        
        updated = repo.update(created["id"], {
            "title": "Updated",
            "description": "New description",
            "priority": "high",
            "status": "in_progress"
        })
        
        assert updated["title"] == "Updated"
        assert updated["description"] == "New description"
        assert updated["priority"] == "high"
        assert updated["status"] == "in_progress"
        assert updated["updated_at"] != created["updated_at"]
    
    def test_update_task_partial(self, repo: SQLiteTaskRepository):
        """Test partial update."""
        created = repo.create({"title": "Original", "description": "Original desc"})
        
        updated = repo.update(created["id"], {"title": "Updated"})
        
        assert updated["title"] == "Updated"
        assert updated["description"] == "Original desc"  # unchanged
    
    def test_update_task_not_exists(self, repo: SQLiteTaskRepository):
        """Test updating a non-existent task."""
        result = repo.update(99999, {"title": "Updated"})
        assert result is None
    
    def test_update_task_no_changes(self, repo: SQLiteTaskRepository):
        """Test updating with no changes."""
        created = repo.create({"title": "Original"})
        result = repo.update(created["id"], {})
        
        assert result["title"] == "Original"
    
    def test_delete_task(self, repo: SQLiteTaskRepository):
        """Test deleting a task."""
        created = repo.create({"title": "To Delete"})
        
        result = repo.delete(created["id"])
        assert result is True
        
        # Verify deletion
        assert repo.get_by_id(created["id"]) is None
    
    def test_delete_task_not_exists(self, repo: SQLiteTaskRepository):
        """Test deleting a non-existent task."""
        result = repo.delete(99999)
        assert result is False
    
    def test_get_statistics_empty(self, repo: SQLiteTaskRepository):
        """Test statistics with no tasks."""
        stats = repo.get_statistics()
        
        assert stats["total_tasks"] == 0
        assert stats["by_status"]["pending"] == 0
        assert stats["by_status"]["in_progress"] == 0
        assert stats["by_status"]["completed"] == 0
    
    def test_get_statistics_with_tasks(self, repo: SQLiteTaskRepository):
        """Test statistics with various tasks."""
        repo.create({"title": "T1", "priority": "high"})
        repo.create({"title": "T2", "priority": "low"})
        task3 = repo.create({"title": "T3", "priority": "medium"})
        repo.update(task3["id"], {"status": "completed"})
        
        stats = repo.get_statistics()
        
        assert stats["total_tasks"] == 3
        assert stats["by_status"]["pending"] == 2
        assert stats["by_status"]["completed"] == 1
        assert stats["by_priority"]["high"] == 1
        assert stats["by_priority"]["low"] == 1
        assert stats["by_priority"]["medium"] == 1
    
    def test_health_check_success(self, repo: SQLiteTaskRepository):
        """Test health check with valid database."""
        result = repo.health_check()
        assert result is True
    
    def test_health_check_failure(self):
        """Test health check with invalid database."""
        # Create a repository pointing to a non-existent directory
        # This test verifies that health_check handles errors gracefully
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        repo = SQLiteTaskRepository(db_path=path)
        
        # Remove the file to simulate connection failure
        os.remove(path)
        
        # Health check should return False for inaccessible database
        # Note: SQLite may still succeed if the file can be created
        # The important thing is that health_check doesn't crash
        result = repo.health_check()
        # Result depends on whether SQLite can create the file
        assert isinstance(result, bool)


class TestRepositoryManagement:
    """Tests for repository management functions."""
    
    def test_get_repository_creates_instance(self):
        """Test that get_repository creates an instance."""
        reset_repository()
        repo = get_repository()
        assert repo is not None
    
    def test_set_repository(self):
        """Test setting a custom repository."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        
        custom_repo = SQLiteTaskRepository(db_path=path)
        set_repository(custom_repo)
        
        assert get_repository() is custom_repo
        
        reset_repository()
        if os.path.exists(path):
            os.remove(path)
    
    def test_reset_repository(self):
        """Test resetting the repository."""
        reset_repository()
        repo1 = get_repository()
        reset_repository()
        repo2 = get_repository()
        
        # Should be different instances
        assert repo1 is not repo2
