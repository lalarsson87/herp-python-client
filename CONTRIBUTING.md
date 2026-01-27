# Contributing to HERP-Notion Integration

Thank you for your interest in contributing to the HERP-Notion Integration project! This document provides guidelines for contributing to the codebase.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project follows Belong Inc's core values:
- **Be Honest (誠実であれ)**: Transparent communication and integrity
- **Be United (一丸となれ)**: Collaborative problem-solving
- **Make a Contribution (貢献しよう)**: Go beyond assigned responsibilities

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- HERP API credentials
- Notion API credentials

### Setup

1. Clone the repository:
```bash
git clone https://github.com/belong-inc/herp-notion-integration.git
cd herp-notion-integration/development/herp
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements-dev.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. Install pre-commit hooks:
```bash
pre-commit install
```

## Development Workflow

### Domain-Driven Design

This project follows domain-driven design (DDD) principles:

```
src/
├── domains/          # Business domains
│   ├── candidates/   # Candidate management
│   ├── sync/         # Synchronization logic
│   ├── notion/       # Notion-specific operations
│   └── user_activity/# User activity tracking
└── core/             # Shared infrastructure
    ├── herp/         # HERP API client
    ├── notion/       # Notion API client
    ├── cache/        # Caching layer
    ├── errors/       # Error handling
    └── utils/        # Utilities
```

### Where to Add Code

- **Business logic**: Add to appropriate domain (e.g., `domains/candidates/`)
- **API clients**: Add to `core/herp/` or `core/notion/`
- **Utilities**: Add to `core/utils/`
- **Scripts**: Add to `scripts/` for executable entry points

## Coding Standards

### Design Principles (from HitoHana Guideline)

1. **Searchable Naming**: Use grep-friendly names
   ```python
   # Good
   def calculate_candidate_score(profile: CandidateProfile) -> float:
       ...

   # Bad (too generic)
   def calc(data):
       ...
   ```

2. **Transaction Management**: Never make external API calls within database transactions
   ```python
   # Good
   response = herp_client.get_candidacy(id)  # API call outside transaction
   with db.transaction():
       candidate.update(response)

   # Bad
   with db.transaction():
       response = herp_client.get_candidacy(id)  # DON'T DO THIS
       candidate.update(response)
   ```

3. **REST API Design**: Follow OpenAPI specifications and REST principles

### Python Style

- **Formatting**: Black (line length: 88)
- **Import sorting**: isort (profile: black)
- **Linting**: flake8
- **Type hints**: Use type hints for all public functions
- **Docstrings**: Google-style docstrings

Example:
```python
from typing import Optional, List
from .models import Candidate

def analyze_candidate_profile(
    candidate_id: str,
    include_timeline: bool = True
) -> Optional[CandidateAnalysis]:
    """
    Analyze candidate profile using AI.

    Args:
        candidate_id: HERP candidacy ID
        include_timeline: Whether to include timeline analysis

    Returns:
        Candidate analysis result, or None if candidate not found

    Raises:
        HerpAPIError: If HERP API request fails
        ValidationError: If candidate data is invalid
    """
    ...
```

### Logging

Use structured logging (not print statements):

```python
from src.core.utils.logging import get_logger

logger = get_logger(__name__)

# Good
logger.info("syncing_candidate", candidate_id=candidate_id, status="in_progress")

# Bad
print(f"Syncing candidate {candidate_id}")
```

### Error Handling

Use the error classification module:

```python
from src.core.errors import classify_error, smart_retry

@smart_retry(max_attempts=3)
def fetch_candidate(candidate_id: str):
    try:
        return herp_client.get_candidacy(candidate_id)
    except HerpAPIError as e:
        error_info = classify_error(e)
        if error_info.category == ErrorCategory.PERMANENT:
            raise  # Don't retry permanent errors
        raise  # Retry transient errors
```

## Testing Guidelines

### Test Coverage

- Aim for >80% code coverage
- 100% coverage for critical paths
- All new features must include tests

### Test Structure

```
tests/
├── unit/           # Unit tests (isolated, mocked dependencies)
├── integration/    # Integration tests (mocked APIs)
├── e2e/            # End-to-end tests (real workflows)
└── fixtures/       # Test data and mocks
```

### Writing Tests

```python
import pytest
from unittest.mock import Mock, patch
from src.domains.sync.services.full_sync import FullSyncService

def test_sync_candidate_success():
    """Test successful candidate synchronization"""
    # Arrange
    herp_client = Mock()
    notion_client = Mock()
    service = FullSyncService(herp_client, notion_client)

    # Act
    result = service.sync_candidate("test-id")

    # Assert
    assert result.success is True
    herp_client.get_candidacy.assert_called_once_with("test-id")
```

### Running Tests

```bash
# All tests
pytest tests/

# Specific test suite
pytest tests/unit/

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific test file
pytest tests/unit/core/cache/test_cache_manager.py

# Specific test
pytest tests/unit/core/cache/test_cache_manager.py::test_cache_hit
```

## Commit Guidelines

### Commit Message Format

Follow conventional commits:

```
<type>(<scope>): <subject>

<body>

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `perf`: Performance improvements
- `chore`: Maintenance tasks

### Examples

```
feat(cache): add TTL-based cache manager

Implement memory-based L1 caching layer to reduce API calls.
Includes cache statistics and metrics tracking.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
fix(sync): resolve race condition in batch sync

Fix concurrent update issue when syncing multiple candidates
simultaneously. Add proper locking mechanism.

Fixes #123

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

## Pull Request Process

### Before Submitting

1. **Run pre-commit hooks**:
   ```bash
   pre-commit run --all-files
   ```

2. **Run tests**:
   ```bash
   pytest tests/ --cov=src
   ```

3. **Update documentation**:
   - Update README.md if needed
   - Update CHANGELOG.md
   - Add docstrings to new functions

4. **Check CI pipeline**: Ensure all checks pass locally

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing locally

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests provide adequate coverage
```

### Review Process

1. Submit PR with clear description
2. Address reviewer feedback
3. Ensure CI pipeline passes
4. Obtain approval from maintainer
5. Squash and merge

## Questions?

- **Technical questions**: Open a GitHub issue
- **Security concerns**: See SECURITY.md
- **General questions**: Contact the engineering team

Thank you for contributing! 🎉
