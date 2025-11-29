"""
API routes for Task Manager application.
Handles HTTP routing and request/response handling.
"""

from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional

from app.models import (
    TaskCreate, TaskUpdate, Task, TaskList, 
    TaskStatistics, Priority, TaskStatus
)
from app.database import get_repository, TaskRepositoryInterface, TaskNotFoundError
from app.config import settings

# Create router with prefix
router = APIRouter(prefix=settings.API_PREFIX, tags=["tasks"])


def get_task_repository() -> TaskRepositoryInterface:
    """Dependency for getting task repository."""
    return get_repository()


@router.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    repo: TaskRepositoryInterface = Depends(get_task_repository)
) -> Task:
    """
    Create a new task.
    
    - **title**: Required. The task title (1-200 characters)
    - **description**: Optional. Detailed description of the task
    - **priority**: Optional. Priority level (low, medium, high). Default: medium
    - **due_date**: Optional. Due date in YYYY-MM-DD format
    """
    task_data = {
        "title": task.title,
        "description": task.description,
        "priority": task.priority.value if task.priority else Priority.MEDIUM.value,
        "due_date": task.due_date
    }
    created_task = repo.create(task_data)
    return Task(**created_task)


@router.get("/tasks", response_model=TaskList)
async def get_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[Priority] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    limit: int = Query(
        settings.DEFAULT_PAGE_LIMIT,
        ge=1,
        le=settings.MAX_PAGE_LIMIT,
        description="Maximum number of tasks to return"
    ),
    offset: int = Query(0, ge=0, description="Number of tasks to skip"),
    repo: TaskRepositoryInterface = Depends(get_task_repository)
) -> TaskList:
    """
    Get all tasks with optional filtering and pagination.
    
    - **status**: Filter tasks by status (pending, in_progress, completed)
    - **priority**: Filter tasks by priority (low, medium, high)
    - **search**: Search for text in task title or description
    - **limit**: Maximum number of tasks to return (1-1000)
    - **offset**: Number of tasks to skip for pagination
    """
    status_value = status.value if status else None
    priority_value = priority.value if priority else None
    
    tasks, total = repo.get_all(
        status=status_value,
        priority=priority_value,
        search=search,
        limit=limit,
        offset=offset
    )
    
    return TaskList(total=total, tasks=[Task(**t) for t in tasks])


@router.get("/tasks/{task_id}", response_model=Task)
async def get_task(
    task_id: int,
    repo: TaskRepositoryInterface = Depends(get_task_repository)
) -> Task:
    """
    Get a specific task by ID.
    
    - **task_id**: The unique identifier of the task
    """
    task = repo.get_by_id(task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    return Task(**task)


@router.put("/tasks/{task_id}", response_model=Task)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    repo: TaskRepositoryInterface = Depends(get_task_repository)
) -> Task:
    """
    Update an existing task.
    
    - **task_id**: The unique identifier of the task to update
    - Only provided fields will be updated
    """
    update_data = {}
    
    if task_update.title is not None:
        update_data['title'] = task_update.title
    if task_update.description is not None:
        update_data['description'] = task_update.description
    if task_update.priority is not None:
        update_data['priority'] = task_update.priority.value
    if task_update.status is not None:
        update_data['status'] = task_update.status.value
    if task_update.due_date is not None:
        update_data['due_date'] = task_update.due_date
    
    updated_task = repo.update(task_id, update_data)
    
    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    return Task(**updated_task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    repo: TaskRepositoryInterface = Depends(get_task_repository)
) -> None:
    """
    Delete a task by ID.
    
    - **task_id**: The unique identifier of the task to delete
    """
    deleted = repo.delete(task_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )


@router.get("/stats", response_model=TaskStatistics)
async def get_statistics(
    repo: TaskRepositoryInterface = Depends(get_task_repository)
) -> TaskStatistics:
    """
    Get task statistics.
    
    Returns counts of tasks by status and priority.
    """
    stats = repo.get_statistics()
    return TaskStatistics(**stats)
