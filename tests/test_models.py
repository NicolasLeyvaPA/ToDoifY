"""
Unit tests for data models.
"""

import pytest
from pydantic import ValidationError

from app.models import (
    TaskCreate, TaskUpdate, Task, TaskList,
    Priority, TaskStatus, HealthStatus, TaskStatistics
)


class TestPriority:
    """Tests for Priority enum."""
    
    def test_priority_values(self):
        """Test that all priority values are correct."""
        assert Priority.LOW.value == "low"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.HIGH.value == "high"
    
    def test_priority_from_string(self):
        """Test creating priority from string."""
        assert Priority("low") == Priority.LOW
        assert Priority("medium") == Priority.MEDIUM
        assert Priority("high") == Priority.HIGH


class TestTaskStatus:
    """Tests for TaskStatus enum."""
    
    def test_status_values(self):
        """Test that all status values are correct."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"


class TestTaskCreate:
    """Tests for TaskCreate model."""
    
    def test_create_with_all_fields(self):
        """Test creating task with all fields."""
        task = TaskCreate(
            title="Test Task",
            description="Test Description",
            priority=Priority.HIGH,
            due_date="2025-12-31"
        )
        assert task.title == "Test Task"
        assert task.description == "Test Description"
        assert task.priority == Priority.HIGH
        assert task.due_date == "2025-12-31"
    
    def test_create_with_minimal_fields(self):
        """Test creating task with only required fields."""
        task = TaskCreate(title="Minimal Task")
        assert task.title == "Minimal Task"
        assert task.description is None
        assert task.priority == Priority.MEDIUM  # default
        assert task.due_date is None
    
    def test_create_with_empty_title_fails(self):
        """Test that empty title raises validation error."""
        with pytest.raises(ValidationError):
            TaskCreate(title="")
    
    def test_create_with_long_title_fails(self):
        """Test that title exceeding max length raises error."""
        with pytest.raises(ValidationError):
            TaskCreate(title="x" * 201)
    
    def test_create_with_long_description_fails(self):
        """Test that description exceeding max length raises error."""
        with pytest.raises(ValidationError):
            TaskCreate(title="Test", description="x" * 1001)
    
    def test_create_with_invalid_date_fails(self):
        """Test that invalid date format raises error."""
        with pytest.raises(ValidationError):
            TaskCreate(title="Test", due_date="invalid-date")
    
    def test_create_with_valid_date_formats(self):
        """Test various valid date formats."""
        task = TaskCreate(title="Test", due_date="2025-01-15")
        assert task.due_date == "2025-01-15"


class TestTaskUpdate:
    """Tests for TaskUpdate model."""
    
    def test_update_with_all_fields(self):
        """Test update with all fields."""
        update = TaskUpdate(
            title="Updated Title",
            description="Updated Description",
            priority=Priority.LOW,
            status=TaskStatus.COMPLETED,
            due_date="2025-06-15"
        )
        assert update.title == "Updated Title"
        assert update.status == TaskStatus.COMPLETED
    
    def test_update_with_no_fields(self):
        """Test update with no fields (all None)."""
        update = TaskUpdate()
        assert update.title is None
        assert update.description is None
        assert update.priority is None
        assert update.status is None
        assert update.due_date is None
    
    def test_update_partial_fields(self):
        """Test update with partial fields."""
        update = TaskUpdate(status=TaskStatus.IN_PROGRESS)
        assert update.status == TaskStatus.IN_PROGRESS
        assert update.title is None


class TestTask:
    """Tests for Task response model."""
    
    def test_task_creation(self):
        """Test creating a complete task response."""
        task = Task(
            id=1,
            title="Test",
            description="Desc",
            priority=Priority.MEDIUM,
            status=TaskStatus.PENDING,
            due_date="2025-12-31",
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:00:00"
        )
        assert task.id == 1
        assert task.title == "Test"


class TestTaskList:
    """Tests for TaskList response model."""
    
    def test_task_list_creation(self):
        """Test creating a task list response."""
        task = Task(
            id=1,
            title="Test",
            description=None,
            priority=Priority.MEDIUM,
            status=TaskStatus.PENDING,
            due_date=None,
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:00:00"
        )
        task_list = TaskList(total=1, tasks=[task])
        assert task_list.total == 1
        assert len(task_list.tasks) == 1


class TestHealthStatus:
    """Tests for HealthStatus model."""
    
    def test_health_status_creation(self):
        """Test creating health status response."""
        health = HealthStatus(
            status="healthy",
            timestamp="2025-01-01T00:00:00",
            version="2.0.0",
            database="connected",
            uptime_seconds=100.5
        )
        assert health.status == "healthy"
        assert health.database == "connected"


class TestTaskStatistics:
    """Tests for TaskStatistics model."""
    
    def test_statistics_creation(self):
        """Test creating statistics response."""
        stats = TaskStatistics(
            total_tasks=10,
            by_status={"pending": 5, "in_progress": 3, "completed": 2},
            by_priority={"low": 2, "medium": 5, "high": 3}
        )
        assert stats.total_tasks == 10
        assert stats.by_status["pending"] == 5
