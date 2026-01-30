"""
Tests for HERP Event-Sourced Aggregate

Tests for event-sourced candidacy aggregate with state reconstruction.
"""

from datetime import timedelta

import pytest

from src.core.herp.events.aggregate import EventSourcedCandidacy
from src.core.herp.events.event_store import InMemoryEventStore
from src.core.herp.events.events import CandidacyCreated, CandidacyStepChanged


class TestEventSourcedCandidacyCreation:
    """Test creating event-sourced candidacy"""

    @pytest.fixture
    def store(self):
        """Create fresh event store for each test"""
        return InMemoryEventStore()

    def test_create_candidacy_with_minimal_fields(self, store):
        """Test creating candidacy with minimal required fields"""
        candidacy = EventSourcedCandidacy.create(
            candidacy_id="cand_min",
            name="Minimal User",
            event_store=store,
        )

        state = candidacy.get_state()

        assert state["candidacy_id"] == "cand_min"
        assert state["name"] == "Minimal User"
        assert state["status"] == "active"
        assert state["step"] == "application"

    def test_create_candidacy_with_all_fields(self, store):
        """Test creating candidacy with all optional fields"""
        candidacy = EventSourcedCandidacy.create(
            candidacy_id="cand_full",
            name="Full User",
            email="full@example.com",
            requisition_id="req_123",
            step="screening",
            tags=["experienced", "remote"],
            event_store=store,
            user_id="user_recruiter",
        )

        state = candidacy.get_state()

        assert state["name"] == "Full User"
        assert state["email"] == "full@example.com"
        assert state["requisition_id"] == "req_123"
        assert state["step"] == "screening"
        assert state["tags"] == ["experienced", "remote"]

    def test_create_stores_event_when_store_provided(self, store):
        """Test create() commits event when event_store provided"""
        candidacy = EventSourcedCandidacy.create(
            candidacy_id="cand_123",
            name="Test User",
            event_store=store,
        )

        # Event should be in store
        events = store.load_events("cand_123")
        assert len(events) == 1
        assert events[0].event_type == "CandidacyCreated"


class TestEventSourcedCandidacyLoading:
    """Test loading event-sourced candidacy"""

    @pytest.fixture
    def store_with_events(self):
        """Create store with sample candidacy events"""
        store = InMemoryEventStore()

        # Create candidacy
        created = CandidacyCreated.create(
            candidacy_id="cand_existing",
            name="Existing User",
            email="existing@example.com",
            requisition_id="req_456",
        )
        store.append(created)

        # Change step
        step_changed = CandidacyStepChanged.create(
            candidacy_id="cand_existing",
            from_step="application",
            to_step="interview",
        )
        store.append(step_changed)

        return store

    def test_load_candidacy_from_store(self, store_with_events):
        """Test loading candidacy from event store"""
        candidacy = EventSourcedCandidacy.load("cand_existing", store_with_events)

        assert candidacy.candidacy_id == "cand_existing"
        assert len(candidacy.events) == 2

    def test_load_rebuilds_state_from_events(self, store_with_events):
        """Test loaded candidacy has correct state"""
        candidacy = EventSourcedCandidacy.load("cand_existing", store_with_events)

        state = candidacy.get_state()

        assert state["name"] == "Existing User"
        assert state["email"] == "existing@example.com"
        assert state["step"] == "interview"  # Changed from application

    def test_load_nonexistent_candidacy(self):
        """Test loading candidacy with no events"""
        store = InMemoryEventStore()
        candidacy = EventSourcedCandidacy.load("nonexistent", store)

        assert len(candidacy.events) == 0
        state = candidacy.get_state()
        assert state["name"] is None


class TestStateReconstruction:
    """Test state reconstruction from events"""

    @pytest.fixture
    def candidacy(self):
        """Create candidacy with multiple events"""
        store = InMemoryEventStore()
        candidacy = EventSourcedCandidacy.create(
            candidacy_id="cand_state",
            name="State Test User",
            email="state@example.com",
            event_store=store,
        )

        candidacy.change_step("screening", user_id="user_1")
        candidacy.commit()

        candidacy.change_step("interview", user_id="user_2")
        candidacy.commit()

        return candidacy

    def test_get_state_returns_current_state(self, candidacy):
        """Test get_state() returns latest state"""
        state = candidacy.get_state()

        assert state["name"] == "State Test User"
        assert state["step"] == "interview"  # Latest step

    def test_get_state_includes_all_expected_fields(self, candidacy):
        """Test state includes all expected fields"""
        state = candidacy.get_state()

        required_fields = [
            "candidacy_id",
            "name",
            "email",
            "requisition_id",
            "step",
            "status",
            "tags",
            "custom_fields",
            "contacts",
            "files",
            "timeline_comments",
            "assignments",
            "created_at",
            "updated_at",
            "terminated_at",
        ]

        for field in required_fields:
            assert field in state

    def test_get_state_at_temporal_query(self):
        """Test get_state_at() filters events by timestamp"""
        store = InMemoryEventStore()

        candidacy = EventSourcedCandidacy.create(
            candidacy_id="cand_temporal",
            name="Temporal User",
            event_store=store,
        )

        # Get creation timestamp
        state1 = candidacy.get_state()
        created_at = state1["created_at"]

        # Make a change
        candidacy.change_step("screening")
        candidacy.commit()

        # State at creation time should have application step
        state_at_creation = candidacy.get_state_at(
            created_at + timedelta(microseconds=1)
        )
        assert state_at_creation["step"] == "application"

        # Current state should have screening step
        current_state = candidacy.get_state()
        assert current_state["step"] == "screening"


class TestCandidacyCommands:
    """Test candidacy command methods"""

    @pytest.fixture
    def candidacy(self):
        """Create candidacy for testing"""
        store = InMemoryEventStore()
        return EventSourcedCandidacy.create(
            candidacy_id="cand_commands",
            name="Commands Test",
            event_store=store,
        )

    def test_change_step(self, candidacy):
        """Test changing hiring step"""
        candidacy.change_step("screening", comment="Strong application", user_id="u1")
        candidacy.commit()

        state = candidacy.get_state()
        assert state["step"] == "screening"

    def test_change_status(self, candidacy):
        """Test changing candidacy status"""
        candidacy.change_status("terminated", reason="hired", user_id="u1")
        candidacy.commit()

        state = candidacy.get_state()
        assert state["status"] == "terminated"

    def test_terminate(self, candidacy):
        """Test terminating candidacy"""
        candidacy.terminate("hired", comment="Accepted offer", user_id="u1")
        candidacy.commit()

        state = candidacy.get_state()
        assert state["terminated_at"] is not None
        assert state["status"] == "terminated"

    def test_add_contact(self, candidacy):
        """Test adding contact/interview"""
        candidacy.add_contact(
            contact_id="contact_123",
            contact_type="phone_screen",
            scheduled_at="2026-02-01T10:00:00Z",
            interviewer_ids=["user_1", "user_2"],
            title="Phone Screen",
            user_id="recruiter_1",
        )
        candidacy.commit()

        state = candidacy.get_state()
        assert len(state["contacts"]) == 1
        assert state["contacts"][0]["contact_id"] == "contact_123"

    def test_update_contact(self, candidacy):
        """Test updating existing contact"""
        candidacy.add_contact("contact_456", "interview")
        candidacy.commit()

        candidacy.update_contact(
            contact_id="contact_456",
            changes={"scheduled_at": "2026-02-02T14:00:00Z"},
        )
        candidacy.commit()

        state = candidacy.get_state()
        assert state["contacts"][0]["scheduled_at"] == "2026-02-02T14:00:00Z"

    def test_upload_file(self, candidacy):
        """Test uploading file"""
        candidacy.upload_file(
            file_id="file_789",
            file_name="resume.pdf",
            file_type="resume",
            file_size=1024000,
        )
        candidacy.commit()

        state = candidacy.get_state()
        assert len(state["files"]) == 1
        assert state["files"][0]["file_name"] == "resume.pdf"

    def test_add_timeline_comment(self, candidacy):
        """Test adding timeline comment"""
        candidacy.add_timeline_comment(
            comment_id="comment_001",
            comment="Great technical skills",
            user_id="interviewer_1",
        )
        candidacy.commit()

        state = candidacy.get_state()
        assert len(state["timeline_comments"]) == 1
        assert state["timeline_comments"][0]["comment"] == "Great technical skills"

    def test_assign_user(self, candidacy):
        """Test assigning team member"""
        candidacy.assign_user(assigned_user_id="user_123", role="interviewer")
        candidacy.commit()

        state = candidacy.get_state()
        assert len(state["assignments"]) == 1
        assert state["assignments"][0]["user_id"] == "user_123"

    def test_unassign_user(self, candidacy):
        """Test unassigning team member"""
        candidacy.assign_user("user_456", role="recruiter")
        candidacy.commit()

        candidacy.unassign_user("user_456")
        candidacy.commit()

        state = candidacy.get_state()
        assert len(state["assignments"]) == 0


class TestEventManagement:
    """Test event management and commits"""

    @pytest.fixture
    def store(self):
        """Create event store"""
        return InMemoryEventStore()

    def test_uncommitted_events_accumulate(self, store):
        """Test uncommitted events accumulate before commit"""
        candidacy = EventSourcedCandidacy.create(
            candidacy_id="cand_uncommit",
            name="Test",
            event_store=store,
        )

        candidacy.change_step("screening")
        candidacy.change_step("interview")

        assert len(candidacy.uncommitted_events) == 2

    def test_commit_persists_events(self, store):
        """Test commit() persists events to store"""
        candidacy = EventSourcedCandidacy.create(
            candidacy_id="cand_persist",
            name="Test",
            event_store=store,
        )

        candidacy.change_step("screening")
        candidacy.change_step("interview")

        assert store.count_by_aggregate("cand_persist") == 1  # Only CandidacyCreated

        candidacy.commit()

        assert store.count_by_aggregate("cand_persist") == 3  # All 3 events

    def test_commit_clears_uncommitted_events(self, store):
        """Test commit() clears uncommitted events"""
        candidacy = EventSourcedCandidacy.create(
            candidacy_id="cand_clear",
            name="Test",
            event_store=store,
        )

        candidacy.change_step("screening")
        assert len(candidacy.uncommitted_events) == 1

        candidacy.commit()
        assert len(candidacy.uncommitted_events) == 0

    def test_get_events_returns_all_events(self, store):
        """Test get_events() returns copy of all events"""
        candidacy = EventSourcedCandidacy.create(
            candidacy_id="cand_events",
            name="Test",
            event_store=store,
        )

        candidacy.change_step("screening")
        candidacy.commit()

        events = candidacy.get_events()

        assert len(events) == 2
        assert events[0].event_type == "CandidacyCreated"
        assert events[1].event_type == "CandidacyStepChanged"

    def test_get_event_history_returns_formatted_history(self, store):
        """Test get_event_history() returns formatted list"""
        candidacy = EventSourcedCandidacy.create(
            candidacy_id="cand_history",
            name="Test",
            event_store=store,
        )

        candidacy.change_step("screening", user_id="user_1")
        candidacy.commit()

        history = candidacy.get_event_history()

        assert len(history) == 2
        assert "timestamp" in history[0]
        assert "event_type" in history[0]


class TestAggregateIntegration:
    """Integration tests for aggregate usage patterns"""

    def test_complete_candidacy_lifecycle(self):
        """Test complete candidacy lifecycle with aggregate"""
        store = InMemoryEventStore()

        candidacy = EventSourcedCandidacy.create(
            candidacy_id="cand_lifecycle",
            name="Lifecycle Test",
            event_store=store,
        )

        candidacy.change_step("screening")
        candidacy.commit()

        candidacy.add_contact("contact_1", "technical_interview")
        candidacy.commit()

        candidacy.terminate("hired", comment="Great candidate")
        candidacy.commit()

        state = candidacy.get_state()
        assert len(state["contacts"]) == 1
        assert state["terminated_at"] is not None

        # Created + step + contact + terminate + status = 5 events
        assert store.count_by_aggregate("cand_lifecycle") >= 4

    def test_load_and_continue_workflow(self):
        """Test loading existing candidacy and continuing workflow"""
        store = InMemoryEventStore()

        candidacy1 = EventSourcedCandidacy.create(
            candidacy_id="cand_continue",
            name="Continue Test",
            event_store=store,
        )
        candidacy1.change_step("screening")
        candidacy1.commit()

        candidacy2 = EventSourcedCandidacy.load("cand_continue", store)

        candidacy2.change_step("interview")
        candidacy2.commit()

        state = candidacy2.get_state()
        assert state["step"] == "interview"

        events = store.load_events("cand_continue")
        assert len(events) == 3

    def test_event_sourcing_ensures_consistency(self):
        """Test event sourcing maintains consistency"""
        store = InMemoryEventStore()

        candidacy = EventSourcedCandidacy.create(
            candidacy_id="cand_consistency",
            name="Consistency Test",
            event_store=store,
        )

        for i in range(5):
            candidacy.change_step(f"step_{i}")

        candidacy.commit()

        reloaded = EventSourcedCandidacy.load("cand_consistency", store)

        assert candidacy.get_state() == reloaded.get_state()
        assert len(candidacy.get_events()) == len(reloaded.get_events())
