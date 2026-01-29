"""
Tests for HERP Events

Tests for immutable event types and event sourcing foundation.
"""

from datetime import datetime

import pytest

from src.core.herp.events.events import (
    AssignmentAdded,
    AssignmentRemoved,
    CandidacyCreated,
    CandidacyEvent,
    CandidacyStatusChanged,
    CandidacyStepChanged,
    CandidacyTerminated,
    ContactAdded,
    ContactUpdated,
    Event,
    FileUploaded,
    TimelineCommentAdded,
)


class TestBaseEvent:
    """Test base Event class"""

    def test_event_initialization_with_defaults(self):
        """Test event created with auto-generated fields"""
        event = Event(
            event_type="TestEvent",
            aggregate_id="test_123",
        )

        # Auto-generated fields
        assert event.event_id is not None
        assert len(event.event_id) > 0  # UUID format
        assert isinstance(event.timestamp, datetime)
        assert event.version == 1
        assert event.data == {}
        assert event.metadata == {}

        # Provided fields
        assert event.event_type == "TestEvent"
        assert event.aggregate_id == "test_123"

    def test_event_initialization_with_all_fields(self):
        """Test event created with all fields specified"""
        timestamp = datetime(2026, 1, 29, 10, 0, 0)
        event = Event(
            event_id="evt_custom_123",
            event_type="CustomEvent",
            aggregate_id="agg_456",
            timestamp=timestamp,
            data={"key": "value"},
            metadata={"user_id": "user_789"},
            version=2,
        )

        assert event.event_id == "evt_custom_123"
        assert event.event_type == "CustomEvent"
        assert event.aggregate_id == "agg_456"
        assert event.timestamp == timestamp
        assert event.data == {"key": "value"}
        assert event.metadata == {"user_id": "user_789"}
        assert event.version == 2

    def test_event_to_dict(self):
        """Test event serialization to dict"""
        timestamp = datetime(2026, 1, 29, 10, 0, 0)
        event = Event(
            event_id="evt_123",
            event_type="TestEvent",
            aggregate_id="agg_456",
            timestamp=timestamp,
            data={"field": "value"},
            metadata={"user_id": "user_1"},
            version=1,
        )

        result = event.to_dict()

        assert result["event_id"] == "evt_123"
        assert result["event_type"] == "TestEvent"
        assert result["aggregate_id"] == "agg_456"
        assert result["timestamp"] == "2026-01-29T10:00:00"
        assert result["data"] == {"field": "value"}
        assert result["metadata"] == {"user_id": "user_1"}
        assert result["version"] == 1

    def test_event_from_dict(self):
        """Test event deserialization from dict"""
        data = {
            "event_id": "evt_789",
            "event_type": "DeserializedEvent",
            "aggregate_id": "agg_012",
            "timestamp": "2026-01-29T15:30:00",
            "data": {"key": "value"},
            "metadata": {"correlation_id": "corr_123"},
            "version": 2,
        }

        event = Event.from_dict(data)

        assert event.event_id == "evt_789"
        assert event.event_type == "DeserializedEvent"
        assert event.aggregate_id == "agg_012"
        assert event.timestamp == datetime(2026, 1, 29, 15, 30, 0)
        assert event.data == {"key": "value"}
        assert event.metadata == {"correlation_id": "corr_123"}
        assert event.version == 2

    def test_event_from_dict_with_minimal_fields(self):
        """Test from_dict with only required fields"""
        data = {
            "event_id": "evt_min",
            "event_type": "MinEvent",
            "aggregate_id": "agg_min",
            "timestamp": "2026-01-29T10:00:00",
        }

        event = Event.from_dict(data)

        assert event.event_id == "evt_min"
        assert event.data == {}
        assert event.metadata == {}
        assert event.version == 1

    def test_event_roundtrip_serialization(self):
        """Test event survives to_dict -> from_dict roundtrip"""
        original = Event(
            event_id="evt_round",
            event_type="RoundTripEvent",
            aggregate_id="agg_round",
            timestamp=datetime(2026, 1, 29, 12, 0, 0),
            data={"test": "data"},
            metadata={"test": "metadata"},
            version=1,
        )

        dict_form = original.to_dict()
        restored = Event.from_dict(dict_form)

        assert restored.event_id == original.event_id
        assert restored.event_type == original.event_type
        assert restored.aggregate_id == original.aggregate_id
        assert restored.timestamp == original.timestamp
        assert restored.data == original.data
        assert restored.metadata == original.metadata
        assert restored.version == original.version

    def test_event_is_immutable(self):
        """Test events are frozen (immutable)"""
        event = Event(event_type="ImmutableEvent", aggregate_id="agg_123")

        with pytest.raises(Exception):  # FrozenInstanceError
            event.event_type = "ChangedType"

        with pytest.raises(Exception):
            event.data = {"new": "data"}


class TestCandidacyEvent:
    """Test CandidacyEvent base class"""

    def test_candidacy_event_inherits_from_event(self):
        """Test CandidacyEvent is subclass of Event"""
        assert issubclass(CandidacyEvent, Event)

    def test_candidacy_event_creation(self):
        """Test creating CandidacyEvent directly"""
        event = CandidacyEvent(
            event_type="GenericCandidacyEvent",
            aggregate_id="cand_123",
        )

        assert isinstance(event, Event)
        assert event.aggregate_id == "cand_123"


class TestCandidacyCreated:
    """Test CandidacyCreated event"""

    def test_candidacy_created_event_type(self):
        """Test event type is set correctly"""
        event = CandidacyCreated.create(
            candidacy_id="cand_123",
            name="John Doe",
        )

        assert event.event_type == "CandidacyCreated"

    def test_candidacy_created_with_all_fields(self):
        """Test creating event with all optional fields"""
        event = CandidacyCreated.create(
            candidacy_id="cand_456",
            name="Jane Smith",
            email="jane@example.com",
            requisition_id="req_789",
            step="interview",
            status="active",
            tags=["experienced", "remote"],
            custom_fields={"years_experience": 5},
            user_id="user_recruiter_1",
        )

        assert event.aggregate_id == "cand_456"
        assert event.data["name"] == "Jane Smith"
        assert event.data["email"] == "jane@example.com"
        assert event.data["requisition_id"] == "req_789"
        assert event.data["step"] == "interview"
        assert event.data["status"] == "active"
        assert event.data["tags"] == ["experienced", "remote"]
        assert event.data["custom_fields"] == {"years_experience": 5}
        assert event.metadata == {"user_id": "user_recruiter_1"}

    def test_candidacy_created_with_minimal_fields(self):
        """Test creating event with only required fields"""
        event = CandidacyCreated.create(
            candidacy_id="cand_min",
            name="Minimal Candidate",
        )

        assert event.aggregate_id == "cand_min"
        assert event.data["name"] == "Minimal Candidate"
        assert event.data["email"] is None
        assert event.data["requisition_id"] is None
        assert event.data["step"] == "application"
        assert event.data["status"] == "active"
        assert event.data["tags"] == []
        assert event.data["custom_fields"] == {}
        assert event.metadata == {}

    def test_candidacy_created_without_user_id(self):
        """Test metadata is empty when user_id not provided"""
        event = CandidacyCreated.create(
            candidacy_id="cand_123",
            name="Test",
        )

        assert event.metadata == {}


class TestCandidacyStepChanged:
    """Test CandidacyStepChanged event"""

    def test_candidacy_step_changed_event_type(self):
        """Test event type is set correctly"""
        event = CandidacyStepChanged.create(
            candidacy_id="cand_123",
            from_step="application",
            to_step="interview",
        )

        assert event.event_type == "CandidacyStepChanged"

    def test_candidacy_step_changed_with_all_fields(self):
        """Test creating event with all fields"""
        event = CandidacyStepChanged.create(
            candidacy_id="cand_456",
            from_step="screening",
            to_step="technical_interview",
            comment="Strong initial screening performance",
            user_id="user_recruiter_1",
        )

        assert event.aggregate_id == "cand_456"
        assert event.data["from_step"] == "screening"
        assert event.data["to_step"] == "technical_interview"
        assert event.data["comment"] == "Strong initial screening performance"
        assert event.metadata == {"user_id": "user_recruiter_1"}

    def test_candidacy_step_changed_without_comment(self):
        """Test creating event without optional comment"""
        event = CandidacyStepChanged.create(
            candidacy_id="cand_123",
            from_step="application",
            to_step="screening",
        )

        assert event.data["comment"] is None


class TestCandidacyStatusChanged:
    """Test CandidacyStatusChanged event"""

    def test_candidacy_status_changed_event_type(self):
        """Test event type is set correctly"""
        event = CandidacyStatusChanged.create(
            candidacy_id="cand_123",
            from_status="active",
            to_status="terminated",
        )

        assert event.event_type == "CandidacyStatusChanged"

    def test_candidacy_status_changed_with_reason(self):
        """Test creating event with reason"""
        event = CandidacyStatusChanged.create(
            candidacy_id="cand_456",
            from_status="active",
            to_status="terminated",
            reason="hired",
            user_id="user_manager_1",
        )

        assert event.aggregate_id == "cand_456"
        assert event.data["from_status"] == "active"
        assert event.data["to_status"] == "terminated"
        assert event.data["reason"] == "hired"
        assert event.metadata == {"user_id": "user_manager_1"}


class TestCandidacyTerminated:
    """Test CandidacyTerminated event"""

    def test_candidacy_terminated_event_type(self):
        """Test event type is set correctly"""
        event = CandidacyTerminated.create(
            candidacy_id="cand_123",
            reason="hired",
        )

        assert event.event_type == "CandidacyTerminated"

    def test_candidacy_terminated_with_all_fields(self):
        """Test creating event with all fields"""
        event = CandidacyTerminated.create(
            candidacy_id="cand_456",
            reason="hired",
            comment="Excellent candidate, accepted offer",
            final_step="offer",
            user_id="user_manager_1",
        )

        assert event.aggregate_id == "cand_456"
        assert event.data["reason"] == "hired"
        assert event.data["comment"] == "Excellent candidate, accepted offer"
        assert event.data["final_step"] == "offer"
        assert event.metadata == {"user_id": "user_manager_1"}

    def test_candidacy_terminated_rejected(self):
        """Test termination with rejection"""
        event = CandidacyTerminated.create(
            candidacy_id="cand_789",
            reason="rejected",
            comment="Not a good fit for role",
            final_step="technical_interview",
        )

        assert event.data["reason"] == "rejected"


class TestContactAdded:
    """Test ContactAdded event"""

    def test_contact_added_event_type(self):
        """Test event type is set correctly"""
        event = ContactAdded.create(
            candidacy_id="cand_123",
            contact_id="contact_456",
            contact_type="phone_screen",
        )

        assert event.event_type == "ContactAdded"

    def test_contact_added_with_all_fields(self):
        """Test creating event with all fields"""
        event = ContactAdded.create(
            candidacy_id="cand_123",
            contact_id="contact_456",
            contact_type="technical_interview",
            scheduled_at="2026-02-01T10:00:00Z",
            interviewer_ids=["user_1", "user_2"],
            title="Technical Screen - Python",
            user_id="user_recruiter",
        )

        assert event.aggregate_id == "cand_123"
        assert event.data["contact_id"] == "contact_456"
        assert event.data["type"] == "technical_interview"
        assert event.data["scheduled_at"] == "2026-02-01T10:00:00Z"
        assert event.data["interviewer_ids"] == ["user_1", "user_2"]
        assert event.data["title"] == "Technical Screen - Python"
        assert event.metadata == {"user_id": "user_recruiter"}

    def test_contact_added_with_minimal_fields(self):
        """Test creating event with minimal fields"""
        event = ContactAdded.create(
            candidacy_id="cand_123",
            contact_id="contact_789",
            contact_type="casual_conversation",
        )

        assert event.data["scheduled_at"] is None
        assert event.data["interviewer_ids"] == []
        assert event.data["title"] is None


class TestContactUpdated:
    """Test ContactUpdated event"""

    def test_contact_updated_event_type(self):
        """Test event type is set correctly"""
        event = ContactUpdated.create(
            candidacy_id="cand_123",
            contact_id="contact_456",
            changes={},
        )

        assert event.event_type == "ContactUpdated"

    def test_contact_updated_with_changes(self):
        """Test creating event with changes"""
        changes = {
            "scheduled_at": "2026-02-02T14:00:00Z",
            "interviewer_ids": ["user_3", "user_4"],
        }

        event = ContactUpdated.create(
            candidacy_id="cand_123",
            contact_id="contact_456",
            changes=changes,
            user_id="user_recruiter",
        )

        assert event.aggregate_id == "cand_123"
        assert event.data["contact_id"] == "contact_456"
        assert event.data["changes"] == changes
        assert event.metadata == {"user_id": "user_recruiter"}


class TestFileUploaded:
    """Test FileUploaded event"""

    def test_file_uploaded_event_type(self):
        """Test event type is set correctly"""
        event = FileUploaded.create(
            candidacy_id="cand_123",
            file_id="file_456",
            file_name="resume.pdf",
            file_type="resume",
        )

        assert event.event_type == "FileUploaded"

    def test_file_uploaded_with_all_fields(self):
        """Test creating event with all fields"""
        event = FileUploaded.create(
            candidacy_id="cand_123",
            file_id="file_456",
            file_name="john_doe_resume.pdf",
            file_type="resume",
            file_size=1024000,
            user_id="user_candidate",
        )

        assert event.aggregate_id == "cand_123"
        assert event.data["file_id"] == "file_456"
        assert event.data["file_name"] == "john_doe_resume.pdf"
        assert event.data["file_type"] == "resume"
        assert event.data["file_size"] == 1024000
        assert event.metadata == {"user_id": "user_candidate"}

    def test_file_uploaded_without_size(self):
        """Test creating event without file size"""
        event = FileUploaded.create(
            candidacy_id="cand_123",
            file_id="file_789",
            file_name="cover_letter.txt",
            file_type="other",
        )

        assert event.data["file_size"] is None


class TestTimelineCommentAdded:
    """Test TimelineCommentAdded event"""

    def test_timeline_comment_added_event_type(self):
        """Test event type is set correctly"""
        event = TimelineCommentAdded.create(
            candidacy_id="cand_123",
            comment_id="comment_456",
            comment="Great interview",
        )

        assert event.event_type == "TimelineCommentAdded"

    def test_timeline_comment_added_with_all_fields(self):
        """Test creating event with all fields"""
        event = TimelineCommentAdded.create(
            candidacy_id="cand_123",
            comment_id="comment_456",
            comment="# Interview Feedback\n\n**Technical Skills**: Excellent\n",
            format="text/markdown",
            user_id="user_interviewer",
        )

        assert event.aggregate_id == "cand_123"
        assert event.data["comment_id"] == "comment_456"
        assert "Interview Feedback" in event.data["comment"]
        assert event.data["format"] == "text/markdown"
        assert event.metadata == {"user_id": "user_interviewer"}

    def test_timeline_comment_added_default_format(self):
        """Test creating event with default format"""
        event = TimelineCommentAdded.create(
            candidacy_id="cand_123",
            comment_id="comment_789",
            comment="Plain text comment",
        )

        assert event.data["format"] == "text/plain"


class TestAssignmentAdded:
    """Test AssignmentAdded event"""

    def test_assignment_added_event_type(self):
        """Test event type is set correctly"""
        event = AssignmentAdded.create(
            candidacy_id="cand_123",
            assigned_user_id="user_456",
        )

        assert event.event_type == "AssignmentAdded"

    def test_assignment_added_with_all_fields(self):
        """Test creating event with all fields"""
        event = AssignmentAdded.create(
            candidacy_id="cand_123",
            assigned_user_id="user_interviewer",
            role="interviewer",
            by_user_id="user_recruiter",
        )

        assert event.aggregate_id == "cand_123"
        assert event.data["user_id"] == "user_interviewer"
        assert event.data["role"] == "interviewer"
        assert event.metadata == {"user_id": "user_recruiter"}

    def test_assignment_added_default_role(self):
        """Test creating event with default role"""
        event = AssignmentAdded.create(
            candidacy_id="cand_123",
            assigned_user_id="user_456",
        )

        assert event.data["role"] == "recruiter"


class TestAssignmentRemoved:
    """Test AssignmentRemoved event"""

    def test_assignment_removed_event_type(self):
        """Test event type is set correctly"""
        event = AssignmentRemoved.create(
            candidacy_id="cand_123",
            unassigned_user_id="user_456",
        )

        assert event.event_type == "AssignmentRemoved"

    def test_assignment_removed_with_all_fields(self):
        """Test creating event with all fields"""
        event = AssignmentRemoved.create(
            candidacy_id="cand_123",
            unassigned_user_id="user_interviewer",
            by_user_id="user_recruiter",
        )

        assert event.aggregate_id == "cand_123"
        assert event.data["user_id"] == "user_interviewer"
        assert event.metadata == {"user_id": "user_recruiter"}

    def test_assignment_removed_without_metadata(self):
        """Test creating event without metadata"""
        event = AssignmentRemoved.create(
            candidacy_id="cand_123",
            unassigned_user_id="user_456",
        )

        assert event.metadata == {}


class TestEventIntegration:
    """Integration tests for event usage patterns"""

    def test_event_workflow_candidacy_lifecycle(self):
        """Test complete candidacy lifecycle with events"""
        # Create candidacy
        created = CandidacyCreated.create(
            candidacy_id="cand_lifecycle",
            name="Lifecycle Candidate",
            email="lifecycle@example.com",
            requisition_id="req_001",
        )

        assert created.event_type == "CandidacyCreated"

        # Change step
        step_changed = CandidacyStepChanged.create(
            candidacy_id="cand_lifecycle",
            from_step="application",
            to_step="interview",
        )

        assert step_changed.aggregate_id == created.aggregate_id

        # Add contact
        contact_added = ContactAdded.create(
            candidacy_id="cand_lifecycle",
            contact_id="contact_001",
            contact_type="technical_interview",
        )

        assert contact_added.aggregate_id == created.aggregate_id

        # Terminate
        terminated = CandidacyTerminated.create(
            candidacy_id="cand_lifecycle",
            reason="hired",
            final_step="offer",
        )

        assert terminated.aggregate_id == created.aggregate_id

    def test_events_can_be_serialized_and_deserialized(self):
        """Test events survive serialization roundtrip"""
        events = [
            CandidacyCreated.create("cand_1", "Test 1"),
            CandidacyStepChanged.create("cand_1", "app", "interview"),
            ContactAdded.create("cand_1", "contact_1", "phone_screen"),
            FileUploaded.create("cand_1", "file_1", "resume.pdf", "resume"),
            TimelineCommentAdded.create("cand_1", "comm_1", "Great candidate"),
            AssignmentAdded.create("cand_1", "user_1"),
        ]

        for event in events:
            dict_form = event.to_dict()
            # Can recreate base Event from dict
            restored = Event.from_dict(dict_form)
            assert restored.event_type == event.event_type
            assert restored.aggregate_id == event.aggregate_id
            assert restored.data == event.data

    def test_all_events_are_immutable(self):
        """Test all event types are frozen"""
        events = [
            CandidacyCreated.create("cand_1", "Test"),
            CandidacyStepChanged.create("cand_1", "a", "b"),
            CandidacyStatusChanged.create("cand_1", "active", "terminated"),
            CandidacyTerminated.create("cand_1", "hired"),
            ContactAdded.create("cand_1", "c1", "phone"),
            ContactUpdated.create("cand_1", "c1", {}),
            FileUploaded.create("cand_1", "f1", "file.pdf", "resume"),
            TimelineCommentAdded.create("cand_1", "comm_1", "comment"),
            AssignmentAdded.create("cand_1", "u1"),
            AssignmentRemoved.create("cand_1", "u1"),
        ]

        for event in events:
            with pytest.raises(Exception):  # FrozenInstanceError
                event.event_type = "Modified"
