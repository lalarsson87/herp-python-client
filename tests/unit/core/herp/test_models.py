"""
Tests for HERP API Data Models
"""

from datetime import datetime

import pytest

from src.core.herp.models import (
    Candidacy,
    CandidacyStatus,
    Contact,
    ContactType,
    Evaluation,
    File,
    FileType,
    Requisition,
    TerminationReason,
    TimelineComment,
    User,
)


class TestEnums:
    """Test enum values"""

    def test_candidacy_status_values(self):
        """Test CandidacyStatus enum values"""
        assert CandidacyStatus.ACTIVE.value == "active"
        assert CandidacyStatus.TERMINATED.value == "terminated"

    def test_termination_reason_values(self):
        """Test TerminationReason enum values"""
        assert TerminationReason.REJECTED.value == "rejected"
        assert TerminationReason.WITHDRAWN.value == "withdrawn"
        assert TerminationReason.HIRED.value == "hired"
        assert TerminationReason.OTHER.value == "other"

    def test_contact_type_values(self):
        """Test ContactType enum values"""
        assert ContactType.TECHNICAL_INTERVIEW.value == "technical_interview"
        assert ContactType.CASUAL_CONVERSATION.value == "casual_conversation"
        assert ContactType.PHONE_SCREEN.value == "phone_screen"
        assert ContactType.ONSITE_INTERVIEW.value == "onsite_interview"
        assert ContactType.FINAL_INTERVIEW.value == "final_interview"
        assert ContactType.OTHER.value == "other"

    def test_file_type_values(self):
        """Test FileType enum values"""
        assert FileType.RESUME.value == "resume"
        assert FileType.CAREER_SUMMARY.value == "career_summary"
        assert FileType.OTHER.value == "other"


class TestCandidacy:
    """Test Candidacy model"""

    def test_candidacy_initialization(self):
        """Test basic candidacy initialization"""
        candidacy = Candidacy(
            id="cand_123",
            name="John Doe",
            email="john@example.com",
            status="active",
        )

        assert candidacy.id == "cand_123"
        assert candidacy.name == "John Doe"
        assert candidacy.email == "john@example.com"
        assert candidacy.status == "active"

    def test_candidacy_from_dict(self):
        """Test creating candidacy from API response"""
        data = {
            "id": "cand_456",
            "name": "Jane Smith",
            "email": "jane@example.com",
            "status": "active",
            "step": "interview",
            "terminationReason": None,
            "createdAt": "2026-01-01T10:00:00Z",
            "updatedAt": "2026-01-15T14:30:00Z",
            "requisitionId": "req_789",
            "channel": {"name": "LinkedIn", "id": "ch_001"},
        }

        candidacy = Candidacy.from_dict(data)

        assert candidacy.id == "cand_456"
        assert candidacy.name == "Jane Smith"
        assert candidacy.email == "jane@example.com"
        assert candidacy.status == "active"
        assert candidacy.step == "interview"
        assert candidacy.termination_reason is None
        assert candidacy.created_at == "2026-01-01T10:00:00Z"
        assert candidacy.updated_at == "2026-01-15T14:30:00Z"
        assert candidacy.requisition_id == "req_789"
        assert candidacy.channel == {"name": "LinkedIn", "id": "ch_001"}
        assert candidacy.metadata == data

    def test_candidacy_from_dict_with_minimal_fields(self):
        """Test creating candidacy with minimal required fields"""
        data = {
            "id": "cand_001",
            "name": "Minimal User",
        }

        candidacy = Candidacy.from_dict(data)

        assert candidacy.id == "cand_001"
        assert candidacy.name == "Minimal User"
        assert candidacy.email is None
        assert candidacy.status == "active"
        assert candidacy.step is None
        assert candidacy.termination_reason is None

    def test_candidacy_from_dict_with_empty_dict(self):
        """Test creating candidacy from empty dict uses defaults"""
        data = {}

        candidacy = Candidacy.from_dict(data)

        assert candidacy.id == ""
        assert candidacy.name == ""
        assert candidacy.email is None
        assert candidacy.status == "active"

    def test_candidacy_to_dict(self):
        """Test converting candidacy to API request format"""
        candidacy = Candidacy(
            id="cand_123",
            name="Test User",
            email="test@example.com",
            status="active",
            step="screening",
        )

        result = candidacy.to_dict()

        assert result == {
            "name": "Test User",
            "email": "test@example.com",
            "status": "active",
            "step": "screening",
        }

    def test_candidacy_is_active_property(self):
        """Test is_active property"""
        active_candidacy = Candidacy(id="c1", name="User", status="active")
        terminated_candidacy = Candidacy(id="c2", name="User", status="terminated")

        assert active_candidacy.is_active is True
        assert terminated_candidacy.is_active is False

    def test_candidacy_is_terminated_property(self):
        """Test is_terminated property"""
        active_candidacy = Candidacy(id="c1", name="User", status="active")
        terminated_candidacy = Candidacy(id="c2", name="User", status="terminated")

        assert active_candidacy.is_terminated is False
        assert terminated_candidacy.is_terminated is True

    def test_candidacy_default_metadata(self):
        """Test candidacy has default empty metadata dict"""
        candidacy = Candidacy(id="c1", name="User")

        assert candidacy.metadata == {}
        assert isinstance(candidacy.metadata, dict)


class TestContact:
    """Test Contact model"""

    def test_contact_initialization(self):
        """Test basic contact initialization"""
        contact = Contact(
            id="contact_123",
            candidacy_id="cand_456",
            contact_type="technical_interview",
            scheduled_at="2026-02-01T10:00:00Z",
        )

        assert contact.id == "contact_123"
        assert contact.candidacy_id == "cand_456"
        assert contact.contact_type == "technical_interview"
        assert contact.scheduled_at == "2026-02-01T10:00:00Z"

    def test_contact_from_dict(self):
        """Test creating contact from API response"""
        data = {
            "id": "contact_789",
            "contactType": "phone_screen",
            "scheduledAt": "2026-02-15T14:00:00Z",
            "completedAt": "2026-02-15T14:30:00Z",
            "createdAt": "2026-02-01T09:00:00Z",
            "evaluations": [{"id": "eval_001", "result": "pass"}],
        }

        contact = Contact.from_dict(data, candidacy_id="cand_123")

        assert contact.id == "contact_789"
        assert contact.candidacy_id == "cand_123"
        assert contact.contact_type == "phone_screen"
        assert contact.scheduled_at == "2026-02-15T14:00:00Z"
        assert contact.completed_at == "2026-02-15T14:30:00Z"
        assert contact.created_at == "2026-02-01T09:00:00Z"
        assert len(contact.evaluations) == 1
        assert contact.metadata == data

    def test_contact_from_dict_minimal(self):
        """Test creating contact with minimal fields"""
        data = {"id": "c1"}

        contact = Contact.from_dict(data)

        assert contact.id == "c1"
        assert contact.candidacy_id == ""
        assert contact.contact_type == ""
        assert contact.scheduled_at is None
        assert contact.completed_at is None
        assert contact.evaluations == []

    def test_contact_is_scheduled_property(self):
        """Test is_scheduled property"""
        scheduled_contact = Contact(
            id="c1",
            candidacy_id="cand_1",
            contact_type="interview",
            scheduled_at="2026-02-01T10:00:00Z",
        )
        unscheduled_contact = Contact(
            id="c2", candidacy_id="cand_1", contact_type="interview"
        )

        assert scheduled_contact.is_scheduled is True
        assert unscheduled_contact.is_scheduled is False

    def test_contact_is_completed_property(self):
        """Test is_completed property"""
        completed_contact = Contact(
            id="c1",
            candidacy_id="cand_1",
            contact_type="interview",
            completed_at="2026-02-01T11:00:00Z",
        )
        pending_contact = Contact(
            id="c2", candidacy_id="cand_1", contact_type="interview"
        )

        assert completed_contact.is_completed is True
        assert pending_contact.is_completed is False

    def test_contact_default_evaluations(self):
        """Test contact has default empty evaluations list"""
        contact = Contact(id="c1", candidacy_id="cand_1", contact_type="interview")

        assert contact.evaluations == []
        assert isinstance(contact.evaluations, list)


class TestEvaluation:
    """Test Evaluation model"""

    def test_evaluation_initialization(self):
        """Test basic evaluation initialization"""
        evaluation = Evaluation(
            id="eval_123",
            candidacy_id="cand_456",
            contact_id="contact_789",
            evaluator_id="user_001",
            result="pass",
        )

        assert evaluation.id == "eval_123"
        assert evaluation.candidacy_id == "cand_456"
        assert evaluation.contact_id == "contact_789"
        assert evaluation.evaluator_id == "user_001"
        assert evaluation.result == "pass"

    def test_evaluation_from_dict(self):
        """Test creating evaluation from API response"""
        data = {
            "id": "eval_456",
            "candidacyId": "cand_123",
            "contactId": "contact_456",
            "evaluatorId": "user_789",
            "result": "strong_yes",
            "responses": {
                "technical_skill": "excellent",
                "communication": "good",
            },
            "createdAt": "2026-02-01T15:00:00Z",
            "updatedAt": "2026-02-01T15:30:00Z",
        }

        evaluation = Evaluation.from_dict(data)

        assert evaluation.id == "eval_456"
        assert evaluation.candidacy_id == "cand_123"
        assert evaluation.contact_id == "contact_456"
        assert evaluation.evaluator_id == "user_789"
        assert evaluation.result == "strong_yes"
        assert evaluation.responses["technical_skill"] == "excellent"
        assert evaluation.responses["communication"] == "good"
        assert evaluation.created_at == "2026-02-01T15:00:00Z"
        assert evaluation.updated_at == "2026-02-01T15:30:00Z"
        assert evaluation.metadata == data

    def test_evaluation_from_dict_minimal(self):
        """Test creating evaluation with minimal fields"""
        data = {"id": "eval_001"}

        evaluation = Evaluation.from_dict(data)

        assert evaluation.id == "eval_001"
        assert evaluation.candidacy_id is None
        assert evaluation.contact_id is None
        assert evaluation.evaluator_id is None
        assert evaluation.result is None
        assert evaluation.responses == {}

    def test_evaluation_default_responses(self):
        """Test evaluation has default empty responses dict"""
        evaluation = Evaluation(id="e1")

        assert evaluation.responses == {}
        assert isinstance(evaluation.responses, dict)


class TestTimelineComment:
    """Test TimelineComment model"""

    def test_timeline_comment_initialization(self):
        """Test basic timeline comment initialization"""
        comment = TimelineComment(
            id="comment_123",
            candidacy_id="cand_456",
            author_id="user_789",
            comment="Great interview performance",
        )

        assert comment.id == "comment_123"
        assert comment.candidacy_id == "cand_456"
        assert comment.author_id == "user_789"
        assert comment.comment == "Great interview performance"
        assert comment.content_type == "text/plain"

    def test_timeline_comment_from_dict(self):
        """Test creating timeline comment from API response"""
        data = {
            "id": "comment_456",
            "authorId": "user_001",
            "comment": "Excellent technical skills demonstrated",
            "contentType": "text/markdown",
            "createdAt": "2026-02-01T16:00:00Z",
        }

        comment = TimelineComment.from_dict(data, candidacy_id="cand_123")

        assert comment.id == "comment_456"
        assert comment.candidacy_id == "cand_123"
        assert comment.author_id == "user_001"
        assert comment.comment == "Excellent technical skills demonstrated"
        assert comment.content_type == "text/markdown"
        assert comment.created_at == "2026-02-01T16:00:00Z"
        assert comment.metadata == data

    def test_timeline_comment_from_dict_minimal(self):
        """Test creating timeline comment with minimal fields"""
        data = {}

        comment = TimelineComment.from_dict(data)

        assert comment.id == ""
        assert comment.candidacy_id == ""
        assert comment.author_id == ""
        assert comment.comment == ""
        assert comment.content_type == "text/plain"

    def test_timeline_comment_default_content_type(self):
        """Test timeline comment has default content type"""
        comment = TimelineComment(
            id="c1", candidacy_id="cand_1", author_id="user_1", comment="Test"
        )

        assert comment.content_type == "text/plain"


class TestFile:
    """Test File model"""

    def test_file_initialization(self):
        """Test basic file initialization"""
        file = File(
            id="file_123",
            candidacy_id="cand_456",
            file_name="resume.pdf",
            file_type="resume",
            file_size=1024000,
        )

        assert file.id == "file_123"
        assert file.candidacy_id == "cand_456"
        assert file.file_name == "resume.pdf"
        assert file.file_type == "resume"
        assert file.file_size == 1024000

    def test_file_from_dict(self):
        """Test creating file from API response"""
        data = {
            "id": "file_789",
            "fileName": "john_doe_resume.pdf",
            "fileType": "resume",
            "fileSize": 2048000,
            "createdAt": "2026-01-15T10:00:00Z",
            "downloadUrl": "https://storage.example.com/files/file_789",
        }

        file = File.from_dict(data, candidacy_id="cand_123")

        assert file.id == "file_789"
        assert file.candidacy_id == "cand_123"
        assert file.file_name == "john_doe_resume.pdf"
        assert file.file_type == "resume"
        assert file.file_size == 2048000
        assert file.created_at == "2026-01-15T10:00:00Z"
        assert file.download_url == "https://storage.example.com/files/file_789"
        assert file.metadata == data

    def test_file_from_dict_minimal(self):
        """Test creating file with minimal fields"""
        data = {}

        file = File.from_dict(data)

        assert file.id == ""
        assert file.candidacy_id == ""
        assert file.file_name == ""
        assert file.file_type == "other"
        assert file.file_size is None
        assert file.download_url is None

    def test_file_default_file_type_from_dict(self):
        """Test file from_dict provides default file type"""
        # from_dict provides default "other" when fileType is missing
        data = {"id": "f1", "fileName": "document.txt"}
        file = File.from_dict(data, candidacy_id="cand_1")

        assert file.file_type == "other"


class TestRequisition:
    """Test Requisition model"""

    def test_requisition_initialization(self):
        """Test basic requisition initialization"""
        requisition = Requisition(
            id="req_123", title="Senior Python Engineer", status="open"
        )

        assert requisition.id == "req_123"
        assert requisition.title == "Senior Python Engineer"
        assert requisition.status == "open"

    def test_requisition_from_dict(self):
        """Test creating requisition from API response"""
        data = {
            "id": "req_456",
            "title": "Full Stack Developer",
            "status": "open",
            "createdAt": "2026-01-01T08:00:00Z",
            "department": "Engineering",
            "location": "Remote",
        }

        requisition = Requisition.from_dict(data)

        assert requisition.id == "req_456"
        assert requisition.title == "Full Stack Developer"
        assert requisition.status == "open"
        assert requisition.created_at == "2026-01-01T08:00:00Z"
        assert requisition.metadata == data
        assert requisition.metadata["department"] == "Engineering"

    def test_requisition_from_dict_minimal(self):
        """Test creating requisition with minimal fields"""
        data = {}

        requisition = Requisition.from_dict(data)

        assert requisition.id == ""
        assert requisition.title == ""
        assert requisition.status == "open"
        assert requisition.created_at is None

    def test_requisition_default_status(self):
        """Test requisition has default status"""
        requisition = Requisition(id="r1", title="Developer")

        assert requisition.status == "open"


class TestUser:
    """Test User model"""

    def test_user_initialization(self):
        """Test basic user initialization"""
        user = User(id="user_123", name="John Recruiter", email="john@company.com")

        assert user.id == "user_123"
        assert user.name == "John Recruiter"
        assert user.email == "john@company.com"

    def test_user_from_dict(self):
        """Test creating user from API response"""
        data = {
            "id": "user_456",
            "name": "Jane Hiring Manager",
            "email": "jane@company.com",
            "role": "hiring_manager",
            "department": "Engineering",
        }

        user = User.from_dict(data)

        assert user.id == "user_456"
        assert user.name == "Jane Hiring Manager"
        assert user.email == "jane@company.com"
        assert user.metadata == data
        assert user.metadata["role"] == "hiring_manager"

    def test_user_from_dict_minimal(self):
        """Test creating user with minimal fields"""
        data = {}

        user = User.from_dict(data)

        assert user.id == ""
        assert user.name == ""
        assert user.email is None

    def test_user_optional_email(self):
        """Test user can be created without email"""
        user = User(id="u1", name="No Email User")

        assert user.id == "u1"
        assert user.name == "No Email User"
        assert user.email is None


class TestModelIntegration:
    """Integration tests for model usage patterns"""

    def test_candidacy_with_full_workflow(self):
        """Test candidacy model through complete workflow"""
        # Create from API response
        api_data = {
            "id": "cand_workflow",
            "name": "Workflow Test",
            "email": "workflow@example.com",
            "status": "active",
            "step": "screening",
            "requisitionId": "req_001",
            "createdAt": "2026-01-01T10:00:00Z",
            "updatedAt": "2026-01-15T14:00:00Z",
        }

        candidacy = Candidacy.from_dict(api_data)

        # Verify properties work
        assert candidacy.is_active is True
        assert candidacy.is_terminated is False

        # Convert to dict for API request
        request_data = candidacy.to_dict()
        assert "name" in request_data
        assert "email" in request_data
        assert "status" in request_data

    def test_contact_with_evaluations(self):
        """Test contact model with nested evaluations"""
        contact_data = {
            "id": "contact_complex",
            "contactType": "technical_interview",
            "scheduledAt": "2026-02-01T10:00:00Z",
            "completedAt": "2026-02-01T11:30:00Z",
            "evaluations": [
                {"id": "eval_1", "result": "strong_yes"},
                {"id": "eval_2", "result": "yes"},
            ],
        }

        contact = Contact.from_dict(contact_data, candidacy_id="cand_001")

        assert len(contact.evaluations) == 2
        assert contact.is_scheduled is True
        assert contact.is_completed is True

    def test_models_preserve_extra_fields_in_metadata(self):
        """Test that models preserve extra API fields in metadata"""
        # Candidacy with extra fields
        candidacy_data = {
            "id": "c1",
            "name": "Test",
            "customField1": "value1",
            "customField2": "value2",
        }

        candidacy = Candidacy.from_dict(candidacy_data)
        assert candidacy.metadata["customField1"] == "value1"
        assert candidacy.metadata["customField2"] == "value2"

        # User with extra fields
        user_data = {
            "id": "u1",
            "name": "User",
            "customRole": "admin",
        }

        user = User.from_dict(user_data)
        assert user.metadata["customRole"] == "admin"
