# Integration Tests

Integration tests for HERP Python Client with VCR cassette recording/playback.

## Overview

Integration tests use **pytest-vcr** to record real HTTP interactions with the HERP API. Recorded interactions (cassettes) are replayed on subsequent runs, allowing tests to run without API credentials.

## Installation

```bash
# Install with integration test dependencies
pip install -e ".[dev]"
pip install pytest-vcr vcrpy

# Or install all test dependencies
pip install pytest pytest-vcr vcrpy pytest-cov
```

## Running Tests

### Run All Tests (Excludes Integration by Default)

```bash
pytest tests/
```

### Run Integration Tests

```bash
# Run with existing cassettes (no API key needed)
pytest tests/integration/ --integration -v

# Run all tests including integration
pytest --integration -v
```

### Record New Cassettes

```bash
# Set API key and record
export HERP_API_KEY=your_api_key_here
pytest tests/integration/ --integration --record-vcr -v
```

## How VCR Works

### First Run (Recording)
1. Set `HERP_API_KEY` environment variable
2. Run tests with `--integration` flag
3. VCR records HTTP requests/responses
4. Cassettes saved to `tests/integration/fixtures/cassettes/`

### Subsequent Runs (Playback)
1. No API key required
2. VCR replays recorded responses
3. Fast, deterministic tests
4. No network calls

## Test Organization

```
tests/integration/
├── conftest.py                          # Shared configuration
├── README.md                            # This file
├── fixtures/
│   └── cassettes/                       # Recorded HTTP interactions
│       ├── test_list_candidacies.yaml
│       ├── test_get_candidacy.yaml
│       └── ...
└── herp/
    ├── test_candidacies_integration.py  # Candidacy endpoints
    ├── test_contacts_integration.py     # Contact/interview endpoints
    └── ...
```

## Writing Integration Tests

### Basic Test with VCR

```python
import pytest

pytest_plugins = ["pytest_vcr"]

@pytest.mark.integration
@pytest.mark.vcr()
def test_list_candidacies(herp_client):
    """Test listing candidacies"""
    candidacies = herp_client.candidacies.list(limit=5)
    
    assert isinstance(candidacies, list)
    assert len(candidacies) <= 5
```

### Skipping Write Tests

Tests that modify data should be skipped by default:

```python
@pytest.mark.integration
@pytest.mark.vcr()
@pytest.mark.skip(reason="Requires write permissions")
def test_create_candidacy(herp_client):
    """Test creating candidacy (run manually)"""
    candidacy = herp_client.candidacies.create(data)
    assert "id" in candidacy
```

### Testing Error Handling

```python
@pytest.mark.integration
@pytest.mark.vcr()
def test_error_not_found(herp_client):
    """Test 404 error handling"""
    from src.core.errors.exceptions import HerpNotFoundError
    
    with pytest.raises(HerpNotFoundError):
        herp_client.candidacies.get("nonexistent_id")
```

## VCR Configuration

Configured in `conftest.py`:

```python
@pytest.fixture(scope="module")
def vcr_config():
    return {
        "filter_headers": ["authorization", "x-api-key"],  # Redact sensitive headers
        "record_mode": "once",  # Record once, replay thereafter
        "match_on": ["method", "scheme", "host", "port", "path", "query"],
        "cassette_library_dir": "tests/integration/fixtures/cassettes",
    }
```

### Record Modes

- **once** (default): Record if cassette doesn't exist, replay otherwise
- **new_episodes**: Record new interactions, replay existing
- **all**: Always record (overwrites cassettes)
- **none**: Only replay, fail if cassette missing

## Environment Variables

```bash
# API Configuration
export HERP_API_KEY=your_api_key           # Required for recording
export HERP_BASE_URL=https://...           # Optional (uses default)

# VCR Configuration
export VCR_MODE=once                        # Record mode (once, new_episodes, all)
```

## Best Practices

### 1. Use VCR for Read Operations
✅ List, get, search operations
❌ Create, update, delete operations (unless necessary)

### 2. Keep Cassettes in Version Control
- Commit cassettes to git
- Allows tests without API access
- Documents API behavior

### 3. Refresh Cassettes Periodically
```bash
# Delete old cassettes
rm tests/integration/fixtures/cassettes/*.yaml

# Re-record with current API
export HERP_API_KEY=your_key
pytest tests/integration/ --integration --record-vcr
```

### 4. Test Schema Validation
```python
def test_candidacy_schema(herp_client):
    candidacy = herp_client.candidacies.get("cand_123")
    
    # Verify required fields
    assert isinstance(candidacy["id"], str)
    assert isinstance(candidacy["name"], str)
    assert candidacy["status"] in ["active", "hired", "terminated"]
```

### 5. Handle Pagination
```python
def test_pagination(herp_client):
    page1 = herp_client.candidacies.list(limit=2, offset=0)
    page2 = herp_client.candidacies.list(limit=2, offset=2)
    
    if page1 and page2:
        assert page1[0]["id"] != page2[0]["id"]
```

## Troubleshooting

### "No cassette found"
- Run with `--record-vcr` to create cassettes
- Check cassette directory path
- Verify test name matches cassette filename

### "API key required"
- Set `HERP_API_KEY` environment variable
- Use `--record-vcr` to re-record cassettes

### "Request doesn't match cassette"
- Query parameters or headers changed
- Re-record cassette with `--record-vcr`
- Check VCR match_on configuration

### Tests fail in CI
- Ensure cassettes are committed to git
- Don't use `--record-vcr` in CI
- Skip write tests by default

## CI/CD Integration

```yaml
# .github/workflows/test.yml
- name: Run integration tests
  run: |
    pytest tests/integration/ --integration -v
  # No API key needed - uses cassettes
```

## Security

**Never commit API keys!**

VCR automatically filters sensitive headers:
- `authorization`
- `x-api-key`

Cassettes contain:
- Request method, URL, body
- Response status, headers, body
- **No sensitive authentication data**

## Further Reading

- [pytest-vcr Documentation](https://pytest-vcr.readthedocs.io/)
- [VCR.py Documentation](https://vcrpy.readthedocs.io/)
- [HERP API Documentation](https://herp.cloud/docs/api)
