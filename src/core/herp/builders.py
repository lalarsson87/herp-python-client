#!/usr/bin/env python3
"""
HERP API Builder Patterns

Fluent builder interfaces for constructing complex API requests.
Provides type-safe, readable methods for creating candidacies, contacts, and evaluations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class CandidacyBuilder:
    """
    Fluent builder for creating candidacy requests

    Provides a readable, chainable interface for constructing candidacy data.
    Ensures required fields are set and validates data before submission.

    Example:
        >>> candidacy = (
        ...     CandidacyBuilder()
        ...     .with_name("Jane Doe")
        ...     .with_email("jane@example.com")
        ...     .with_phone("+81-90-1234-5678")
        ...     .for_requisition("req_001")
        ...     .at_step("application")
        ...     .with_tags(["backend", "senior"])
        ...     .build()
        ... )
        >>> client.candidacies.create(candidacy)
    """

    def __init__(self):
        """Initialize candidacy builder with empty data"""
        self._data: Dict[str, Any] = {}

    def with_name(self, name: str) -> "CandidacyBuilder":
        """
        Set candidate name (required)

        Args:
            name: Full name of the candidate

        Returns:
            Self for chaining
        """
        self._data["name"] = name
        return self

    def with_email(self, email: str) -> "CandidacyBuilder":
        """
        Set candidate email (optional but recommended)

        Args:
            email: Email address

        Returns:
            Self for chaining
        """
        self._data["email"] = email
        return self

    def with_phone(self, phone: str) -> "CandidacyBuilder":
        """
        Set candidate phone number (optional)

        Args:
            phone: Phone number (any format)

        Returns:
            Self for chaining
        """
        self._data["phone"] = phone
        return self

    def with_resume_url(self, url: str) -> "CandidacyBuilder":
        """
        Set resume URL (optional)

        Args:
            url: URL to candidate's resume

        Returns:
            Self for chaining
        """
        self._data["resume_url"] = url
        return self

    def for_requisition(self, requisition_id: str) -> "CandidacyBuilder":
        """
        Set requisition/job posting ID (required)

        Args:
            requisition_id: ID of the job requisition

        Returns:
            Self for chaining
        """
        self._data["requisition_id"] = requisition_id
        return self

    def at_step(self, step: str) -> "CandidacyBuilder":
        """
        Set hiring step/stage (optional)

        Args:
            step: Hiring step (e.g., "application", "interview", "offer")

        Returns:
            Self for chaining
        """
        self._data["step"] = step
        return self

    def with_tags(self, tags: List[str]) -> "CandidacyBuilder":
        """
        Add tags to the candidacy (optional)

        Args:
            tags: List of tag strings

        Returns:
            Self for chaining
        """
        self._data["tags"] = tags
        return self

    def with_custom_field(self, key: str, value: Any) -> "CandidacyBuilder":
        """
        Add custom field data (optional)

        Args:
            key: Custom field name
            value: Custom field value

        Returns:
            Self for chaining
        """
        if "custom_fields" not in self._data:
            self._data["custom_fields"] = {}
        self._data["custom_fields"][key] = value
        return self

    def build(self) -> Dict[str, Any]:
        """
        Build and validate candidacy data

        Returns:
            Dictionary ready for API submission

        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        if "name" not in self._data:
            raise ValueError("Candidate name is required")
        if "requisition_id" not in self._data:
            raise ValueError("Requisition ID is required")

        return self._data.copy()


class ContactBuilder:
    """
    Fluent builder for creating contact/interview requests

    Provides a readable interface for scheduling interviews and contacts.

    Example:
        >>> contact = (
        ...     ContactBuilder()
        ...     .of_type("technical_interview")
        ...     .with_title("Senior Backend Engineer Interview")
        ...     .scheduled_at("2026-02-01T14:00:00Z")
        ...     .for_duration(60)
        ...     .at_location("https://zoom.us/j/123456789")
        ...     .with_interviewers(["user_001", "user_002"])
        ...     .with_notes("Focus on system design and Golang experience")
        ...     .build()
        ... )
        >>> client.contacts.create("cand_123", contact)
    """

    def __init__(self):
        """Initialize contact builder with empty data"""
        self._data: Dict[str, Any] = {}

    def of_type(self, contact_type: str) -> "ContactBuilder":
        """
        Set contact type (required)

        Args:
            contact_type: Type of contact (phone_screen, technical_interview,
                         casual_interview, behavioral_interview,
                         final_interview, reference_check, other)

        Returns:
            Self for chaining
        """
        self._data["type"] = contact_type
        return self

    def with_title(self, title: str) -> "ContactBuilder":
        """
        Set contact title (optional)

        Args:
            title: Interview/contact title

        Returns:
            Self for chaining
        """
        self._data["title"] = title
        return self

    def scheduled_at(self, scheduled_time: str) -> "ContactBuilder":
        """
        Set scheduled time (optional)

        Args:
            scheduled_time: ISO 8601 datetime string

        Returns:
            Self for chaining
        """
        self._data["scheduled_at"] = scheduled_time
        return self

    def scheduled_for(self, dt: datetime) -> "ContactBuilder":
        """
        Set scheduled time from datetime object (optional)

        Args:
            dt: Python datetime object

        Returns:
            Self for chaining
        """
        self._data["scheduled_at"] = dt.isoformat()
        return self

    def for_duration(self, minutes: int) -> "ContactBuilder":
        """
        Set duration in minutes (optional)

        Args:
            minutes: Duration in minutes

        Returns:
            Self for chaining
        """
        self._data["duration_minutes"] = minutes
        return self

    def at_location(self, location: str) -> "ContactBuilder":
        """
        Set location (optional)

        Args:
            location: Physical location or video call URL

        Returns:
            Self for chaining
        """
        self._data["location"] = location
        return self

    def with_interviewers(self, interviewer_ids: List[str]) -> "ContactBuilder":
        """
        Set interviewer user IDs (optional)

        Args:
            interviewer_ids: List of user IDs

        Returns:
            Self for chaining
        """
        self._data["interviewer_ids"] = interviewer_ids
        return self

    def with_notes(self, notes: str) -> "ContactBuilder":
        """
        Add notes to the contact (optional)

        Args:
            notes: Interview notes or description

        Returns:
            Self for chaining
        """
        self._data["notes"] = notes
        return self

    def build(self) -> Dict[str, Any]:
        """
        Build and validate contact data

        Returns:
            Dictionary ready for API submission

        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        if "type" not in self._data:
            raise ValueError("Contact type is required")

        return self._data.copy()


class EvaluationResponseBuilder:
    """
    Fluent builder for submitting evaluation responses

    Helps construct evaluation submissions with proper structure.

    Example:
        >>> evaluation = (
        ...     EvaluationResponseBuilder()
        ...     .answer_question("q1", "Excellent communication skills")
        ...     .score_question("q1", 5, max_score=5)
        ...     .answer_question("q2", "Strong technical background in Golang")
        ...     .score_question("q2", 4, max_score=5)
        ...     .with_overall_score(9, max_score=10)
        ...     .with_recommendation("strong_yes")
        ...     .with_notes("Great culture fit, recommend proceeding to final round")
        ...     .build()
        ... )
        >>> client.evaluations.submit("eval_123", evaluation)
    """

    def __init__(self):
        """Initialize evaluation builder with empty data"""
        self._data: Dict[str, Any] = {
            "questions": []
        }
        self._question_map: Dict[str, int] = {}

    def answer_question(
        self,
        question_id: str,
        answer: str
    ) -> "EvaluationResponseBuilder":
        """
        Add text answer to a question

        Args:
            question_id: Question identifier
            answer: Text answer

        Returns:
            Self for chaining
        """
        if question_id not in self._question_map:
            idx = len(self._data["questions"])
            self._question_map[question_id] = idx
            self._data["questions"].append({
                "id": question_id,
                "answer": answer
            })
        else:
            idx = self._question_map[question_id]
            self._data["questions"][idx]["answer"] = answer

        return self

    def score_question(
        self,
        question_id: str,
        score: int,
        max_score: Optional[int] = None
    ) -> "EvaluationResponseBuilder":
        """
        Add numeric score to a question

        Args:
            question_id: Question identifier
            score: Numeric score
            max_score: Maximum possible score (optional)

        Returns:
            Self for chaining
        """
        if question_id not in self._question_map:
            idx = len(self._data["questions"])
            self._question_map[question_id] = idx
            question_data = {
                "id": question_id,
                "score": score
            }
            if max_score is not None:
                question_data["max_score"] = max_score
            self._data["questions"].append(question_data)
        else:
            idx = self._question_map[question_id]
            self._data["questions"][idx]["score"] = score
            if max_score is not None:
                self._data["questions"][idx]["max_score"] = max_score

        return self

    def with_overall_score(
        self,
        score: int,
        max_score: Optional[int] = None
    ) -> "EvaluationResponseBuilder":
        """
        Set overall evaluation score

        Args:
            score: Overall score
            max_score: Maximum possible score (optional)

        Returns:
            Self for chaining
        """
        self._data["overall_score"] = score
        if max_score is not None:
            self._data["max_overall_score"] = max_score
        return self

    def with_recommendation(
        self,
        recommendation: str
    ) -> "EvaluationResponseBuilder":
        """
        Set hiring recommendation

        Args:
            recommendation: One of: strong_yes, yes, maybe, no, strong_no

        Returns:
            Self for chaining
        """
        valid_recommendations = ["strong_yes", "yes", "maybe", "no", "strong_no"]
        if recommendation not in valid_recommendations:
            raise ValueError(
                f"Invalid recommendation: {recommendation}. "
                f"Must be one of: {', '.join(valid_recommendations)}"
            )
        self._data["recommendation"] = recommendation
        return self

    def with_notes(self, notes: str) -> "EvaluationResponseBuilder":
        """
        Add general notes to the evaluation

        Args:
            notes: Evaluation notes

        Returns:
            Self for chaining
        """
        self._data["notes"] = notes
        return self

    def build(self) -> Dict[str, Any]:
        """
        Build and validate evaluation response data

        Returns:
            Dictionary ready for API submission

        Raises:
            ValueError: If no questions have been answered
        """
        if not self._data["questions"]:
            raise ValueError("At least one question must be answered")

        return self._data.copy()


# Convenience aliases for backward compatibility
CandidateBuilder = CandidacyBuilder  # Alternative name
InterviewBuilder = ContactBuilder     # Alternative name
