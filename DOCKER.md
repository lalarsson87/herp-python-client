# Docker Development Environment

> Isolated, reproducible development and testing environment for HERP-Notion integration

## Overview

The Docker setup provides:
- **Python 3.12** development environment with all dependencies
- **PostgreSQL 16** for integration testing
- **Mock API servers** for isolated testing (HERP and Notion)
- **Volume mounts** for live code reloading
- **Network isolation** for service communication

## Quick Start

### 1. Create Environment File

```bash
# Copy example to .env
cp .env.example .env

# Edit .env with your API keys
vim .env
```

### 2. Build and Start Services

```bash
# Build Docker images
docker-compose build

# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

### 3. Run Tests

```bash
# Run all tests in Docker
docker-compose run herp-dev pytest tests/ -v

# Run specific test file
docker-compose run herp-dev pytest tests/e2e/test_candidate_analysis.py -v

# Run with coverage
docker-compose run herp-dev pytest tests/ --cov=src --cov-report=html
```

### 4. Interactive Development

```bash
# Start interactive Python shell
docker-compose run herp-dev python

# Run specific script
docker-compose run herp-dev python scripts/test-herp-api.py

# Open bash shell in container
docker-compose run herp-dev bash
```

### 5. Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

## Services

### 1. herp-dev (Main Development Container)

**Purpose**: Primary development and testing environment

**Includes**:
- Python 3.12
- All Python dependencies from requirements.txt and requirements-dev.txt
- Git, curl, build-essential
- PostgreSQL client

**Usage**:
```bash
# Run tests
docker-compose run herp-dev pytest

# Run script
docker-compose run herp-dev python scripts/sync-herp-notion-full.py

# Interactive shell
docker-compose run herp-dev bash
```

### 2. postgres (PostgreSQL Database)

**Purpose**: Database for integration testing

**Configuration**:
- User: `herp_test`
- Password: `herp_test_password`
- Database: `herp_test`
- Port: 5432 (mapped to host)

**Access from Host**:
```bash
psql -h localhost -U herp_test -d herp_test
```

**Health Check**: Automatically verifies database is ready before dependent services start

### 3. herp-mock-api (Mock HERP API Server)

**Purpose**: Isolated testing without hitting real HERP API

**Configuration**:
- Port: 8001 (mapped to host)
- Returns fixture data from `tests/fixtures/herp_responses.py`

**Usage**:
```bash
# Start mock API
docker-compose up -d herp-mock-api

# Test from host
curl http://localhost:8001/v1/candidacies

# Use in tests
HERP_API_BASE_URL=http://herp-mock-api:8001 pytest
```

### 4. notion-mock-api (Mock Notion API Server)

**Purpose**: Isolated testing without hitting real Notion API

**Configuration**:
- Port: 8002 (mapped to host)
- Returns fixture data from `tests/fixtures/notion_responses.py`

**Usage**:
```bash
# Start mock API
docker-compose up -d notion-mock-api

# Test from host
curl http://localhost:8002/v1/databases/test-db-id/query

# Use in tests
NOTION_API_BASE_URL=http://notion-mock-api:8002 pytest
```

## Common Workflows

### Development Workflow

```bash
# 1. Start services
docker-compose up -d

# 2. Edit code on host (changes reflect in container via volume mount)
vim src/core/herp/client.py

# 3. Run tests to verify changes
docker-compose run herp-dev pytest tests/unit/test_herp_client.py -v

# 4. Run full test suite
docker-compose run herp-dev pytest tests/ -v

# 5. Stop services when done
docker-compose down
```

### Testing Workflow (Isolated)

```bash
# Start only test dependencies (no real APIs)
docker-compose up -d postgres herp-mock-api notion-mock-api

# Run tests against mock APIs
docker-compose run herp-dev \
  env HERP_API_BASE_URL=http://herp-mock-api:8001 \
      NOTION_API_BASE_URL=http://notion-mock-api:8002 \
  pytest tests/ -v

# No external API calls, fully isolated
```

### Debugging Workflow

```bash
# Start services
docker-compose up -d

# Open interactive shell in dev container
docker-compose run herp-dev bash

# Inside container:
$ python
>>> from src.core.herp import HERPClient
>>> client = HERPClient(api_key="test")
>>> # Debug interactively
```

### Integration Testing Workflow

```bash
# Start all services including database
docker-compose up -d

# Run integration tests
docker-compose run herp-dev pytest tests/integration/ -v

# Check database state
docker-compose exec postgres psql -U herp_test -d herp_test -c "SELECT * FROM test_table;"
```

## Volume Mounts

### Source Code (Live Reload)
```yaml
volumes:
  - ../../development/herp:/app/development/herp
  - ../../knowledge-base:/app/knowledge-base
```
- Changes on host immediately visible in container
- No rebuild needed for code changes

### Data Persistence
```yaml
volumes:
  - herp-data:/app/development/herp/data
```
- Candidate files, logs persist across container restarts
- Independent of host filesystem

### PostgreSQL Data
```yaml
volumes:
  - postgres-data:/var/lib/postgresql/data
```
- Database persists across restarts
- Remove with `docker-compose down -v` for clean state

## Environment Variables

**Set in `.env` file** (not committed to git):

### Required
```bash
HERP_API_KEY=herp_xxx           # Your HERP API key
NOTION_API_KEY=secret_xxx       # Your Notion integration token
NOTION_CANDIDATES_DB_ID=1f8c... # Notion database ID
```

### Optional
```bash
HERP_API_BASE_URL=...           # Override API endpoint
LOG_LEVEL=DEBUG                 # Increase logging verbosity
USE_MOCK_APIS=true              # Force mock APIs for all tests
```

## Troubleshooting

### Issue: "Permission denied" errors

**Cause**: Volume mount permissions mismatch

**Solution**:
```bash
# Fix data directory permissions
sudo chown -R $(whoami):$(whoami) data/

# Or run container as root (not recommended)
docker-compose run --user root herp-dev bash
```

### Issue: "Import error: No module named 'src'"

**Cause**: PYTHONPATH not set correctly

**Solution**:
```bash
# Already set in docker-compose.yml, but verify:
docker-compose run herp-dev env | grep PYTHONPATH

# Should show: PYTHONPATH=/app/src:/app
```

### Issue: Tests fail with connection errors

**Cause**: Services not started or unhealthy

**Solution**:
```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs herp-dev
docker-compose logs postgres

# Restart services
docker-compose restart
```

### Issue: "Database does not exist"

**Cause**: PostgreSQL not initialized

**Solution**:
```bash
# Recreate database volume
docker-compose down -v
docker-compose up -d postgres

# Wait for health check
docker-compose ps

# Should show postgres as "healthy"
```

### Issue: Docker build fails

**Cause**: Missing dependencies or network issues

**Solution**:
```bash
# Rebuild without cache
docker-compose build --no-cache

# Or rebuild specific service
docker-compose build --no-cache herp-dev
```

## Performance Optimization

### Faster Builds
```dockerfile
# In Dockerfile, copy requirements first (layer caching)
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements.txt && pip install -r requirements-dev.txt

# Then copy source code (changes less frequently)
COPY . .
```

### Faster Test Execution
```bash
# Run tests in parallel (pytest-xdist)
docker-compose run herp-dev pytest tests/ -n auto -v

# Run only changed tests (pytest-testmon)
docker-compose run herp-dev pytest tests/ --testmon -v
```

### Reduce Image Size
```dockerfile
# Use multi-stage builds (future enhancement)
FROM python:3.12-slim AS base
FROM base AS builder
FROM base AS runtime
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/docker-test.yml
name: Docker Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker images
        run: |
          cd development/herp
          docker-compose build

      - name: Run tests
        run: |
          cd development/herp
          docker-compose run herp-dev pytest tests/ -v

      - name: Cleanup
        run: |
          cd development/herp
          docker-compose down -v
```

## Security Best Practices

### 1. Never Commit .env
```bash
# Already in .gitignore
echo ".env" >> .gitignore
```

### 2. Use Secrets Management
```bash
# In production, use Docker secrets
docker secret create herp_api_key herp_api_key.txt
```

### 3. Run as Non-Root User
```dockerfile
# Add to Dockerfile (future enhancement)
RUN useradd -m -u 1000 herp
USER herp
```

### 4. Scan Images for Vulnerabilities
```bash
# Use trivy or similar
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest image herp-dev:latest
```

## Cleanup

### Remove All Containers and Volumes
```bash
docker-compose down -v
```

### Remove All Images
```bash
docker-compose down --rmi all
```

### Full Cleanup (Nuclear Option)
```bash
# Stop all containers
docker-compose down -v --rmi all

# Remove all unused Docker data
docker system prune -a --volumes
```

## Next Steps

1. **Implement Mock API Servers**: Create `tests/mocks/herp_api_server.py` and `tests/mocks/notion_api_server.py`
2. **Add Pre-Commit Hooks**: Lint and test before commit using Docker
3. **Create Development Scripts**: `./scripts/test.sh`, `./scripts/lint.sh` that wrap Docker commands
4. **Multi-Stage Builds**: Separate builder and runtime stages for smaller images
5. **Docker Compose Profiles**: Different profiles for dev, test, prod

## Related Documentation

- [HERP Project README](./README.md)
- [Testing Guide](./tests/README.md)
- [Source Code Architecture](./src/README.md)
- [CI/CD Workflow](../../.github/workflows/ci.yml)

---

**Last Updated**: January 24, 2026
**Maintainer**: Lars Larsson (@larsson-l)
**Status**: Active development
