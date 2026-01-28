"""
Tests for HERP Event Sourcing Events
"""

from datetime import datetime

import pytest

from src.core.herp.events.events import (
    AssignmentAdded,
    AssignmentRemoved,
    CandidacyCreated,
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

    def test_event_initialization(self):
        """Test creating base event"""
        event = Event(
            event_type="TestEvent",
            aggregate_id="agg_123",
            data={"key": "value"},
            metadata={"user_id": "user_1"},
        )

        assert event.event_type == "TestEvent"
        assert event.aggregate_id == "agg_123"
        assert event.data == {"key": "value"}
        assert event.metadata == {"user_id": "user_1"}
        assert event.version == 1
        assert event.event_id  # Should have generated UUID

    def test_event_is_immutable(self):
        """Test event is frozen/immutable"""
        event = Event(event_type="Test", aggregate_id="agg_123")

        with pytest.raises(Exception):  # FrozenInstanceError
            event.event_type = "Modified"

    def test_event_generates_unique_id(self):
        """Test each event gets unique ID"""
        event1 = Event(event_type="Test", aggregate_id="agg_123")
        event2 = Event(event_type="Test", aggregate_id="agg_123")

        assert event1.event_id != event2.event_id

    def test_event_has_timestamp(self):
        """Test event has timestamp"""
        before = datetime.now()
        event = Event(event_type="Test", aggregate_id="agg_123")
        after = datetime.now()

        assert before <= event.timestamp <= after

    def test_event_to_dict(self):
        """Test converting event to dictionary"""
        timestamp = datetime(2026, 1, 15, 10, 30, 0)
        event = Event(
            event_id="evt_123",
            event_type="TestEvent",
            aggregate_id="agg_456",
            timestamp=timestamp,
            data={"field": "value"},
            metadata={"user_id": "user_1"},
            version=2,
        )

        result = event.to_dict()

        assert result["event_id"] == "evt_123"
        assert result["event_type"] == "TestEvent"
        assert result["aggregate_id"] == "agg_456"
        assert result["timestamp"] == "2026-01-15T10:30:00"
        assert result["data"] == {"field": "value"}
        assert result["metadata"] == {"user_id": "user_1"}
        assert result["version"] == 2

    def test_event_from_dict(self):
        """Test creating event from dictionary"""
        data = {
            "event_id": "evt_123",
            "event_type": "TestEvent",
            "aggregate_id": "agg_456",
            "timestamp": "2026-01-15T10:30:00",
            "data": {"field": "value"},
            "metadata": {"user_id": "user_1"},
            "version": 2,
        }

        event = Event.from_dict(data)

        assert event.event_id == "evt_123"
        assert event.event_type == "TestEvent"
        assert event.aggregate_id == "agg_456"
        assert event.timestamp == datetime(2026, 1, 15, 10, 30, 0)
        assert event.data == {"field": "value"}
        assert event.metadata == {"user_id": "user_1"}
        assert event.version == 2

    def test_event_from_dict_minimal(self):
        """Test creating event from minimal dictionary"""
        data = {
            "event_id": "evt_123",
            "event_type": "TestEvent",
            "aggregate_id": "agg_456",
            "timestamp": "2026-01-15T10:30:00",
        }

        event = Event.from_dict(data)

        assert event.event_id == "evt_123"
        assert event.data == {}
        assert event.metadata == {}
        assert event.version == 1

    def test_event_round_trip_serialization(self):
        """Test event can be serialized and deserialized"""
        original = Event(
            event_type="TestEvent",
            aggregate_id="agg_123",
            data={"key": "value"},
            metadata={"user_id": "user_1"},
        )

        # Serialize to dict
        event_dict = original.to_dict()

        # Deserialize from dict
        reconstructed = Event.from_dict(event_dict)

        assert reconstructed.event_id == original.event_id
        assert reconstructed.event_type == original.event_type
        assert reconstructed.aggregate_id == original.aggregate_id
        assert reconstructed.data == original.data
        assert reconstructed.metadata == original.metadata


class TestCandidacyCreated:
    """Test CandidacyCreated event"""

    def test_create_candidacy_created(self):
        """Test creating CandidacyCreated event"""
        event = CandidacyCreated.create(
            candidacy_id="cand_123",
            name="Alice Smith",
            email="alice@example.com",
            requisition_id="req_001",
            step="application",
            status="active",
            tags=["python", "senior"],
            custom_fields={"years_experience": 5},
            user_id="user_recruiter",
        )

        assert event.event_type == "CandidacyCreated"
        assert event.aggregate_id == "cand_123"
        assert event.data["name"] == "Alice Smith"
        assert event.data["email"] == "alice@example.com"
        assert event.data["requisition_id"] == "req_001"
        assert event.data["step"] == "application"
        assert event.data["status"] == "active"
        assert event.data["tags"] == ["python", "senior"]
        assert event.data["custom_fields"] == {"years_experience": 5}
        assert event.metadata["user_id"] == "user_recruiter"

    def test_create_candidacy_created_minimal(self):
        """Test creating CandidacyCreated with minimal data"""
        event = CandidacyCreated.create(candidacy_id="cand_123", name="Alice Smith")

        assert event.event_type == "CandidacyCreated"
        assert event.aggregate_id == "cand_123"
        assert event.data["name"] == "Alice Smith"
        assert event.data["email"] is None
        assert event.data["tags"] == []
        assert event.data["custom_fields"] == {}
        assert event.metadata == {}

    def test_candidacy_created_is_immutable(self):
        """Test CandidacyCreated is immutable"""
        event = CandidacyCreated.create(candidacy_id="cand_123", name="Alice")

        with pytest.raises(Exception):
            event.aggregate_id = "modified"


class TestCandidacyStepChanged:
    """Test CandidacyStepChanged event"""

    def test_create_candidacy_step_changed(self):
        """Test creating CandidacyStepChanged event"""
        event = CandidacyStepChanged.create(
            candidacy_id="cand_123",
            from_step="application",
            to_step="phone_screen",
            comment="Moving to next stage",
            user_id="user_recruiter",
        )

        assert event.event_type == "CandidacyStepChanged"
        assert event.aggregate_id == "cand_123"
        assert event.data["from_step"] == "application"
        assert event.data["to_step"] == "phone_screen"
        assert event.data["comment"] == "Moving to next stage"
        assert event.metadata["user_id"] == "user_recruiter"

    def test_create_candidacy_step_changed_no_comment(self):
        """Test creating step change without comment"""
        event = CandidacyStepChanged.create(
            candidacy_id="cand_123", from_step="interview", to_step="offer"
        )

        assert event.data["comment"] is None
        assert event.metadata == {}


class TestCandidacyStatusChanged:
    """Test CandidacyStatusChanged event"""

    def test_create_candidacy_status_changed(self):
        """Test creating CandidacyStatusChanged event"""
        event = CandidacyStatusChanged.create(
            candidacy_id="cand_123",
            from_status="active",
            to_status="terminated",
            reason="hired",
            user_id="user_manager",
        )

        assert event.event_type == "CandidacyStatusChanged"
        assert event.aggregate_id == "cand_123"
        assert event.data["from_status"] == "active"
        assert event.data["to_status"] == "terminated"
        assert event.data["reason"] == "hired"
        assert event.metadata["user_id"] == "user_manager"

    def test_create_candidacy_status_changed_minimal(self):
        """Test creating status change without reason"""
        event = CandidacyStatusChanged.create(
            candidacy_id="cand_123", from_status="active", to_status="on_hold"
        )

        assert event.data["reason"] is None


class TestCandidacyTerminated:
    """Test CandidacyTerminated event"""

    def test_create_candidacy_terminated(self):
        """Test creating CandidacyTerminated event"""
        event = CandidacyTerminated.create(
            candidacy_id="cand_123",
            reason="hired",
            comment="Accepted offer, starts next month",
            final_step="offer",
            user_id="user_recruiter",
        )

        assert event.event_type == "CandidacyTerminated"
        assert event.aggregate_id == "cand_123"
        assert event.data["reason"] == "hired"
        assert event.data["comment"] == "Accepted offer, starts next month"
        assert event.data["final_step"] == "offer"
        assert event.metadata["user_id"] == "user_recruiter"

    def test_create_candidacy_terminated_rejected(self):
        """Test creating termination event for rejection"""
        event = CandidacyTerminated.create(
            candidacy_id="cand_123", reason="rejected", final_step="technical_interview"
        )

        assert event.data["reason"] == "rejected"
        assert event.data["comment"] is None


class TestContactAdded:
    """Test ContactAdded event"""

    def test_create_contact_added(self):
        """Test creating ContactAdded event"""
        event = ContactAdded.create(
            candidacy_id="cand_123",
            contact_id="contact_456",
            contact_type="technical_interview",
            scheduled_at="2026-02-01T10:00:00Z",
            interviewer_ids=["user_1", "user_2"],
            title="Senior Engineer Technical Screen",
            user_id="user_recruiter",
        )

        assert event.event_type == "ContactAdded"
        assert event.aggregate_id == "cand_123"
        assert event.data["contact_id"] == "contact_456"
        assert event.data["type"] == "technical_interview"
        assert event.data["scheduled_at"] == "2026-02-01T10:00:00Z"
        assert event.data["interviewer_ids"] == ["user_1", "user_2"]
        assert event.data["title"] == "Senior Engineer Technical Screen"
        assert event.metadata["user_id"] == "user_recruiter"

    def test_create_contact_added_minimal(self):
        """Test creating contact with minimal data"""
        event = ContactAdded.create(
            candidacy_id="cand_123",
            contact_id="contact_456",
            contact_type="phone_screen",
        )

        assert event.data["interviewer_ids"] == []
        assert event.data["scheduled_at"] is None


class TestContactUpdated:
    """Test ContactUpdated event"""

    def test_create_contact_updated(self):
        """Test creating ContactUpdated event"""
        changes = {
            "scheduled_at": "2026-02-02T15:00:00Z",
            "interviewer_ids": ["user_3"],
        }

        event = ContactUpdated.create(
            candidacy_id="cand_123",
            contact_id="contact_456",
            changes=changes,
            user_id="user_recruiter",
        )

        assert event.event_type == "ContactUpdated"
        assert event.aggregate_id == "cand_123"
        assert event.data["contact_id"] == "contact_456"
        assert event.data["changes"] == changes
        assert event.metadata["user_id"] == "user_recruiter"


class TestFileUploaded:
    """Test FileUploaded event"""

    def test_create_file_uploaded(self):
        """Test creating FileUploaded event"""
        event = FileUploaded.create(
            candidacy_id="cand_123",
            file_id="file_789",
            file_name="resume.pdf",
            file_type="resume",
            file_size=102400,
            user_id="user_candidate",
        )

        assert event.event_type == "FileUploaded"
        assert event.aggregate_id == "cand_123"
        assert event.data["file_id"] == "file_789"
        assert event.data["file_name"] == "resume.pdf"
        assert event.data["file_type"] == "resume"
        assert event.data["file_size"] == 102400
        assert event.metadata["user_id"] == "user_candidate"

    def test_create_file_uploaded_no_size(self):
        """Test creating file upload without size"""
        event = FileUploaded.create(
            candidacy_id="cand_123",
            file_id="file_789",
            file_name="resume.pdf",
            file_type="resume",
        )

        assert event.data["file_size"] is None


class TestTimelineCommentAdded:
    """Test TimelineCommentAdded event"""

    def test_create_timeline_comment_added(self):
        """Test creating TimelineCommentAdded event"""
        event = TimelineCommentAdded.create(
            candidacy_id="cand_123",
            comment_id="comment_101",
            comment="Great technical skills demonstrated",
            format="text/plain",
            user_id="user_interviewer",
        )

        assert event.event_type == "TimelineCommentAdded"
        assert event.aggregate_id == "cand_123"
        assert event.data["comment_id"] == "comment_101"
        assert event.data["comment"] == "Great technical skills demonstrated"
        assert event.data["format"] == "text/plain"
        assert event.metadata["user_id"] == "user_interviewer"

    def test_create_timeline_comment_markdown(self):
        """Test creating timeline comment with markdown"""
        comment_text = (
            "## Technical Assessment\n\n- Strong problem solving\n- Great communication"
        )

        event = TimelineCommentAdded.create(
            candidacy_id="cand_123",
            comment_id="comment_102",
            comment=comment_text,
            format="text/markdown",
        )

        assert event.data["comment"] == comment_text
        assert event.data["format"] == "text/markdown"

    def test_create_timeline_comment_default_format(self):
        """Test timeline comment defaults to text/plain"""
        event = TimelineCommentAdded.create(
            candidacy_id="cand_123", comment_id="comment_103", comment="Test"
        )

        assert event.data["format"] == "text/plain"


class TestAssignmentAdded:
    """Test AssignmentAdded event"""

    def test_create_assignment_added(self):
        """Test creating AssignmentAdded event"""
        event = AssignmentAdded.create(
            candidacy_id="cand_123",
            assigned_user_id="user_recruiter_1",
            role="recruiter",
            by_user_id="user_admin",
        )

        assert event.event_type == "AssignmentAdded"
        assert event.aggregate_id == "cand_123"
        assert event.data["user_id"] == "user_recruiter_1"
        assert event.data["role"] == "recruiter"
        assert event.metadata["user_id"] == "user_admin"

    def test_create_assignment_added_hiring_manager(self):
        """Test creating assignment for hiring manager"""
        event = AssignmentAdded.create(
            candidacy_id="cand_123",
            assigned_user_id="user_manager_1",
            role="hiring_manager",
        )

        assert event.data["role"] == "hiring_manager"

    def test_create_assignment_added_default_role(self):
        """Test assignment defaults to recruiter role"""
        event = AssignmentAdded.create(
            candidacy_id="cand_123", assigned_user_id="user_1"
        )

        assert event.data["role"] == "recruiter"


class TestAssignmentRemoved:
    """Test AssignmentRemoved event"""

    def test_create_assignment_removed(self):
        """Test creating AssignmentRemoved event"""
        event = AssignmentRemoved.create(
            candidacy_id="cand_123",
            unassigned_user_id="user_recruiter_1",
            by_user_id="user_admin",
        )

        assert event.event_type == "AssignmentRemoved"
        assert event.aggregate_id == "cand_123"
        assert event.data["user_id"] == "user_recruiter_1"
        assert event.metadata["user_id"] == "user_admin"

    def test_create_assignment_removed_no_actor(self):
        """Test creating assignment removal without actor"""
        event = AssignmentRemoved.create(
            candidacy_id="cand_123", unassigned_user_id="user_1"
        )

        assert event.metadata == {}


class TestEventSerialization:
    """Test event serialization for all event types"""

    def test_candidacy_created_to_dict(self):
        """Test CandidacyCreated serialization to dict"""
        event = CandidacyCreated.create(
            candidacy_id="cand_123", name="Alice", email="alice@example.com"
        )

        event_dict = event.to_dict()

        assert event_dict["event_type"] == "CandidacyCreated"
        assert event_dict["aggregate_id"] == "cand_123"
        assert event_dict["data"]["name"] == "Alice"
        assert event_dict["data"]["email"] == "alice@example.com"
        assert "event_id" in event_dict
        assert "timestamp" in event_dict

    def test_candidacy_step_changed_to_dict(self):
        """Test CandidacyStepChanged serialization to dict"""
        event = CandidacyStepChanged.create(
            candidacy_id="cand_123", from_step="app", to_step="screen"
        )

        event_dict = event.to_dict()

        assert event_dict["event_type"] == "CandidacyStepChanged"
        assert event_dict["data"]["from_step"] == "app"
        assert event_dict["data"]["to_step"] == "screen"

    def test_contact_added_to_dict(self):
        """Test ContactAdded serialization to dict"""
        event = ContactAdded.create(
            candidacy_id="cand_123",
            contact_id="contact_1",
            contact_type="interview",
        )

        event_dict = event.to_dict()

        assert event_dict["event_type"] == "ContactAdded"
        assert event_dict["data"]["contact_id"] == "contact_1"
        assert event_dict["data"]["type"] == "interview"

    def test_base_event_deserialization(self):
        """Test base Event class can deserialize all event types"""
        # Create a CandidacyCreated event
        event = CandidacyCreated.create(candidacy_id="cand_123", name="Alice")
        event_dict = event.to_dict()

        # Deserialize as base Event class
        reconstructed = Event.from_dict(event_dict)

        assert reconstructed.event_type == "CandidacyCreated"
        assert reconstructed.aggregate_id == "cand_123"
        assert reconstructed.data["name"] == "Alice"


class TestEventEdgeCases:
    """Test edge cases for events"""

    def test_event_with_empty_data(self):
        """Test event with empty data dict"""
        event = Event(event_type="Test", aggregate_id="agg_123", data={})

        assert event.data == {}

    def test_event_with_empty_metadata(self):
        """Test event with empty metadata dict"""
        event = Event(event_type="Test", aggregate_id="agg_123", metadata={})

        assert event.metadata == {}

    def test_event_with_unicode_data(self):
        """Test event with unicode data"""
        event = CandidacyCreated.create(
            candidacy_id="cand_123", name="候補者 - Candidate 🌟"
        )

        assert event.data["name"] == "候補者 - Candidate 🌟"

        # Should serialize correctly
        event_dict = event.to_dict()
        assert event_dict["data"]["name"] == "候補者 - Candidate 🌟"

        # Deserialize as base Event class
        reconstructed = Event.from_dict(event_dict)
        assert reconstructed.data["name"] == "候補者 - Candidate 🌟"

    def test_event_with_nested_data(self):
        """Test event with nested data structures"""
        event = CandidacyCreated.create(
            candidacy_id="cand_123",
            name="Alice",
            custom_fields={
                "skills": {"python": "expert", "javascript": "intermediate"},
                "education": [{"degree": "BS", "field": "CS"}],
            },
        )

        assert event.data["custom_fields"]["skills"]["python"] == "expert"
        assert event.data["custom_fields"]["education"][0]["degree"] == "BS"
