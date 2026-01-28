# HERP API Validator Skill

**Skill ID**: `herp-api-validator`
**Purpose**: Validate HERP API responses against TypedDict schemas
**When to use**: Schema validation, API contract testing, migration verification

## Usage

```
/herp-api-validator [command] [options]
```

**Commands**:
- `validate` - Validate API responses against schemas
- `extract` - Extract schemas from VCR cassettes
- `compare` - Compare expected vs actual schemas
- `report` - Generate validation report

## What This Skill Does

1. **Schema extraction** - Extracts actual field structures from API responses
2. **Type validation** - Validates responses against TypedDict schemas
3. **Field mapping** - Verifies camelCase ↔ snake_case mappings
4. **Coverage reporting** - Reports schema coverage percentage
5. **Difference detection** - Identifies schema drift over time

## Implementation Reference

### TypedDict Schema Location

All HERP API schemas are in `src/core/herp/schemas.py`:

```python
from typing import TypedDict, List, NotRequired
try:
    from typing import NotRequired  # Python 3.11+
except ImportError:
    from typing_extensions import NotRequired  # Python 3.10

class CandidacySchema(TypedDict):
    """HERP Candidacy API response schema"""
    id: str
    name: str
    email: NotRequired[str]
    status: str  # "active" | "terminated"
    step: NotRequired[str]
    stepUpdatedAt: NotRequired[str]
    terminationReason: NotRequired[str]
    requisitionId: NotRequired[str]
    createdAt: NotRequired[str]
    updatedAt: NotRequired[str]
```

### Field Naming Convention

**Critical**: HERP API uses camelCase, Python code uses snake_case

```python
# ✅ CORRECT - API responses use camelCase
candidacy["requisitionId"]
candidacy["stepUpdatedAt"]
candidacy["terminationReason"]

# ❌ WRONG - Will fail!
candidacy["requisition_id"]
candidacy["step_updated_at"]
candidacy["termination_reason"]
```

### Models vs Schemas

**Schemas** (`src/core/herp/schemas.py`):
- TypedDict definitions for API responses
- Used for type hints and validation
- Matches exact API structure (camelCase)

**Models** (`src/core/herp/models.py`):
- Dataclass definitions for business logic
- Python-friendly names (snake_case)
- Convenience methods and properties

```python
# Schema - for API validation
from src.core.herp.schemas import CandidacySchema

def get_candidacy(id: str) -> CandidacySchema:
    return self.get(f"/v1/candidacies/{id}")

# Model - for business logic
from src.core.herp.models import Candidacy

candidacy = Candidacy.from_dict(api_response)
if candidacy.is_active:
    print(f"Processing {candidacy.name}")
```

## Usage Examples

### Validate Live API Response

```bash
/herp-api-validator validate \
  --endpoint=/v1/candidacies/123 \
  --schema=CandidacySchema \
  --strict
```

This will:
1. Fetch candidacy from HERP API
2. Validate against `CandidacySchema`
3. Report missing/extra fields
4. Check field types
5. Verify required fields present

### Extract Schemas from VCR Cassettes

```bash
/herp-api-validator extract \
  --cassettes=tests/integration/fixtures/cassettes/ \
  --output=schemas_extracted.json
```

Uses `scripts/utilities/extract_api_schemas.py`:

```python
#!/usr/bin/env python3
"""Extract actual schemas from recorded API responses"""

from pathlib import Path
import yaml
from collections import defaultdict

def extract_schemas(cassette_dir: Path):
    schemas = defaultdict(lambda: {"fields": set(), "samples": []})

    for cassette in cassette_dir.glob("*.yaml"):
        with open(cassette) as f:
            data = yaml.safe_load(f)

        for interaction in data.get("interactions", []):
            response = interaction["response"]
            endpoint = interaction["request"]["uri"]

            # Extract schema
            if response["status"]["code"] == 200:
                body = json.loads(response["body"]["string"])
                schemas[endpoint]["fields"].update(extract_fields(body))
                schemas[endpoint]["samples"].append(body)

    return schemas
```

### Compare Expected vs Actual

```bash
/herp-api-validator compare \
  --expected=src/core/herp/schemas.py \
  --actual=schemas_extracted.json \
  --report=schema_diff.md
```

Output:
```markdown
# Schema Validation Report

## CandidacySchema

### Missing Fields (in schema but not in API)
- None

### Extra Fields (in API but not in schema)
- `channel` (optional field not documented)
- `tags` (array of strings)

### Type Mismatches
- `stepUpdatedAt`: Expected string, got null in 15% of samples
  → Recommendation: Mark as NotRequired[str]

### Recommendations
1. Add `channel` field to schema as NotRequired
2. Add `tags` field as NotRequired[List[str]]
3. Verify `stepUpdatedAt` is truly optional
```

### Generate Coverage Report

```bash
/herp-api-validator report \
  --cassettes=tests/integration/fixtures/cassettes/ \
  --schemas=src/core/herp/schemas.py \
  --output=coverage_report.html
```

## Validation Patterns

### Runtime Validation

```python
from src.core.herp.schemas import CandidacySchema
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Static type checking with mypy
    def get_candidacy(id: str) -> CandidacySchema:
        ...

# Runtime validation (optional, for critical paths)
def validate_candidacy(data: dict) -> bool:
    """Validate candidacy data matches schema"""
    required_fields = {"id", "name", "status"}
    optional_fields = {
        "email", "step", "stepUpdatedAt", "terminationReason",
        "requisitionId", "createdAt", "updatedAt", "channel"
    }

    # Check required fields
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # Check for unknown fields
    all_fields = required_fields | optional_fields
    extra_fields = set(data.keys()) - all_fields
    if extra_fields:
        print(f"Warning: Extra fields detected: {extra_fields}")

    return True
```

### Type Narrowing

```python
from typing import cast
from src.core.herp.schemas import CandidacySchema

response = client.get(f"/v1/candidacies/{id}")

# Type narrowing for better IDE support
candidacy = cast(CandidacySchema, response)

# Now IDE knows exact structure
print(candidacy["id"])  # ✓ Valid
print(candidacy["name"])  # ✓ Valid
print(candidacy["email"])  # ✓ Valid (NotRequired)
print(candidacy["unknown"])  # ✗ Type error
```

## Schema Evolution Tracking

### Detect API Changes

```python
# Track schema versions
SCHEMA_VERSIONS = {
    "CandidacySchema": {
        "v1.0": ["id", "name", "email", "status"],
        "v1.1": ["id", "name", "email", "status", "step"],
        "v2.0": ["id", "name", "email", "status", "step", "channel"],
    }
}

def detect_version(data: dict) -> str:
    """Detect which schema version data matches"""
    fields = set(data.keys())

    for version, expected_fields in SCHEMA_VERSIONS["CandidacySchema"].items():
        if fields >= set(expected_fields):
            return version

    return "unknown"
```

### Migration Helpers

```python
def migrate_candidacy_v1_to_v2(old_data: dict) -> dict:
    """Migrate candidacy from v1 to v2 schema"""
    new_data = old_data.copy()

    # Add new required fields with defaults
    if "channel" not in new_data:
        new_data["channel"] = None

    # Transform renamed fields
    if "stepId" in new_data:
        new_data["step"] = new_data.pop("stepId")

    return new_data
```

## Integration with Tests

### VCR-Based Validation

```python
import pytest
import vcr
from src.core.herp.client import HerpClient
from src.core.herp.schemas import CandidacySchema

@pytest.mark.vcr
def test_candidacy_schema_validation():
    """Test that API response matches schema"""
    client = HerpClient(api_token="test_token")

    # Recorded interaction from VCR cassette
    candidacy = client.get_candidacy("candidacy_123")

    # Validate required fields
    assert "id" in candidacy
    assert "name" in candidacy
    assert "status" in candidacy

    # Validate field types
    assert isinstance(candidacy["id"], str)
    assert isinstance(candidacy["name"], str)
    assert candidacy["status"] in ["active", "terminated"]

    # Validate optional fields if present
    if "email" in candidacy:
        assert isinstance(candidacy["email"], str)
        assert "@" in candidacy["email"]

    if "stepUpdatedAt" in candidacy:
        assert isinstance(candidacy["stepUpdatedAt"], str)
        # Validate ISO 8601 format
        from datetime import datetime
        datetime.fromisoformat(candidacy["stepUpdatedAt"])
```

### Schema Contract Tests

```python
def test_all_endpoints_have_schemas():
    """Ensure all API endpoints have defined schemas"""
    from src.core.herp import schemas

    required_schemas = [
        "CandidacySchema",
        "ContactSchema",
        "EvaluationSchema",
        "TimelineCommentSchema",
        "FileSchema",
        "RequisitionSchema",
        "UserSchema",
    ]

    for schema_name in required_schemas:
        assert hasattr(schemas, schema_name), \
            f"Missing schema: {schema_name}"
```

## Common Issues

### Missing NotRequired

**Problem**: Optional fields not marked as NotRequired

```python
# ❌ WRONG - email might not be present
class CandidacySchema(TypedDict):
    id: str
    name: str
    email: str  # Will fail if email is None

# ✅ CORRECT
class CandidacySchema(TypedDict):
    id: str
    name: str
    email: NotRequired[str]  # Explicitly optional
```

### CamelCase Confusion

**Problem**: Using snake_case for API fields

```python
# ❌ WRONG
candidacy["created_at"]  # KeyError!

# ✅ CORRECT
candidacy["createdAt"]

# ✅ BETTER - Use model for Python-friendly access
from src.core.herp.models import Candidacy
c = Candidacy.from_dict(candidacy)
c.created_at  # Works!
```

### Type Union Issues

**Problem**: Fields that can be multiple types

```python
# Handle null/None values
class ContactSchema(TypedDict):
    id: str
    scheduledAt: NotRequired[str | None]  # Can be string or None
    completedAt: NotRequired[str | None]
```

## Validation Tools

### Mypy Integration

```bash
# Run type checking
mypy src/ --ignore-missing-imports

# Check specific file
mypy src/core/herp/client.py --strict
```

### Runtime Validation Library

Consider using `pydantic` for runtime validation:

```python
from pydantic import BaseModel, Field
from typing import Optional

class CandidacyModel(BaseModel):
    """Pydantic model for runtime validation"""
    id: str
    name: str
    email: Optional[str] = None
    status: str
    step: Optional[str] = None

    # Camel case conversion
    class Config:
        alias_generator = lambda field: ''.join(
            word.capitalize() if i else word
            for i, word in enumerate(field.split('_'))
        )
        populate_by_name = True

# Validate API response
candidacy = CandidacyModel(**api_response)
```

## Best Practices

1. **Define schemas first**: Before implementing endpoints
2. **Keep schemas minimal**: Only required + common optional fields
3. **Use NotRequired**: Explicitly mark all optional fields
4. **Document field purpose**: Add docstrings to schema classes
5. **Version schemas**: Track changes over time
6. **Test with real data**: Use VCR cassettes from production
7. **Validate early**: Check schemas in CI/CD pipeline

## Related Files

- `src/core/herp/schemas.py` - All TypedDict schemas
- `src/core/herp/models.py` - Dataclass models
- `src/core/herp/types.py` - Additional type definitions
- `scripts/utilities/extract_api_schemas.py` - Schema extraction utility
- `tests/unit/core/herp/test_schemas.py` - Schema validation tests

## Notes

- Always use camelCase for API field names in schemas
- Mark all optional fields with `NotRequired`
- Keep schemas in sync with API documentation
- Use VCR cassettes to capture real API responses
- Validate schemas in CI/CD pipeline
- Consider using pydantic for runtime validation
