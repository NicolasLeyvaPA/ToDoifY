"""
Integration tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for /health endpoint."""
    
    def test_health_check_returns_status(self, client: TestClient):
        """Test health check returns healthy status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert data["database"] == "connected"
        assert "uptime_seconds" in data
    
    def test_health_check_version(self, client: TestClient):
        """Test health check returns correct version."""
        response = client.get("/health")
        data = response.json()
        
        assert data["version"] == "2.0.0"


class TestMetricsEndpoint:
    """Tests for /metrics endpoint."""
    
    def test_metrics_prometheus_format(self, client: TestClient):
        """Test metrics endpoint returns Prometheus format."""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        
        content = response.text
        assert "# HELP" in content
        assert "# TYPE" in content
        assert "http_requests_total" in content
    
    def test_metrics_json_format(self, client: TestClient):
        """Test metrics JSON endpoint."""
        response = client.get("/metrics/json")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "uptime_seconds" in data
        assert "metrics" in data


class TestCreateTask:
    """Tests for POST /api/tasks endpoint."""
    
    def test_create_task_full(self, client: TestClient, sample_task_data: dict):
        """Test creating a task with all fields."""
        response = client.post("/api/tasks", json=sample_task_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_task_data["title"]
        assert data["description"] == sample_task_data["description"]
        assert data["priority"] == sample_task_data["priority"]
        assert data["due_date"] == sample_task_data["due_date"]
        assert data["status"] == "pending"
        assert data["id"] is not None
    
    def test_create_task_minimal(self, client: TestClient, sample_task_minimal: dict):
        """Test creating a task with minimal fields."""
        response = client.post("/api/tasks", json=sample_task_minimal)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Task"
        assert data["priority"] == "medium"
        assert data["status"] == "pending"
    
    def test_create_task_invalid_priority(self, client: TestClient):
        """Test creating task with invalid priority."""
        response = client.post("/api/tasks", json={
            "title": "Test",
            "priority": "invalid"
        })
        
        assert response.status_code == 422
    
    def test_create_task_empty_title(self, client: TestClient):
        """Test creating task with empty title."""
        response = client.post("/api/tasks", json={"title": ""})
        
        assert response.status_code == 422
    
    def test_create_task_missing_title(self, client: TestClient):
        """Test creating task without title."""
        response = client.post("/api/tasks", json={"description": "No title"})
        
        assert response.status_code == 422
    
    def test_create_task_invalid_date(self, client: TestClient):
        """Test creating task with invalid date."""
        response = client.post("/api/tasks", json={
            "title": "Test",
            "due_date": "invalid-date"
        })
        
        assert response.status_code == 422


class TestGetTasks:
    """Tests for GET /api/tasks endpoint."""
    
    def test_get_tasks_empty(self, client: TestClient):
        """Test getting tasks when none exist."""
        response = client.get("/api/tasks")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["tasks"] == []
    
    def test_get_tasks_with_data(self, client: TestClient):
        """Test getting tasks."""
        # Create tasks
        client.post("/api/tasks", json={"title": "Task 1"})
        client.post("/api/tasks", json={"title": "Task 2"})
        
        response = client.get("/api/tasks")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["tasks"]) == 2
    
    def test_get_tasks_filter_by_status(self, client: TestClient):
        """Test filtering tasks by status."""
        client.post("/api/tasks", json={"title": "Pending"})
        
        response = client.get("/api/tasks?status=pending")
        
        assert response.status_code == 200
        data = response.json()
        assert all(t["status"] == "pending" for t in data["tasks"])
    
    def test_get_tasks_filter_by_priority(self, client: TestClient):
        """Test filtering tasks by priority."""
        client.post("/api/tasks", json={"title": "High", "priority": "high"})
        client.post("/api/tasks", json={"title": "Low", "priority": "low"})
        
        response = client.get("/api/tasks?priority=high")
        
        assert response.status_code == 200
        data = response.json()
        assert all(t["priority"] == "high" for t in data["tasks"])
    
    def test_get_tasks_search(self, client: TestClient):
        """Test searching tasks."""
        client.post("/api/tasks", json={"title": "Buy groceries"})
        client.post("/api/tasks", json={"title": "Clean house"})
        
        response = client.get("/api/tasks?search=groceries")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
    
    def test_get_tasks_pagination(self, client: TestClient):
        """Test pagination."""
        for i in range(5):
            client.post("/api/tasks", json={"title": f"Task {i}"})
        
        response = client.get("/api/tasks?limit=2&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["tasks"]) == 2


class TestGetTask:
    """Tests for GET /api/tasks/{id} endpoint."""
    
    def test_get_task_exists(self, client: TestClient):
        """Test getting an existing task."""
        create_response = client.post("/api/tasks", json={"title": "Test"})
        task_id = create_response.json()["id"]
        
        response = client.get(f"/api/tasks/{task_id}")
        
        assert response.status_code == 200
        assert response.json()["id"] == task_id
    
    def test_get_task_not_found(self, client: TestClient):
        """Test getting a non-existent task."""
        response = client.get("/api/tasks/99999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUpdateTask:
    """Tests for PUT /api/tasks/{id} endpoint."""
    
    def test_update_task_title(self, client: TestClient):
        """Test updating task title."""
        create_response = client.post("/api/tasks", json={"title": "Original"})
        task_id = create_response.json()["id"]
        
        response = client.put(f"/api/tasks/{task_id}", json={"title": "Updated"})
        
        assert response.status_code == 200
        assert response.json()["title"] == "Updated"
    
    def test_update_task_status(self, client: TestClient):
        """Test updating task status."""
        create_response = client.post("/api/tasks", json={"title": "Test"})
        task_id = create_response.json()["id"]
        
        response = client.put(f"/api/tasks/{task_id}", json={"status": "completed"})
        
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
    
    def test_update_task_multiple_fields(self, client: TestClient):
        """Test updating multiple fields."""
        create_response = client.post("/api/tasks", json={"title": "Test"})
        task_id = create_response.json()["id"]
        
        update_data = {
            "title": "Updated",
            "description": "New desc",
            "priority": "high",
            "status": "in_progress"
        }
        response = client.put(f"/api/tasks/{task_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"
        assert data["description"] == "New desc"
        assert data["priority"] == "high"
        assert data["status"] == "in_progress"
    
    def test_update_task_not_found(self, client: TestClient):
        """Test updating a non-existent task."""
        response = client.put("/api/tasks/99999", json={"title": "Test"})
        
        assert response.status_code == 404
    
    def test_update_task_no_changes(self, client: TestClient):
        """Test updating with no changes."""
        create_response = client.post("/api/tasks", json={"title": "Test"})
        task_id = create_response.json()["id"]
        
        response = client.put(f"/api/tasks/{task_id}", json={})
        
        assert response.status_code == 200


class TestDeleteTask:
    """Tests for DELETE /api/tasks/{id} endpoint."""
    
    def test_delete_task_exists(self, client: TestClient):
        """Test deleting an existing task."""
        create_response = client.post("/api/tasks", json={"title": "To Delete"})
        task_id = create_response.json()["id"]
        
        response = client.delete(f"/api/tasks/{task_id}")
        
        assert response.status_code == 204
        
        # Verify deletion
        get_response = client.get(f"/api/tasks/{task_id}")
        assert get_response.status_code == 404
    
    def test_delete_task_not_found(self, client: TestClient):
        """Test deleting a non-existent task."""
        response = client.delete("/api/tasks/99999")
        
        assert response.status_code == 404


class TestStatistics:
    """Tests for GET /api/stats endpoint."""
    
    def test_statistics_empty(self, client: TestClient):
        """Test statistics with no tasks."""
        response = client.get("/api/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_tasks"] == 0
    
    def test_statistics_with_tasks(self, client: TestClient):
        """Test statistics with various tasks."""
        client.post("/api/tasks", json={"title": "T1", "priority": "high"})
        client.post("/api/tasks", json={"title": "T2", "priority": "low"})
        
        # Complete one task
        create_response = client.post("/api/tasks", json={"title": "T3"})
        task_id = create_response.json()["id"]
        client.put(f"/api/tasks/{task_id}", json={"status": "completed"})
        
        response = client.get("/api/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_tasks"] == 3
        assert data["by_status"]["completed"] == 1
        assert data["by_priority"]["high"] == 1


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    def test_root_returns_html(self, client: TestClient):
        """Test root endpoint returns HTML or API info."""
        response = client.get("/")
        
        assert response.status_code == 200


class TestOpenAPIDocumentation:
    """Tests for API documentation endpoints."""
    
    def test_openapi_schema(self, client: TestClient):
        """Test OpenAPI schema is available."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
    
    def test_docs_available(self, client: TestClient):
        """Test Swagger UI is available."""
        response = client.get("/docs")
        
        assert response.status_code == 200
    
    def test_redoc_available(self, client: TestClient):
        """Test ReDoc is available."""
        response = client.get("/redoc")
        
        assert response.status_code == 200
