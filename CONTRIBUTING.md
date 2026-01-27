# Contributing to HERP Python Client

Thank you for your interest in contributing to the HERP Python Client!

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/lalarsson87/herp-python-client.git
cd herp-python-client
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install package in development mode
pip install -e ".[dev]"

# Or install dependencies separately
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. Set Up Pre-commit Hooks

Pre-commit hooks automatically run code quality checks before each commit:

```bash
pip install pre-commit
pre-commit install

# Run hooks manually on all files
pre-commit run --all-files
```

The pre-commit hooks include:
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Static type checking
- **bandit**: Security checks
- **pydocstyle**: Docstring style checks
- **Standard hooks**: Trailing whitespace, YAML/JSON validation, etc.

### 5. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/core/herp/test_builders.py

# Run with verbose output
pytest -v
```

### 6. Type Checking

```bash
# Run mypy on source code
mypy src/

# Check specific module
mypy src/core/herp/client.py
```

## Code Style Guidelines

### Python Style
- Follow PEP 8 guidelines
- Line length: 100 characters (enforced by black)
- Use type hints for function signatures
- Write docstrings for all public functions/classes (Google style)

### Example

```python
from typing import Dict, Optional

def create_candidacy(
    name: str,
    requisition_id: str,
    email: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new candidacy in HERP.

    Args:
        name: Candidate's full name
        requisition_id: ID of the job requisition
        email: Candidate's email address (optional)

    Returns:
        Dictionary containing the created candidacy data

    Raises:
        HerpValidationError: If required fields are missing
        HerpAuthenticationError: If API key is invalid
    """
    # Implementation here
    pass
```

## Testing Guidelines

### Test Structure
- Use unittest or pytest framework
- One test file per source module
- Clear, descriptive test names
- Group related tests in classes

### Test Coverage
- Aim for >80% code coverage
- Test both success and failure cases
- Include edge cases and boundary conditions
- Mock external API calls

### Example Test

```python
import unittest
from src.core.herp.builders import CandidacyBuilder


class TestCandidacyBuilder(unittest.TestCase):
    """Test cases for CandidacyBuilder"""

    def test_basic_build(self):
        """Test building candidacy with required fields"""
        result = (
            CandidacyBuilder()
            .with_name("Jane Doe")
            .for_requisition("req_001")
            .build()
        )

        self.assertEqual(result["name"], "Jane Doe")
        self.assertEqual(result["requisition_id"], "req_001")

    def test_missing_name_raises_error(self):
        """Test that missing name raises ValueError"""
        with self.assertRaises(ValueError) as cm:
            CandidacyBuilder().for_requisition("req_001").build()

        self.assertIn("name", str(cm.exception).lower())
```

## Commit Message Guidelines

Follow conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code formatting (no functional changes)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Example

```
feat(builders): add TimelineCommentBuilder for creating comments

Add fluent builder interface for creating timeline comments with
support for both plain text and markdown content.

Closes #42
```

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following style guidelines
   - Add/update tests
   - Update documentation

3. **Run quality checks**
   ```bash
   # Format code
   black src/ tests/
   isort src/ tests/

   # Run linting
   flake8 src/ tests/

   # Run tests
   pytest --cov=src
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: your commit message"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Provide clear description of changes
   - Reference related issues
   - Ensure CI passes

## CI/CD Pipeline

The repository uses GitHub Actions for continuous integration:

1. **Lint**: Code formatting and linting checks
2. **Test**: Run test suite with coverage
3. **Type Check**: MyPy static type checking
4. **Security**: Bandit security scanning
5. **Docs**: Build documentation
6. **Build**: Package building

All checks must pass before merging.

## Questions or Issues?

- **Bug Reports**: [GitHub Issues](https://github.com/lalarsson87/herp-python-client/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/lalarsson87/herp-python-client/discussions)
- **Email**: engineering@belong.co.jp

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
