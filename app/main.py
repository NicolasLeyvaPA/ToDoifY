"""
Task Manager API - Main Application Module
A RESTful API for managing tasks with DevOps best practices.
"""

import time
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings, get_settings
from app.routes import router as task_router
from app.database import get_repository, reset_repository
from app.metrics import get_metrics, track_request
from app.models import HealthStatus


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track request metrics."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and track metrics."""
        metrics = get_metrics()
        
        # Track active requests
        metrics.active_requests.inc()
        
        # Record start time
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise
        finally:
            # Calculate duration
            duration = time.time() - start_time
            
            # Track metrics
            path = request.url.path
            method = request.method
            track_request(method, path, status_code, duration)
            
            # Decrement active requests
            metrics.active_requests.dec()
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    # Startup
    repo = get_repository()
    yield
    # Shutdown
    reset_repository()


def create_app() -> FastAPI:
    """Application factory function."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="A RESTful API for managing tasks with DevOps best practices",
        version=settings.APP_VERSION,
        lifespan=lifespan
    )
    
    # Add metrics middleware
    app.add_middleware(MetricsMiddleware)
    
    # Include task routes
    app.include_router(task_router)
    
    # Mount static files
    try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
    except RuntimeError:
        # Static directory doesn't exist (e.g., in tests)
        pass
    
    # Root endpoint - serve the frontend
    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Serve the main HTML page."""
        try:
            return FileResponse("templates/index.html")
        except FileNotFoundError:
            return HTMLResponse(
                content="<h1>Task Manager API</h1><p>Visit /docs for API documentation</p>",
                status_code=200
            )
    
    # Health check endpoint
    @app.get("/health", response_model=HealthStatus)
    async def health_check():
        """
        Health check endpoint for monitoring.
        
        Returns application status, version, and database connectivity.
        """
        repo = get_repository()
        db_healthy = repo.health_check()
        metrics = get_metrics()
        
        return HealthStatus(
            status="healthy" if db_healthy else "unhealthy",
            timestamp=datetime.now().isoformat(),
            version=settings.APP_VERSION,
            database="connected" if db_healthy else "disconnected",
            uptime_seconds=metrics.get_uptime()
        )
    
    # Metrics endpoint (Prometheus format)
    @app.get("/metrics", response_class=PlainTextResponse)
    async def metrics_endpoint():
        """
        Expose Prometheus-compatible metrics.
        
        Returns metrics for request count, latency, and errors.
        """
        metrics = get_metrics()
        return metrics.to_prometheus_format()
    
    # JSON metrics endpoint
    @app.get("/metrics/json")
    async def metrics_json():
        """
        Expose metrics in JSON format.
        
        Returns detailed metrics including histograms.
        """
        metrics = get_metrics()
        return metrics.collect_all()
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
