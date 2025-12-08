# HERP API Builder Patterns

## Overview

Builder patterns provide a fluent, readable interface for constructing complex API requests. Instead of manually building dictionaries with all the required fields, builders guide you through the process with clear, chainable methods.

## Benefits

✅ **Type Safety**: Clear method signatures prevent typos and missing fields
✅ **Readability**: Code reads like natural language
✅ **Validation**: Built-in validation catches errors before API calls
✅ **IDE Support**: Full autocomplete and inline documentation
✅ **Maintainability**: Changes to API structure isolated in builders

## Available Builders

### 1. CandidacyBuilder

Create candidacies with a fluent interface.

#### Basic Usage

```python
from src.core.herp import HerpClient, CandidacyBuilder
from src.core.utils.config import load_herp_config

client = HerpClient(load_herp_config())

# Build candidacy data
candidacy = (
    CandidacyBuilder()
    .with_name("Jane Doe")
    .with_email("jane@example.com")
    .with_phone("+81-90-1234-5678")
    .for_requisition("req_001")
    .at_step("application")
    .with_tags(["backend", "senior"])
    .build()
)

# Create candidacy
result = client.candidacies.create(candidacy)
print(f"Created candidacy: {result['id']}")
```

#### Available Methods

| Method | Required | Description |
|--------|----------|-------------|
| `with_name(name)` | ✅ | Set candidate full name |
| `with_email(email)` | ⭕ | Set candidate email (recommended) |
| `with_phone(phone)` | ⭕ | Set candidate phone number |
| `with_resume_url(url)` | ⭕ | Set resume URL |
| `for_requisition(id)` | ✅ | Set job requisition ID |
| `at_step(step)` | ⭕ | Set hiring step/stage |
| `with_tags(tags)` | ⭕ | Add tags (list of strings) |
| `with_custom_field(key, value)` | ⭕ | Add custom field data |
| `build()` | ✅ | Build and validate |

#### Examples

**Minimal Candidacy**:
```python
candidacy = (
    CandidacyBuilder()
    .with_name("John Smith")
    .for_requisition("req_backend_001")
    .build()
)
```

**Full Candidacy with Custom Fields**:
```python
candidacy = (
    CandidacyBuilder()
    .with_name("Sarah Johnson")
    .with_email("sarah@example.com")
    .with_phone("+81-80-9876-5432")
    .with_resume_url("https://linkedin.com/in/sarahjohnson")
    .for_requisition("req_sre_002")
    .at_step("screening")
    .with_tags(["kubernetes", "golang", "senior"])
    .with_custom_field("referral_source", "LinkedIn")
    .with_custom_field("years_experience", 8)
    .with_custom_field("location_preference", "Tokyo/Remote")
    .build()
)
```

**Bulk Creation**:
```python
candidates = [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"},
    {"name": "Charlie", "email": "charlie@example.com"},
]

candidacies = [
    (
        CandidacyBuilder()
        .with_name(c["name"])
        .with_email(c["email"])
        .for_requisition("req_001")
        .build()
    )
    for c in candidates
]

# Batch create
from src.core.herp import BatchHerpClient
batch_client = BatchHerpClient(client)
result = batch_client.create_candidacies_batch(candidacies)
```

### 2. ContactBuilder (InterviewBuilder)

Schedule interviews and contacts with a fluent interface.

#### Basic Usage

```python
from src.core.herp import ContactBuilder
from datetime import datetime, timedelta

# Schedule technical interview
contact = (
    ContactBuilder()
    .of_type("technical_interview")
    .with_title("Senior Backend Engineer - Technical Round")
    .scheduled_for(datetime.now() + timedelta(days=7))
    .for_duration(60)
    .at_location("https://zoom.us/j/123456789")
    .with_interviewers(["user_001", "user_002"])
    .with_notes("Focus areas: system design, Golang, microservices")
    .build()
)

# Create contact
result = client.contacts.create("cand_123", contact)
```

#### Available Methods

| Method | Required | Description |
|--------|----------|-------------|
| `of_type(type)` | ✅ | Set contact type |
| `with_title(title)` | ⭕ | Set interview title |
| `scheduled_at(iso_string)` | ⭕ | Set time (ISO 8601 string) |
| `scheduled_for(datetime)` | ⭕ | Set time (datetime object) |
| `for_duration(minutes)` | ⭕ | Set duration in minutes |
| `at_location(location)` | ⭕ | Set location or video URL |
| `with_interviewers(user_ids)` | ⭕ | Set interviewer IDs (list) |
| `with_notes(notes)` | ⭕ | Add notes or description |
| `build()` | ✅ | Build and validate |

#### Contact Types

Valid contact types:
- `phone_screen` - Initial phone screening
- `casual_interview` - Casual conversation
- `technical_interview` - Technical assessment
- `behavioral_interview` - Behavioral/cultural fit
- `final_interview` - Final round
- `reference_check` - Reference verification
- `other` - Other contact types

#### Examples

**Phone Screen**:
```python
contact = (
    ContactBuilder()
    .of_type("phone_screen")
    .with_title("Initial Phone Screen")
    .scheduled_at("2026-02-01T10:00:00Z")
    .for_duration(30)
    .with_notes("Quick 30-min intro call")
    .build()
)
```

**On-Site Interview Panel**:
```python
from datetime import datetime, timezone

contact = (
    ContactBuilder()
    .of_type("technical_interview")
    .with_title("On-Site Interview Panel - Day 1")
    .scheduled_for(datetime(2026, 2, 15, 9, 0, tzinfo=timezone.utc))
    .for_duration(240)  # 4 hours
    .at_location("Tokyo Office, Meeting Room A")
    .with_interviewers([
        "user_tech_lead",
        "user_eng_mgr",
        "user_vp_eng"
    ])
    .with_notes(
        "Full day panel:\n"
        "- 9:00-10:30: Technical deep dive\n"
        "- 10:45-12:00: System design\n"
        "- 13:00-14:30: Team collaboration\n"
        "- 14:45-15:30: Leadership discussion"
    )
    .build()
)
```

**Schedule Multiple Interviews**:
```python
# Schedule interview pipeline
pipeline = [
    ("phone_screen", 30, "Initial screening"),
    ("technical_interview", 60, "Technical round 1"),
    ("technical_interview", 90, "System design"),
    ("behavioral_interview", 60, "Cultural fit"),
    ("final_interview", 45, "Executive round"),
]

base_date = datetime.now(timezone.utc)

for i, (type_, duration, title) in enumerate(pipeline):
    contact = (
        ContactBuilder()
        .of_type(type_)
        .with_title(title)
        .scheduled_for(base_date + timedelta(days=i*7))
        .for_duration(duration)
        .build()
    )
    client.contacts.create(candidacy_id, contact)
```

### 3. EvaluationResponseBuilder

Submit interview evaluations with structured responses.

#### Basic Usage

```python
from src.core.herp import EvaluationResponseBuilder

evaluation = (
    EvaluationResponseBuilder()
    .answer_question("technical_skills", "Strong Golang and system design skills")
    .score_question("technical_skills", 5, max_score=5)
    .answer_question("communication", "Clear communicator, good at explaining concepts")
    .score_question("communication", 4, max_score=5)
    .answer_question("culture_fit", "Great team player, aligns with company values")
    .score_question("culture_fit", 5, max_score=5)
    .with_overall_score(14, max_score=15)
    .with_recommendation("strong_yes")
    .with_notes("Excellent candidate. Recommend proceeding to final round.")
    .build()
)

# Submit evaluation
result = client.evaluations.submit("eval_123", evaluation)
```

#### Available Methods

| Method | Required | Description |
|--------|----------|-------------|
| `answer_question(id, answer)` | ✅ | Add text answer |
| `score_question(id, score, max)` | ⭕ | Add numeric score |
| `with_overall_score(score, max)` | ⭕ | Set overall score |
| `with_recommendation(rec)` | ⭕ | Set recommendation |
| `with_notes(notes)` | ⭕ | Add general notes |
| `build()` | ✅ | Build and validate |

#### Recommendation Values

Valid recommendations:
- `strong_yes` - Strong hire
- `yes` - Hire
- `maybe` - Undecided
- `no` - Do not hire
- `strong_no` - Strong reject

#### Examples

**Technical Evaluation**:
```python
evaluation = (
    EvaluationResponseBuilder()
    # Coding assessment
    .answer_question("coding_q1", "Implemented efficient algorithm with O(n log n)")
    .score_question("coding_q1", 5, max_score=5)

    .answer_question("coding_q2", "Good solution but missed edge cases")
    .score_question("coding_q2", 3, max_score=5)

    # System design
    .answer_question("system_design", "Solid understanding of distributed systems")
    .score_question("system_design", 4, max_score=5)

    # Overall
    .with_overall_score(12, max_score=15)
    .with_recommendation("yes")
    .with_notes("Good technical skills, needs more experience with edge cases")
    .build()
)
```

**Behavioral Evaluation**:
```python
evaluation = (
    EvaluationResponseBuilder()
    .answer_question("leadership", "Demonstrated strong leadership in previous role")
    .score_question("leadership", 5, max_score=5)

    .answer_question("teamwork", "Collaborative, values team input")
    .score_question("teamwork", 5, max_score=5)

    .answer_question("adaptability", "Shows flexibility and learning mindset")
    .score_question("adaptability", 4, max_score=5)

    .with_overall_score(14, max_score=15)
    .with_recommendation("strong_yes")
    .with_notes("Outstanding cultural fit. Strong recommend for hire.")
    .build()
)
```

## Comparison: Builder vs Manual

### Manual Dictionary Construction (Before)

```python
# Manual - error-prone, hard to read
candidacy = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "+81-90-1234-5678",
    "requisition_id": "req_001",  # Easy to misspell
    "step": "application",
    "tags": ["backend", "senior"],
    "custom_fields": {
        "referral_source": "LinkedIn"
    }
}

# Missing validation - errors only at API call time
client.candidacies.create(candidacy)
```

### Builder Pattern (After)

```python
# Builder - type-safe, readable, validated
candidacy = (
    CandidacyBuilder()
    .with_name("Jane Doe")
    .with_email("jane@example.com")
    .with_phone("+81-90-1234-5678")
    .for_requisition("req_001")  # IDE autocomplete prevents typos
    .at_step("application")
    .with_tags(["backend", "senior"])
    .with_custom_field("referral_source", "LinkedIn")
    .build()  # Validation happens here
)

# Errors caught before API call
client.candidacies.create(candidacy)
```

## Advanced Patterns

### Reusable Builder Templates

```python
def base_senior_backend_candidacy():
    """Template for senior backend candidates"""
    return (
        CandidacyBuilder()
        .for_requisition("req_backend_senior")
        .at_step("application")
        .with_tags(["backend", "senior"])
    )

# Use template
candidacy = (
    base_senior_backend_candidacy()
    .with_name("Alice Smith")
    .with_email("alice@example.com")
    .with_custom_field("referral_source", "Employee referral")
    .build()
)
```

### Builder with Validation Logic

```python
def create_candidacy_with_validation(builder_func, **validator_args):
    """Create candidacy with custom validation"""
    candidacy = builder_func()

    # Custom validation
    if validator_args.get("require_phone") and "phone" not in candidacy:
        raise ValueError("Phone number is required for this requisition")

    return candidacy

# Use
candidacy = create_candidacy_with_validation(
    lambda: (
        CandidacyBuilder()
        .with_name("Bob Jones")
        .with_email("bob@example.com")
        .for_requisition("req_001")
        .build()
    ),
    require_phone=True  # Will raise error
)
```

### Conditional Building

```python
def build_candidacy(data: dict, requisition_id: str):
    """Build candidacy from variable data"""
    builder = (
        CandidacyBuilder()
        .with_name(data["name"])
        .for_requisition(requisition_id)
    )

    # Conditional fields
    if email := data.get("email"):
        builder = builder.with_email(email)

    if phone := data.get("phone"):
        builder = builder.with_phone(phone)

    if tags := data.get("tags"):
        builder = builder.with_tags(tags)

    return builder.build()
```

## Integration with Existing Code

### Using with BatchHerpClient

```python
from src.core.herp import BatchHerpClient, CandidacyBuilder

batch_client = BatchHerpClient(client)

# Build multiple candidacies
candidacies = [
    (
        CandidacyBuilder()
        .with_name(name)
        .with_email(f"{name.lower().replace(' ', '.')}@example.com")
        .for_requisition("req_001")
        .build()
    )
    for name in ["Alice Johnson", "Bob Smith", "Charlie Davis"]
]

# Batch create
result = batch_client.create_candidacies_batch(candidacies)
print(f"Created {len(result.successful)} candidacies")
```

### Using with Modular API

```python
from src.core.herp import HerpClient, ContactBuilder

client = HerpClient(config)

# Use with modular API
contact = (
    ContactBuilder()
    .of_type("technical_interview")
    .with_title("Backend Engineer Interview")
    .scheduled_at("2026-02-01T14:00:00Z")
    .build()
)

# Call via modular API
result = client.contacts.create("cand_123", contact)
```

## Best Practices

### 1. Always Use `.build()` Last

```python
# ✅ Good
candidacy = builder.with_name("Jane").build()

# ❌ Bad - missing validation
candidacy = builder.with_name("Jane")._data
```

### 2. Chain Methods for Readability

```python
# ✅ Good - readable, one chain
candidacy = (
    CandidacyBuilder()
    .with_name("Jane Doe")
    .with_email("jane@example.com")
    .for_requisition("req_001")
    .build()
)

# ❌ Bad - verbose
builder = CandidacyBuilder()
builder = builder.with_name("Jane Doe")
builder = builder.with_email("jane@example.com")
builder = builder.for_requisition("req_001")
candidacy = builder.build()
```

### 3. Validate Early

```python
# ✅ Good - validate before processing
try:
    candidacy = builder.build()
except ValueError as e:
    logger.error(f"Invalid candidacy: {e}")
    return

# Now safe to create
result = client.candidacies.create(candidacy)
```

### 4. Use Type Hints

```python
from src.core.herp import CandidacyBuilder

def create_referral_candidacy(
    name: str,
    email: str,
    referrer: str
) -> dict:
    """Create candidacy from referral"""
    return (
        CandidacyBuilder()
        .with_name(name)
        .with_email(email)
        .for_requisition("req_001")
        .with_custom_field("referral_source", "Employee")
        .with_custom_field("referred_by", referrer)
        .build()
    )
```

## Migration Guide

### Migrating from Manual Dictionaries

**Before**:
```python
candidacy_data = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "requisition_id": "req_001",
}
result = client.create_candidacy(candidacy_data)
```

**After**:
```python
candidacy = (
    CandidacyBuilder()
    .with_name("Jane Doe")
    .with_email("jane@example.com")
    .for_requisition("req_001")
    .build()
)
result = client.candidacies.create(candidacy)
```

**Benefits**:
- Type safety (IDE catches errors)
- Early validation (errors before API call)
- Better readability
- Self-documenting code

## Error Handling

```python
from src.core.herp import CandidacyBuilder

try:
    candidacy = (
        CandidacyBuilder()
        # Missing required fields
        .with_email("jane@example.com")
        .build()
    )
except ValueError as e:
    print(f"Validation error: {e}")
    # Output: "Candidate name is required"

try:
    evaluation = (
        EvaluationResponseBuilder()
        .with_recommendation("invalid")  # Invalid value
        .build()
    )
except ValueError as e:
    print(f"Validation error: {e}")
    # Output: "Invalid recommendation: invalid. Must be one of: ..."
```

## Summary

Builder patterns make HERP API integration:

✅ **Safer**: Type-checked and validated before API calls
✅ **Clearer**: Code reads like documentation
✅ **Easier**: IDE autocomplete guides you
✅ **Maintainable**: Changes isolated in builder classes

Start using builders in new code, migrate existing code gradually.
