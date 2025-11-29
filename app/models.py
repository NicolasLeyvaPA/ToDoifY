"""
Data models for Task Manager application.
Follows Single Responsibility Principle - only handles data structures.
"""

from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.config import settings


class Priority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(str, Enum):
    """Task status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskBase(BaseModel):
    """Base task model with common fields."""
    title: str = Field(
        ...,
        min_length=settings.TASK_TITLE_MIN_LENGTH,
        max_length=settings.TASK_TITLE_MAX_LENGTH,
        description="Task title"
    )
    description: Optional[str] = Field(
        None,
        max_length=settings.TASK_DESCRIPTION_MAX_LENGTH,
        description="Task description"
    )
    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Task priority level"
    )
    due_date: Optional[str] = Field(
        None,
        description="Due date in YYYY-MM-DD format"
    )

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate due date format if provided."""
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Due date must be in YYYY-MM-DD format")
        return v


class TaskCreate(TaskBase):
    """Schema for creating a new task."""
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Complete project documentation",
                "description": "Write comprehensive documentation for the API",
                "priority": "high",
                "due_date": "2025-12-31"
            }
        }
    }


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""
    title: Optional[str] = Field(
        None,
        min_length=settings.TASK_TITLE_MIN_LENGTH,
        max_length=settings.TASK_TITLE_MAX_LENGTH
    )
    description: Optional[str] = Field(
        None,
        max_length=settings.TASK_DESCRIPTION_MAX_LENGTH
    )
    priority: Optional[Priority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[str] = None

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate due date format if provided."""
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Due date must be in YYYY-MM-DD format")
        return v


class Task(BaseModel):
    """Complete task model for responses."""
    id: int
    title: str
    description: Optional[str]
    priority: Priority
    status: TaskStatus
    due_date: Optional[str]
    created_at: str
    updated_at: str


class TaskList(BaseModel):
    """Schema for paginated task list response."""
    total: int
    tasks: List[Task]


class HealthStatus(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    version: str
    database: str
    uptime_seconds: float


class TaskStatistics(BaseModel):
    """Task statistics response model."""
    total_tasks: int
    by_status: dict
    by_priority: dict
