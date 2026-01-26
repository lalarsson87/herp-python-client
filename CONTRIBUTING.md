# Contributing to HERP Python Client

Thank you for considering contributing to the HERP Python Client! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help make this project accessible to all skill levels

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- GitHub account

### Setup Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/herp-python-client.git
cd herp-python-client

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or a bugfix branch
git checkout -b fix/issue-number-description
```

## Development Workflow

### 1. Code Style

We use strict code formatting tools:

```bash
# Format code with black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Lint with flake8
flake8 src/ tests/ --max-line-length=100

# Type check with mypy
mypy src/
```

**Code Style Guidelines**:

- Maximum line length: 100 characters
- Use type hints for all function signatures
- Use TypedDict for API response types
- Follow PEP 8 conventions
- Write docstrings for all public APIs

### 2. Testing

Write tests for all new code:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/core/herp/test_client.py

# Run tests matching a pattern
pytest -k "test_batch"
```

**Testing Guidelines**:

- Aim for 80%+ code coverage
- Write unit tests for all new functions
- Add integration tests for new features
- Mock external API calls in tests
- Use descriptive test names: `test_<what>_<condition>_<expected>`

### 3. Documentation

Update documentation for all changes:

```bash
# Check documentation
python scripts/check_docs.py

# Spell check and link validation
markdownlint '**/*.md'
```

**Documentation Guidelines**:

- Update relevant docs/ files
- Add code examples for new features
- Include docstrings with examples
- Update README.md if adding features
- Keep documentation clear and concise

### 4. Pre-commit Hooks

Run pre-commit hooks before committing:

```bash
# Run all hooks
pre-commit run --all-files

# Run specific hook
pre-commit run black
pre-commit run check-docs
```

## Pull Request Process

### 1. Before Creating PR

- [ ] Code is formatted (black, isort)
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] Pre-commit hooks pass
- [ ] Branch is rebased on latest main

### 2. Creating the PR

```bash
# Push your branch
git push origin feature/your-feature-name

# Create PR on GitHub
gh pr create --title "Add feature X" --body "Description of changes"
```

**PR Title Format**:

- `feat: Add Query DSL support for complex filters`
- `fix: Resolve race condition in async batch client`
- `docs: Update webhooks integration guide`
- `test: Add coverage for event sourcing`
- `refactor: Simplify error classification logic`

**PR Description Should Include**:

- What changed and why
- Related issue numbers (#123)
- Testing performed
- Breaking changes (if any)
- Documentation updates

### 3. PR Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (for notable changes)
- [ ] CI checks passing
- [ ] No merge conflicts
- [ ] Reviewed own code

### 4. Review Process

- Maintainers will review within 2-3 business days
- Address review comments
- Push updates to the same branch
- Request re-review when ready

### 5. After Merge

- Delete your branch
- Pull latest main
- Close related issues

## Code Organization

### Directory Structure

```
src/core/herp/
├── client.py              # Main client facade
├── base_client.py         # HTTP client base
├── async_base_client.py   # Async HTTP client
├── types.py               # TypedDict definitions
├── candidates.py          # Candidacy operations
├── contacts.py            # Contact operations
├── files.py               # File operations
├── evaluations.py         # Evaluation operations
├── assignments.py         # Assignment operations
├── timeline.py            # Timeline operations
├── master_data.py         # Master data operations
├── builders.py            # Builder patterns
├── mixins.py              # Reusable mixins
├── query_dsl.py           # Query DSL
├── pagination.py          # Pagination helpers
├── batch_client.py        # Batch operations
├── async_batch_client.py  # Async batch operations
├── events/                # Event sourcing
│   ├── events.py
│   ├── event_store.py
│   ├── aggregate.py
│   └── projections.py
└── webhooks/              # Webhook integration
    ├── verifier.py
    ├── handlers.py
    └── router.py
```

### Adding New Features

**For new API endpoints**:

1. Add types to `types.py`
2. Create new module in `src/core/herp/`
3. Use mixins for common patterns
4. Add to `client.py` facade
5. Write tests in `tests/unit/core/herp/`
6. Update documentation

**For new async support**:

1. Create `async_*.py` version
2. Use `httpx` for HTTP
3. Add `async`/`await` keywords
4. Export from `async_client.py`
5. Test with `pytest-asyncio`

## Architecture Patterns

### Type Safety

Always use TypedDict for API responses:

```python
from typing import TypedDict, NotRequired

class CandidacyResponse(TypedDict):
    id: str
    name: str
    email: str
    phone: NotRequired[str]
```

### Builder Pattern

Use builders for complex object construction:

```python
class CandidacyBuilder:
    def with_name(self, name: str) -> "CandidacyBuilder":
        self._data["name"] = name
        return self

    def build(self) -> Dict[str, Any]:
        self._validate()
        return self._data
```

### Mixins

Extract common patterns into mixins:

```python
class BatchFetchMixin:
    def _batch_fetch(
        self,
        ids: List[str],
        fetch_function: Callable,
        max_workers: int = 10
    ) -> Dict[str, Any]:
        # Implementation
        pass
```

### Error Handling

Use pattern matching for errors (Python 3.10+):

```python
match exception:
    case HerpRateLimitError():
        return (ErrorSeverity.TRANSIENT, ErrorCategory.RATE_LIMIT)
    case HerpAuthenticationError():
        return (ErrorSeverity.PERMANENT, ErrorCategory.AUTHENTICATION)
    case _:
        return (ErrorSeverity.UNKNOWN, ErrorCategory.UNKNOWN)
```

## Common Tasks

### Adding a New API Endpoint

```python
# 1. Add type definition (types.py)
class NewEndpointResponse(TypedDict):
    id: str
    field: str

# 2. Create API module (new_endpoint.py)
class NewEndpointAPI:
    def __init__(self, client: HerpBaseClient):
        self.client = client

    def get(self, id: str) -> NewEndpointResponse:
        return self.client.get(f"/v1/new-endpoint/{id}")

# 3. Add to main client (client.py)
self.new_endpoint = NewEndpointAPI(self._base_client)

# 4. Add tests (tests/unit/core/herp/test_new_endpoint.py)
def test_new_endpoint_get():
    # Test implementation
    pass
```

### Adding Documentation

```python
# Add comprehensive docstrings
def complex_function(param: str, option: int = 10) -> Dict[str, Any]:
    """
    Short description of function.

    Longer description with details about what this function does,
    when to use it, and any important considerations.

    Args:
        param: Description of param
        option: Description of option (default: 10)

    Returns:
        Dictionary containing results with keys:
        - field1: Description
        - field2: Description

    Raises:
        ValueError: When param is invalid
        HerpAPIError: When API request fails

    Example:
        >>> result = complex_function("test", option=20)
        >>> print(result["field1"])
        'value'
    """
    pass
```

## Reporting Issues

### Bug Reports

Include:

- Python version
- Library version
- Minimal reproduction code
- Expected vs actual behavior
- Full error traceback

### Feature Requests

Include:

- Use case description
- Proposed API design
- Example code
- Benefits and trade-offs

## Questions?

- **GitHub Discussions**: For general questions
- **GitHub Issues**: For bugs and features
- **Email**: For security concerns

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to HERP Python Client! 🚀
