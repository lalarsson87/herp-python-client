# HERP Event Sourcing Guide

## Overview

Event Sourcing captures all changes to candidacy state as a sequence of immutable events. Instead of storing current state, we store the complete history and rebuild state by replaying events.

## Benefits

✅ **Complete Audit Trail**: Every change is recorded forever
✅ **Temporal Queries**: View state at any point in time
✅ **Event Replay**: Rebuild state from events
✅ **Projections**: Create multiple views from same events
✅ **Analytics**: Rich data for reporting and metrics
✅ **Compliance**: Full history for regulatory requirements

## Quick Start

```python
from src.core.herp import (
    EventSourcedCandidacy,
    InMemoryEventStore,
    CandidacyProjection,
    TimelineProjection,
    AuditLogProjection,
)

# Create event store
store = InMemoryEventStore()

# Create candidacy
candidacy = EventSourcedCandidacy.create(
    candidacy_id="cand_123",
    name="Jane Doe",
    email="jane@example.com",
    requisition_id="req_001",
    event_store=store,
    user_id="user_456"
)

# Make changes
candidacy.change_step("interview", user_id="user_456")
candidacy.add_contact("contact_789", "technical_interview", user_id="user_456")
candidacy.upload_file("file_001", "resume.pdf", "resume", user_id="user_456")

# Get current state
state = candidacy.get_state()
print(f"Candidate: {state['name']}, Step: {state['step']}")

# Get historical state
from datetime import datetime
state_yesterday = candidacy.get_state_at(datetime(2026, 1, 25))

# Get event history
history = candidacy.get_event_history()
for entry in history:
    print(f"{entry['timestamp']}: {entry['event_type']}")
```

## Core Concepts

### Events

Events are immutable facts that have happened:

```python
# Event: Candidacy created
CandidacyCreated.create(
    candidacy_id="cand_123",
    name="Jane Doe",
    email="jane@example.com",
    requisition_id="req_001",
    user_id="user_456"
)

# Event: Step changed
CandidacyStepChanged.create(
    candidacy_id="cand_123",
    from_step="application",
    to_step="interview",
    user_id="user_456"
)
```

**Available Events**:
- `CandidacyCreated` - Candidacy created
- `CandidacyStepChanged` - Hiring step changed
- `CandidacyStatusChanged` - Status changed
- `CandidacyTerminated` - Candidacy terminated
- `ContactAdded` - Interview added
- `ContactUpdated` - Interview updated
- `FileUploaded` - File uploaded
- `TimelineCommentAdded` - Comment added
- `AssignmentAdded` - Team member assigned
- `AssignmentRemoved` - Team member unassigned

### Event Store

Stores and retrieves events:

```python
# In-memory (for testing)
store = InMemoryEventStore()

# File-based (for production)
from src.core.herp.events import FileEventStore
store = FileEventStore("/path/to/events")

# Append event
store.append(event)

# Load events for candidacy
events = store.load_events("cand_123")

# Load events by type
step_changes = store.load_events_by_type("CandidacyStepChanged")

# Load all events in time range
from datetime import datetime
recent_events = store.load_all_events(
    from_timestamp=datetime(2026, 1, 1),
    to_timestamp=datetime(2026, 1, 31)
)
```

### Event-Sourced Aggregate

Rebuilds state from events:

```python
# Create new candidacy
candidacy = EventSourcedCandidacy.create(
    candidacy_id="cand_123",
    name="Jane Doe",
    event_store=store
)

# Load existing candidacy
candidacy = EventSourcedCandidacy.load("cand_123", store)

# Make changes
candidacy.change_step("interview")
candidacy.add_contact("contact_123", "phone_screen")
candidacy.terminate("hired")

# Commit changes
candidacy.commit()

# Get state
state = candidacy.get_state()
```

### Projections

Create different views from events:

```python
# Candidacy state projection
projection = CandidacyProjection(store)
state = projection.get_candidacy_state("cand_123")
all_states = projection.get_all_candidacy_states()
active = projection.get_candidacies_by_status("active")

# Timeline projection
timeline_proj = TimelineProjection(store)
timeline = timeline_proj.get_candidacy_timeline("cand_123")
recent = timeline_proj.get_recent_activity(hours=24)

# Audit log projection
audit_proj = AuditLogProjection(store)
audit_log = audit_proj.get_audit_log("cand_123")
user_actions = audit_proj.get_user_actions("user_456")

# Analytics projection
analytics_proj = AnalyticsProjection(store)
metrics = analytics_proj.get_metrics()
funnel = analytics_proj.get_conversion_funnel()
time_to_hire = analytics_proj.get_time_to_hire()
```

## Usage Examples

### Complete Candidacy Lifecycle

```python
from src.core.herp import EventSourcedCandidacy, InMemoryEventStore

store = InMemoryEventStore()

# Day 1: Candidate applies
candidacy = EventSourcedCandidacy.create(
    candidacy_id="cand_123",
    name="Jane Doe",
    email="jane@example.com",
    requisition_id="req_001",
    event_store=store,
    user_id="recruiter_1"
)

# Day 3: Phone screen scheduled
candidacy.change_step("phone_screen", user_id="recruiter_1")
candidacy.add_contact(
    contact_id="contact_1",
    contact_type="phone_screen",
    scheduled_at="2026-01-28T10:00:00Z",
    interviewer_ids=["recruiter_1"],
    user_id="recruiter_1"
)

# Day 5: Technical interview
candidacy.change_step("technical_interview", user_id="recruiter_1")
candidacy.add_contact(
    contact_id="contact_2",
    contact_type="technical_interview",
    scheduled_at="2026-01-30T14:00:00Z",
    interviewer_ids=["eng_mgr_1"],
    user_id="recruiter_1"
)

# Day 7: Offer extended
candidacy.change_step("offer", user_id="recruiter_1")

# Day 10: Offer accepted
candidacy.terminate("hired", user_id="recruiter_1")

# View complete history
history = candidacy.get_event_history()
for entry in history:
    print(f"{entry['timestamp']}: {entry['event_type']}")
```

### Temporal Queries

```python
from datetime import datetime

# Get state at specific point in time
state_day_5 = candidacy.get_state_at(datetime(2026, 1, 28))
print(f"On Day 5, candidate was at: {state_day_5['step']}")

state_day_10 = candidacy.get_state_at(datetime(2026, 1, 31))
print(f"On Day 10, candidate was at: {state_day_10['step']}")
```

### Analytics and Reporting

```python
from src.core.herp import AnalyticsProjection

projection = AnalyticsProjection(store)

# Get recruitment metrics
metrics = projection.get_metrics()
print(f"Total candidacies: {metrics['total_candidacies']}")
print(f"Active: {metrics['active_candidacies']}")
print(f"Hired: {metrics['hired_candidacies']}")
print(f"By step: {metrics['by_step']}")

# Get conversion funnel
funnel = projection.get_conversion_funnel()
print(f"Funnel: {funnel}")

# Get time-to-hire
tth = projection.get_time_to_hire()
print(f"Average time to hire: {tth['average_days']} days")
```

### Audit Trail

```python
from src.core.herp import AuditLogProjection

projection = AuditLogProjection(store)

# Get audit log for candidacy
audit_log = projection.get_audit_log("cand_123")
for entry in audit_log:
    print(f"{entry['timestamp']}: {entry['user_id']} {entry['action']}")
    if entry['before']:
        print(f"  Before: {entry['before']}")
    if entry['after']:
        print(f"  After: {entry['after']}")

# Get all actions by user
user_actions = projection.get_user_actions("recruiter_1")
print(f"User performed {len(user_actions)} actions")
```

## Integration with HERP Client

```python
from src.core.herp import HerpClient, EventSourcedCandidacy, InMemoryEventStore
from src.core.utils.config import HerpConfig

config = HerpConfig.from_env()
client = HerpClient(config)
store = InMemoryEventStore()

# Create candidacy via API
api_candidacy = client.candidacies.create({
    "name": "Jane Doe",
    "email": "jane@example.com",
    "requisition_id": "req_001"
})

# Mirror in event store
event_candidacy = EventSourcedCandidacy.create(
    candidacy_id=api_candidacy["id"],
    name=api_candidacy["name"],
    email=api_candidacy.get("email"),
    requisition_id=api_candidacy.get("requisition_id"),
    event_store=store,
    user_id="system"
)

# Sync changes
def sync_to_event_store(candidacy_id, change_type, **kwargs):
    """Sync API changes to event store"""
    candidacy = EventSourcedCandidacy.load(candidacy_id, store)

    if change_type == "step_change":
        candidacy.change_step(kwargs["to_step"], user_id=kwargs.get("user_id"))
    elif change_type == "contact_added":
        candidacy.add_contact(**kwargs)
    # ... handle other types

    candidacy.commit()

# Use
client.candidacies.update_step("cand_123", "interview")
sync_to_event_store("cand_123", "step_change", to_step="interview", user_id="user_456")
```

## Best Practices

### 1. Events are Immutable

```python
# ✅ Good - create new event
candidacy.change_step("interview")

# ❌ Bad - never modify events
event.data["step"] = "interview"  # DON'T DO THIS
```

### 2. Use Projections for Queries

```python
# ✅ Good - use projection
projection = CandidacyProjection(store)
active_candidates = projection.get_candidacies_by_status("active")

# ⭕ OK but slower - rebuild each candidacy
all_candidacies = []
for event in store.load_all_events():
    candidacy = EventSourcedCandidacy.load(event.aggregate_id, store)
    if candidacy.get_state()["status"] == "active":
        all_candidacies.append(candidacy.get_state())
```

### 3. Commit Events

```python
# ✅ Good - commit after changes
candidacy.change_step("interview")
candidacy.commit()

# ❌ Bad - events lost if not committed
candidacy.change_step("interview")
# Forgot to commit!
```

## Performance Tips

1. **Use snapshots for long event streams**: Save state periodically to avoid replaying thousands of events
2. **Use projections**: Build read models optimized for queries
3. **Use file-based or database event store**: In-memory is for testing only
4. **Batch event loading**: Load events in batches for large datasets

## Summary

✅ **Complete audit trail with immutable events**
✅ **Temporal queries - view state at any time**
✅ **Multiple projections from same events**
✅ **11 event types covering all candidacy changes**
✅ **3 store implementations (in-memory, file, custom)**
✅ **4 projections (state, timeline, audit, analytics)**
✅ **Type-safe with dataclasses**

Event sourcing provides a complete, immutable history of all candidacy changes, enabling powerful analytics, compliance, and temporal queries.
