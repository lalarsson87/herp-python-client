#!/usr/bin/env python3
"""
Unit tests for HERP API Builder Patterns

Tests builder classes for constructing complex API requests.
"""

import pytest
from datetime import datetime, timezone

from src.core.herp.builders import (
    CandidacyBuilder,
    ContactBuilder,
    EvaluationResponseBuilder,
)


class TestCandidacyBuilder:
    """Tests for CandidacyBuilder"""

    def test_minimal_build(self):
        """Test building candidacy with only required fields"""
        candidacy = (
            CandidacyBuilder()
            .with_name("Jane Doe")
            .for_requisition("req_001")
            .build()
        )

        assert candidacy["name"] == "Jane Doe"
        assert candidacy["requisition_id"] == "req_001"
        assert len(candidacy) == 2  # Only required fields

    def test_full_build(self):
        """Test building candidacy with all fields"""
        candidacy = (
            CandidacyBuilder()
            .with_name("Jane Doe")
            .with_email("jane@example.com")
            .with_phone("+81-90-1234-5678")
            .with_resume_url("https://example.com/resume.pdf")
            .for_requisition("req_001")
            .at_step("application")
            .with_tags(["backend", "senior"])
            .with_custom_field("referral_source", "LinkedIn")
            .with_custom_field("years_experience", 8)
            .build()
        )

        assert candidacy["name"] == "Jane Doe"
        assert candidacy["email"] == "jane@example.com"
        assert candidacy["phone"] == "+81-90-1234-5678"
        assert candidacy["resume_url"] == "https://example.com/resume.pdf"
        assert candidacy["requisition_id"] == "req_001"
        assert candidacy["step"] == "application"
        assert candidacy["tags"] == ["backend", "senior"]
        assert candidacy["custom_fields"]["referral_source"] == "LinkedIn"
        assert candidacy["custom_fields"]["years_experience"] == 8

    def test_missing_name_raises_error(self):
        """Test that missing name raises ValueError"""
        with pytest.raises(ValueError, match="name is required"):
            CandidacyBuilder().for_requisition("req_001").build()

    def test_missing_requisition_raises_error(self):
        """Test that missing requisition raises ValueError"""
        with pytest.raises(ValueError, match="requisition_id is required"):
            CandidacyBuilder().with_name("Jane Doe").build()

    def test_chaining(self):
        """Test method chaining returns self"""
        builder = CandidacyBuilder()

        result = builder.with_name("Jane")
        assert result is builder

        result = builder.with_email("jane@example.com")
        assert result is builder

    def test_build_returns_copy(self):
        """Test that build() returns a copy, not reference"""
        builder = (
            CandidacyBuilder()
            .with_name("Jane Doe")
            .for_requisition("req_001")
        )

        candidacy1 = builder.build()
        candidacy2 = builder.build()

        # Should be equal but not same object
        assert candidacy1 == candidacy2
        assert candidacy1 is not candidacy2


class TestContactBuilder:
    """Tests for ContactBuilder"""

    def test_minimal_build(self):
        """Test building contact with only required fields"""
        contact = (
            ContactBuilder()
            .of_type("technical_interview")
            .build()
        )

        assert contact["type"] == "technical_interview"
        assert len(contact) == 1

    def test_full_build(self):
        """Test building contact with all fields"""
        contact = (
            ContactBuilder()
            .of_type("technical_interview")
            .with_title("Senior Backend Interview")
            .scheduled_at("2026-02-01T14:00:00Z")
            .for_duration(60)
            .at_location("https://zoom.us/j/123")
            .with_interviewers(["user_001", "user_002"])
            .with_notes("Focus on system design")
            .build()
        )

        assert contact["type"] == "technical_interview"
        assert contact["title"] == "Senior Backend Interview"
        assert contact["scheduled_at"] == "2026-02-01T14:00:00Z"
        assert contact["duration_minutes"] == 60
        assert contact["location"] == "https://zoom.us/j/123"
        assert contact["interviewer_ids"] == ["user_001", "user_002"]
        assert contact["notes"] == "Focus on system design"

    def test_scheduled_for_datetime(self):
        """Test scheduled_for() with datetime object"""
        dt = datetime(2026, 2, 1, 14, 0, 0, tzinfo=timezone.utc)

        contact = (
            ContactBuilder()
            .of_type("phone_screen")
            .scheduled_for(dt)
            .build()
        )

        assert contact["scheduled_at"] == "2026-02-01T14:00:00+00:00"

    def test_missing_type_raises_error(self):
        """Test that missing type raises ValueError"""
        with pytest.raises(ValueError, match="type is required"):
            ContactBuilder().with_title("Interview").build()

    def test_chaining(self):
        """Test method chaining"""
        builder = ContactBuilder()

        result = builder.of_type("technical_interview")
        assert result is builder

        result = builder.with_title("Interview")
        assert result is builder


class TestEvaluationResponseBuilder:
    """Tests for EvaluationResponseBuilder"""

    def test_minimal_build(self):
        """Test building evaluation with only required fields"""
        evaluation = (
            EvaluationResponseBuilder()
            .answer_question("q1", "Good answer")
            .build()
        )

        assert len(evaluation["questions"]) == 1
        assert evaluation["questions"][0]["id"] == "q1"
        assert evaluation["questions"][0]["answer"] == "Good answer"

    def test_full_build(self):
        """Test building evaluation with all fields"""
        evaluation = (
            EvaluationResponseBuilder()
            .answer_question("q1", "Excellent technical skills")
            .score_question("q1", 5, max_score=5)
            .answer_question("q2", "Good communication")
            .score_question("q2", 4, max_score=5)
            .with_overall_score(9, max_score=10)
            .with_recommendation("strong_yes")
            .with_notes("Great candidate")
            .build()
        )

        assert len(evaluation["questions"]) == 2

        assert evaluation["questions"][0]["id"] == "q1"
        assert evaluation["questions"][0]["answer"] == "Excellent technical skills"
        assert evaluation["questions"][0]["score"] == 5
        assert evaluation["questions"][0]["max_score"] == 5

        assert evaluation["questions"][1]["id"] == "q2"
        assert evaluation["questions"][1]["answer"] == "Good communication"
        assert evaluation["questions"][1]["score"] == 4
        assert evaluation["questions"][1]["max_score"] == 5

        assert evaluation["overall_score"] == 9
        assert evaluation["max_overall_score"] == 10
        assert evaluation["recommendation"] == "strong_yes"
        assert evaluation["notes"] == "Great candidate"

    def test_answer_and_score_same_question(self):
        """Test adding both answer and score to same question"""
        evaluation = (
            EvaluationResponseBuilder()
            .answer_question("q1", "Good answer")
            .score_question("q1", 4, max_score=5)
            .build()
        )

        assert len(evaluation["questions"]) == 1
        assert evaluation["questions"][0]["id"] == "q1"
        assert evaluation["questions"][0]["answer"] == "Good answer"
        assert evaluation["questions"][0]["score"] == 4
        assert evaluation["questions"][0]["max_score"] == 5

    def test_score_without_max(self):
        """Test scoring without max_score"""
        evaluation = (
            EvaluationResponseBuilder()
            .score_question("q1", 8)
            .build()
        )

        assert evaluation["questions"][0]["score"] == 8
        assert "max_score" not in evaluation["questions"][0]

    def test_invalid_recommendation_raises_error(self):
        """Test that invalid recommendation raises ValueError"""
        with pytest.raises(ValueError, match="Invalid recommendation"):
            (
                EvaluationResponseBuilder()
                .answer_question("q1", "Answer")
                .with_recommendation("invalid")
                .build()
            )

    def test_valid_recommendations(self):
        """Test all valid recommendation values"""
        valid = ["strong_yes", "yes", "maybe", "no", "strong_no"]

        for rec in valid:
            evaluation = (
                EvaluationResponseBuilder()
                .answer_question("q1", "Answer")
                .with_recommendation(rec)
                .build()
            )
            assert evaluation["recommendation"] == rec

    def test_missing_questions_raises_error(self):
        """Test that building without questions raises ValueError"""
        with pytest.raises(ValueError, match="At least one question"):
            EvaluationResponseBuilder().build()

    def test_chaining(self):
        """Test method chaining"""
        builder = EvaluationResponseBuilder()

        result = builder.answer_question("q1", "Answer")
        assert result is builder

        result = builder.with_recommendation("yes")
        assert result is builder


class TestBuilderIntegration:
    """Integration tests for builders"""

    def test_candidacy_builder_with_contact_builder(self):
        """Test using multiple builders together"""
        # Create candidacy
        candidacy = (
            CandidacyBuilder()
            .with_name("Jane Doe")
            .with_email("jane@example.com")
            .for_requisition("req_001")
            .build()
        )

        # Create contact for this candidacy
        contact = (
            ContactBuilder()
            .of_type("phone_screen")
            .with_title(f"Phone screen for {candidacy['name']}")
            .scheduled_at("2026-02-01T10:00:00Z")
            .build()
        )

        assert candidacy["name"] in contact["title"]

    def test_realistic_workflow(self):
        """Test realistic workflow using builders"""
        # Create candidacy
        candidacy = (
            CandidacyBuilder()
            .with_name("John Smith")
            .with_email("john@example.com")
            .for_requisition("req_backend_001")
            .at_step("application")
            .with_tags(["golang", "kubernetes"])
            .build()
        )

        # Schedule technical interview
        interview = (
            ContactBuilder()
            .of_type("technical_interview")
            .with_title("Technical Interview - Backend Engineer")
            .scheduled_at("2026-02-15T14:00:00Z")
            .for_duration(90)
            .at_location("https://zoom.us/j/123456789")
            .with_interviewers(["user_tech_lead", "user_senior_eng"])
            .with_notes("Topics: Go concurrency, K8s architecture")
            .build()
        )

        # Submit evaluation
        evaluation = (
            EvaluationResponseBuilder()
            .answer_question("golang_skills", "Strong knowledge of Go concurrency patterns")
            .score_question("golang_skills", 5, max_score=5)
            .answer_question("k8s_experience", "Good understanding of K8s concepts")
            .score_question("k8s_experience", 4, max_score=5)
            .answer_question("system_design", "Excellent system design thinking")
            .score_question("system_design", 5, max_score=5)
            .with_overall_score(14, max_score=15)
            .with_recommendation("strong_yes")
            .with_notes("Excellent candidate, recommend moving to final round")
            .build()
        )

        # Verify all data structures are valid
        assert candidacy["name"] == "John Smith"
        assert interview["type"] == "technical_interview"
        assert evaluation["recommendation"] == "strong_yes"
