# ToDoifY v2.0

A RESTful task management application built with Python and FastAPI, featuring DevOps best practices including CI/CD, containerization, monitoring, and comprehensive testing.

## Features

- **Full CRUD Operations**: Create, Read, Update, and Delete tasks
- **Persistent Storage**: SQLite database for data persistence
- **RESTful API**: Well-documented API with OpenAPI/Swagger documentation
- **Modern Web UI**: Responsive frontend with real-time updates
- **Monitoring**: Prometheus metrics and Grafana dashboards
- **Health Checks**: `/health` endpoint for application monitoring
- **Containerization**: Docker and Docker Compose support
- **CI/CD Pipeline**: GitHub Actions for automated testing and deployment
- **High Test Coverage**: >70% code coverage with unit and integration tests

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, Pydantic
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Testing**: pytest, pytest-cov
- **Containerization**: Docker, Docker Compose
- **Monitoring**: Prometheus, Grafana
- **CI/CD**: GitHub Actions

## Project Structure

```
task-manager-v2/
├── app/                          # Application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI application factory
│   ├── config.py                 # Configuration management
│   ├── models.py                 # Pydantic models
│   ├── database.py               # Database repository
│   ├── routes.py                 # API routes
│   └── metrics.py                # Prometheus metrics
├── tests/                        # Test suite
│   ├── conftest.py               # Test fixtures
│   ├── test_api.py               # Integration tests
│   ├── test_models.py            # Model unit tests
│   ├── test_database.py          # Database unit tests
│   ├── test_metrics.py           # Metrics unit tests
│   └── test_config.py            # Config unit tests
├── static/                       # Frontend assets
├── templates/                    # HTML templates
├── monitoring/                   # Monitoring configuration
│   ├── prometheus.yml
│   └── grafana/
├── .github/workflows/            # CI/CD pipeline
│   └── ci-cd.yml
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Multi-container setup
├── requirements.txt              # Python dependencies
├── pytest.ini                    # Test configuration
└── README.md                     # This file
```

## Quick Start

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Docker and Docker Compose (for containerized deployment)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd task-manager-v2
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

5. **Access the application**
   - Web UI: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Metrics: http://localhost:8000/metrics

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run tests with coverage
```bash
pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing
```

### Run specific test files
```bash
pytest tests/test_api.py -v           # Integration tests
pytest tests/test_models.py -v        # Model tests
pytest tests/test_database.py -v      # Database tests
```

### Generate coverage report
```bash
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

## Docker Deployment

### Build and run with Docker
```bash
# Build the image
docker build -t task-manager:latest .

# Run the container
docker run -d -p 8000:8000 --name task-manager task-manager:latest
```

### Run with Docker Compose (includes monitoring)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Access services
- **Application**: http://localhost:8000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Web UI |
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/tasks` | Create task |
| GET | `/api/tasks` | List tasks (with filters) |
| GET | `/api/tasks/{id}` | Get task |
| PUT | `/api/tasks/{id}` | Update task |
| DELETE | `/api/tasks/{id}` | Delete task |
| GET | `/api/stats` | Statistics |

### Query Parameters for GET /api/tasks

- `status`: Filter by status (pending, in_progress, completed)
- `priority`: Filter by priority (low, medium, high)
- `search`: Search in title and description
- `limit`: Maximum results (default: 100)
- `offset`: Pagination offset

### Example API Calls

```bash
# Create a task
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Task", "priority": "high"}'

# Get all tasks
curl "http://localhost:8000/api/tasks"

# Update a task
curl -X PUT "http://localhost:8000/api/tasks/1" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'

# Delete a task
curl -X DELETE "http://localhost:8000/api/tasks/1"

# Health check
curl "http://localhost:8000/health"
```

## CI/CD Pipeline

The GitHub Actions pipeline includes:

1. **Test**: Runs pytest with coverage (fails if <70%)
2. **Lint**: Checks code quality with flake8, black, isort
3. **Build**: Builds Docker image and tests it
4. **Deploy**: Pushes to Docker Hub (main branch only)

### Required Secrets for Deployment

Configure these in GitHub repository settings:
- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub access token

## Monitoring

### Prometheus Metrics

Available at `/metrics`:
- `http_requests_total`: Total HTTP requests (by method, path, status)
- `http_request_duration_seconds`: Request latency histogram
- `http_errors_total`: Total HTTP errors
- `http_active_requests`: Currently active requests

### Grafana Dashboard

The included dashboard shows:
- Total requests and errors
- Request rate over time
- Response time percentiles (p50, p95)
- Error rate by endpoint

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `tasks.db` | SQLite database path |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `DEBUG` | `false` | Debug mode |

## Development

### Code Style

The project follows:
- PEP 8 guidelines
- Black for formatting
- isort for import sorting
- Type hints throughout

### Running Linters

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Check for errors
flake8 app/ tests/
```

## License

MIT License

## Author

Software Development and DevOps Course - Individual Assignment 2
