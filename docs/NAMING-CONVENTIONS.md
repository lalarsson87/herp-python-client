# Naming Conventions

**Project**: HERP Domain-Driven Architecture
**Last Updated**: January 25, 2026

---

## Overview

This document defines naming conventions for the HERP project. These conventions ensure consistency across the codebase while respecting the idioms of each API we integrate with.

## Python Code Conventions

### General Principles

1. **Follow PEP 8**: All Python code follows PEP 8 style guide
2. **Snake Case for Python**: Functions, variables, and attributes use `snake_case`
3. **Pascal Case for Classes**: Class names use `PascalCase`
4. **SCREAMING_SNAKE_CASE for Constants**: Module-level constants use `SCREAMING_SNAKE_CASE`
5. **Preserve API Conventions**: When interfacing with external APIs, preserve their naming conventions in request/response data

### Functions and Methods

```python
# Good
def get_candidate_profile(candidacy_id: str) -> Dict[str, Any]:
    """Fetch candidate profile from HERP API"""
    pass

def calculate_velocity_score(timeline: List[Dict]) -> float:
    """Calculate candidate progression velocity"""
    pass

# Bad
def GetCandidateProfile(candidacyId: str):  # Wrong: camelCase parameters
    pass

def calculateVelocityScore(timeline):  # Wrong: camelCase function name
    pass
```

### Variables

```python
# Good
candidate_id = "550e8400-e29b-41d4-a716-446655440000"
evaluation_score = 8.5
time_to_current_stage = 14

# Bad
candidateId = "..."  # Wrong: camelCase
EvaluationScore = 8.5  # Wrong: PascalCase for variable
timeTocurrentStage = 14  # Wrong: inconsistent casing
```

### Class Names

```python
# Good
class CandidateAnalyzer:
    """Analyzes candidate profiles"""
    pass

class HerpClient:
    """Client for HERP API"""
    pass

# Bad
class candidate_analyzer:  # Wrong: snake_case for class
    pass

class HERP_Client:  # Wrong: SCREAMING_SNAKE_CASE for class
    pass
```

### Constants

```python
# Good
DEFAULT_RATE_LIMIT_DELAY = 0.6
MAX_RETRY_ATTEMPTS = 3
API_VERSION = "v1"

# Bad
default_rate_limit_delay = 0.6  # Wrong: snake_case for constant
maxRetryAttempts = 3  # Wrong: camelCase for constant
```

## API Integration Conventions

### HERP API (camelCase)

HERP API uses camelCase for field names. **Preserve these in request/response data**:

```python
# Good - Preserve HERP's camelCase in API data
herp_response = {
    "candidacyId": "abc-123",
    "firstName": "Tomoka",
    "lastName": "Fukushima",
    "currentStep": {"id": "step-1", "name": "1st Interview"},
    "appliedAt": "2026-01-20T00:00:00Z"
}

# But use snake_case in Python code
candidacy_id = herp_response["candidacyId"]
first_name = herp_response["firstName"]
current_step = herp_response["currentStep"]
```

### Notion API (snake_case in Python SDK)

Notion's Python SDK uses snake_case. Follow their convention:

```python
# Good - Notion SDK uses snake_case
notion_client.pages.update(
    page_id="abc-123",
    properties={
        "Status": {"status": {"name": "In Progress"}},
        "Overall Score": {"number": 8.5}
    }
)
```

### Pydantic Models (Hybrid Approach)

Use Pydantic's `Field` with `alias` to map between conventions:

```python
from pydantic import BaseModel, Field

class HerpCandidacyResponse(BaseModel):
    """HERP API response with camelCase aliases"""

    # Python code uses snake_case
    candidacy_id: str = Field(alias="candidacyId")
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    applied_at: str = Field(alias="appliedAt")

    class Config:
        populate_by_name = True  # Accept both snake_case and camelCase

# Usage
candidacy = HerpCandidacyResponse(**herp_response)
print(candidacy.candidacy_id)  # Access via snake_case
```

## File and Directory Naming

### Python Modules

```
# Good
src/domains/candidates/analysis/profile_analyzer.py
src/core/herp/client.py
src/core/utils/retry.py

# Bad
src/domains/candidates/analysis/ProfileAnalyzer.py  # Wrong: PascalCase
src/core/herp/HERPClient.py  # Wrong: PascalCase
src/core/utils/Retry.py  # Wrong: PascalCase
```

### Directories

```
# Good
src/domains/candidates/
src/domains/sync/
src/cli/entrypoints/

# Bad
src/Domains/Candidates/  # Wrong: PascalCase
src/domains/Sync/  # Wrong: PascalCase
```

### Test Files

```
# Good
tests/unit/domains/candidates/test_profile_analyzer.py
tests/unit/core/test_herp_client.py

# Bad
tests/unit/domains/candidates/TestProfileAnalyzer.py  # Wrong: PascalCase
tests/unit/core/test_HERPClient.py  # Wrong: mixed case
```

## Database Field Naming

### Notion Database Properties

Notion properties can use any format (often with emojis). **Preserve as-is**:

```python
# Good - Preserve exact Notion property names
properties = {
    "📊 Overall Score": {"number": 8.5},
    "🎯 Recommendation": {"select": {"name": "Strong Hire"}},
    "Status": {"status": {"name": "In Progress"}}
}

# Access via exact names
OVERALL_SCORE_PROPERTY = "📊 Overall Score"  # Constant for consistency
properties[OVERALL_SCORE_PROPERTY] = {"number": 9.0}
```

## Exceptions to Rules

### 1. Third-Party Library Compatibility

When integrating with third-party libraries that enforce their own conventions, follow their conventions:

```python
# Good - Follow library convention
from notion_client import Client as NotionSDKClient

notion = NotionSDKClient(auth=api_key)
notion.pages.retrieve(page_id="abc-123")  # SDK uses snake_case
```

### 2. JSON/Dict Keys from External APIs

Preserve external API field names in raw dictionaries:

```python
# Good - Preserve HERP's camelCase in dict
herp_data = {
    "candidacyId": "abc-123",
    "firstName": "Tomoka",
    "currentStep": {"id": "1", "name": "Interview"}
}

# Transform to snake_case only in internal data structures
candidate = {
    "candidacy_id": herp_data["candidacyId"],
    "first_name": herp_data["firstName"],
    "current_step": herp_data["currentStep"]
}
```

### 3. Configuration Keys

Environment variables and configuration keys use SCREAMING_SNAKE_CASE:

```python
# Good
HERP_API_KEY = os.getenv("HERP_API_KEY")
NOTION_CANDIDATES_DB_ID = os.getenv("NOTION_CANDIDATES_DB_ID")
RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", "0.6"))

# Bad
herpApiKey = os.getenv("HERP_API_KEY")  # Wrong: camelCase variable
NotionCandidatesDbId = os.getenv("NOTION_CANDIDATES_DB_ID")  # Wrong: PascalCase
```

## Naming Patterns

### Service Classes

```python
# Pattern: {Domain}{Function}{Type}
class CandidateAnalyzer:  # Domain=Candidate, Function=Analyzer
class ProfileAnalyzer:  # Domain=Profile, Function=Analyzer
class CandidateEvaluator:  # Domain=Candidate, Function=Evaluator
class FullSyncService:  # Domain=FullSync, Type=Service
```

### Client Classes

```python
# Pattern: {API}Client
class HerpClient:  # API=Herp
class NotionClient:  # API=Notion
```

### Configuration Classes

```python
# Pattern: {Component}Config
class HerpConfig:
class NotionConfig:
class DeduplicationConfig:
class EvaluationConfig:
```

### Data Classes

```python
# Pattern: {Domain}{Type}
class CandidateData:  # Domain=Candidate, Type=Data
class DuplicateGroup:  # Domain=Duplicate, Type=Group
class DeduplicationMetrics:  # Domain=Deduplication, Type=Metrics
```

## Common Abbreviations

Use these standard abbreviations consistently:

| Full Term | Abbreviation | Example |
|-----------|--------------|---------|
| Identification | ID | `candidate_id`, `user_id` |
| Configuration | Config | `HerpConfig`, `NotionConfig` |
| Database | DB | `NOTION_CANDIDATES_DB_ID` |
| Application Programming Interface | API | `HERP_API_KEY` |
| Maximum | Max | `MAX_RETRY_ATTEMPTS` |
| Minimum | Min | `min_score` |
| Number | Num | `num_candidates` |

## Anti-Patterns to Avoid

### 1. Mixed Casing in Same Scope

```python
# Bad - Inconsistent casing
def process_candidate(candidacyId, firstName, last_name):
    #                  ^ camelCase  ^ camelCase  ^ snake_case
    pass

# Good - Consistent casing
def process_candidate(candidacy_id, first_name, last_name):
    #                  ^ snake_case ^ snake_case ^ snake_case
    pass
```

### 2. Abbreviations Without Context

```python
# Bad - Unclear abbreviations
def get_cand_prof(cid):
    pass

# Good - Clear names
def get_candidate_profile(candidacy_id):
    pass
```

### 3. Redundant Prefixes

```python
# Bad - Redundant type prefix
candidate_dict = {}
candidate_list = []
candidate_string = ""

# Good - Type is implied or clear from context
candidate = {}
candidates = []
candidate_name = ""
```

## Validation

Use linters to enforce naming conventions:

```bash
# Check with pylint
pylint src/ --disable=all --enable=invalid-name

# Check with flake8
flake8 src/ --select=N  # Naming conventions

# Auto-format with black
black src/
```

## Summary

| Element | Convention | Example |
|---------|-----------|---------|
| Functions/Methods | `snake_case` | `def get_candidate()` |
| Variables | `snake_case` | `candidate_id = "abc"` |
| Classes | `PascalCase` | `class CandidateAnalyzer` |
| Constants | `SCREAMING_SNAKE_CASE` | `MAX_ATTEMPTS = 3` |
| Modules | `snake_case.py` | `profile_analyzer.py` |
| Directories | `snake_case/` | `candidates/` |
| Environment Vars | `SCREAMING_SNAKE_CASE` | `HERP_API_KEY` |
| HERP API Fields | `camelCase` (preserve) | `candidacyId` |
| Notion Properties | As-defined (preserve) | `📊 Overall Score` |

**Guiding Principle**: Be consistent within Python code (snake_case), but preserve external API conventions in request/response data to maintain API compatibility.

---

**Last Updated**: January 25, 2026
**Applies To**: All Python code in `src/`, `tests/`, and `scripts/`
