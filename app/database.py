"""
Database module for Task Manager application.
Handles all database operations following Repository pattern.
"""

import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager
from abc import ABC, abstractmethod

from app.config import settings
from app.models import Priority, TaskStatus


class DatabaseConnectionError(Exception):
    """Raised when database connection fails."""
    pass


class TaskNotFoundError(Exception):
    """Raised when a task is not found."""
    pass


class TaskRepositoryInterface(ABC):
    """Abstract interface for task repository (Dependency Inversion Principle)."""
    
    @abstractmethod
    def create(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task."""
        pass
    
    @abstractmethod
    def get_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get a task by ID."""
        pass
    
    @abstractmethod
    def get_all(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get all tasks with optional filtering."""
        pass
    
    @abstractmethod
    def update(self, task_id: int, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a task."""
        pass
    
    @abstractmethod
    def delete(self, task_id: int) -> bool:
        """Delete a task."""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Get task statistics."""
        pass


class SQLiteTaskRepository(TaskRepositoryInterface):
    """SQLite implementation of TaskRepository."""
    
    def __init__(self, db_path: str = None):
        """Initialize repository with database path."""
        self.db_path = db_path or settings.DATABASE_PATH
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Database error: {e}")
        finally:
            if conn:
                conn.close()
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    due_date TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            conn.commit()
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a database row to dictionary."""
        return dict(row) if row else None
    
    def create(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task in the database."""
        now = datetime.now().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tasks (title, description, priority, status, due_date, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_data['title'],
                task_data.get('description'),
                task_data.get('priority', Priority.MEDIUM.value),
                TaskStatus.PENDING.value,
                task_data.get('due_date'),
                now,
                now
            ))
            task_id = cursor.lastrowid
            conn.commit()
            
            cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            return self._row_to_dict(cursor.fetchone())
    
    def get_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get a task by its ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None
    
    def get_all(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get all tasks with optional filtering and pagination."""
        query = 'SELECT * FROM tasks WHERE 1=1'
        count_query = 'SELECT COUNT(*) as count FROM tasks WHERE 1=1'
        params = []
        
        if status:
            query += ' AND status = ?'
            count_query += ' AND status = ?'
            params.append(status)
        
        if priority:
            query += ' AND priority = ?'
            count_query += ' AND priority = ?'
            params.append(priority)
        
        if search:
            query += ' AND (title LIKE ? OR description LIKE ?)'
            count_query += ' AND (title LIKE ? OR description LIKE ?)'
            search_param = f'%{search}%'
            params.extend([search_param, search_param])
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total count
            cursor.execute(count_query, params)
            total = cursor.fetchone()['count']
            
            # Get paginated results
            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            cursor.execute(query, params)
            
            tasks = [self._row_to_dict(row) for row in cursor.fetchall()]
            return tasks, total
    
    def update(self, task_id: int, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a task by ID."""
        # Check if task exists
        existing = self.get_by_id(task_id)
        if not existing:
            return None
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        field_mappings = ['title', 'description', 'priority', 'status', 'due_date']
        for field in field_mappings:
            if field in task_data and task_data[field] is not None:
                update_fields.append(f'{field} = ?')
                value = task_data[field]
                # Handle enum values
                if hasattr(value, 'value'):
                    value = value.value
                params.append(value)
        
        if not update_fields:
            return existing
        
        update_fields.append('updated_at = ?')
        params.append(datetime.now().isoformat())
        params.append(task_id)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = f'UPDATE tasks SET {", ".join(update_fields)} WHERE id = ?'
            cursor.execute(query, params)
            conn.commit()
            
            cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            return self._row_to_dict(cursor.fetchone())
    
    def delete(self, task_id: int) -> bool:
        """Delete a task by ID."""
        existing = self.get_by_id(task_id)
        if not existing:
            return False
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            conn.commit()
            return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get task statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Count by status
            cursor.execute('''
                SELECT status, COUNT(*) as count 
                FROM tasks 
                GROUP BY status
            ''')
            status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Count by priority
            cursor.execute('''
                SELECT priority, COUNT(*) as count 
                FROM tasks 
                GROUP BY priority
            ''')
            priority_counts = {row['priority']: row['count'] for row in cursor.fetchall()}
            
            # Total count
            cursor.execute('SELECT COUNT(*) as total FROM tasks')
            total = cursor.fetchone()['total']
            
            return {
                "total_tasks": total,
                "by_status": {
                    "pending": status_counts.get("pending", 0),
                    "in_progress": status_counts.get("in_progress", 0),
                    "completed": status_counts.get("completed", 0)
                },
                "by_priority": {
                    "low": priority_counts.get("low", 0),
                    "medium": priority_counts.get("medium", 0),
                    "high": priority_counts.get("high", 0)
                }
            }
    
    def health_check(self) -> bool:
        """Check if database is accessible."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                return True
        except Exception:
            return False


# Global repository instance (can be overridden for testing)
_repository: Optional[TaskRepositoryInterface] = None


def get_repository() -> TaskRepositoryInterface:
    """Get or create the task repository instance."""
    global _repository
    if _repository is None:
        _repository = SQLiteTaskRepository()
    return _repository


def set_repository(repo: TaskRepositoryInterface) -> None:
    """Set a custom repository (useful for testing)."""
    global _repository
    _repository = repo


def reset_repository() -> None:
    """Reset the repository instance."""
    global _repository
    _repository = None
