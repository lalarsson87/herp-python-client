#!/usr/bin/env python3
"""
Unit tests for Builder Patterns

Tests fluent builder interfaces for candidacies, contacts, and evaluations.
"""

import unittest
from datetime import datetime

from src.core.herp.builders import (
    CandidacyBuilder,
    ContactBuilder,
    EvaluationResponseBuilder,
    TimelineCommentBuilder,
)


class TestCandidacyBuilder(unittest.TestCase):
    """Test cases for CandidacyBuilder"""

    def test_basic_build(self):
        """Test building candidacy with required fields"""
        result = (
            CandidacyBuilder().with_name("Jane Doe").for_requisition("req_001").build()
        )

        self.assertEqual(result["name"], "Jane Doe")
        self.assertEqual(result["requisition_id"], "req_001")
        self.assertNotIn("email", result)

    def test_build_with_all_fields(self):
        """Test building candidacy with all fields"""
        result = (
            CandidacyBuilder()
            .with_name("Jane Doe")
            .with_email("jane@example.com")
            .with_phone("+81-90-1234-5678")
            .with_resume_url("https://example.com/resume.pdf")
            .for_requisition("req_001")
            .at_step("application")
            .with_tags(["backend", "senior"])
            .with_custom_field("referral_source", "LinkedIn")
            .build()
        )

        self.assertEqual(result["name"], "Jane Doe")
        self.assertEqual(result["email"], "jane@example.com")
        self.assertEqual(result["phone"], "+81-90-1234-5678")
        self.assertEqual(result["resume_url"], "https://example.com/resume.pdf")
        self.assertEqual(result["requisition_id"], "req_001")
        self.assertEqual(result["step"], "application")
        self.assertEqual(result["tags"], ["backend", "senior"])
        self.assertEqual(result["custom_fields"]["referral_source"], "LinkedIn")

    def test_missing_name_raises_error(self):
        """Test that missing name raises ValueError"""
        with self.assertRaises(ValueError) as cm:
            CandidacyBuilder().for_requisition("req_001").build()

        self.assertIn("name", str(cm.exception).lower())

    def test_missing_requisition_raises_error(self):
        """Test that missing requisition_id raises ValueError"""
        with self.assertRaises(ValueError) as cm:
            CandidacyBuilder().with_name("Jane Doe").build()

        self.assertIn("requisition", str(cm.exception).lower())

    def test_method_chaining(self):
        """Test that all methods return self for chaining"""
        builder = CandidacyBuilder()

        self.assertIs(builder.with_name("Jane"), builder)
        self.assertIs(builder.with_email("jane@example.com"), builder)
        self.assertIs(builder.for_requisition("req_001"), builder)
        self.assertIs(builder.at_step("interview"), builder)


class TestContactBuilder(unittest.TestCase):
    """Test cases for ContactBuilder"""

    def test_basic_build(self):
        """Test building contact with required fields"""
        result = ContactBuilder().of_type("technical_interview").build()

        self.assertEqual(result["type"], "technical_interview")

    def test_build_with_all_fields(self):
        """Test building contact with all fields"""
        result = (
            ContactBuilder()
            .of_type("technical_interview")
            .with_title("Senior Backend Interview")
            .scheduled_at("2026-02-01T14:00:00Z")
            .for_duration(60)
            .at_location("https://zoom.us/j/123456789")
            .with_interviewers(["user_001", "user_002"])
            .with_notes("Focus on system design")
            .build()
        )

        self.assertEqual(result["type"], "technical_interview")
        self.assertEqual(result["title"], "Senior Backend Interview")
        self.assertEqual(result["scheduled_at"], "2026-02-01T14:00:00Z")
        self.assertEqual(result["duration_minutes"], 60)
        self.assertEqual(result["location"], "https://zoom.us/j/123456789")
        self.assertEqual(result["interviewer_ids"], ["user_001", "user_002"])
        self.assertEqual(result["notes"], "Focus on system design")

    def test_scheduled_for_datetime(self):
        """Test scheduling with datetime object"""
        dt = datetime(2026, 2, 1, 14, 0, 0)
        result = ContactBuilder().of_type("phone_screen").scheduled_for(dt).build()

        self.assertIn("scheduled_at", result)
        self.assertIn("2026-02-01", result["scheduled_at"])

    def test_missing_type_raises_error(self):
        """Test that missing type raises ValueError"""
        with self.assertRaises(ValueError) as cm:
            ContactBuilder().with_title("Interview").build()

        self.assertIn("type", str(cm.exception).lower())

    def test_method_chaining(self):
        """Test that all methods return self for chaining"""
        builder = ContactBuilder()

        self.assertIs(builder.of_type("technical_interview"), builder)
        self.assertIs(builder.with_title("Interview"), builder)
        self.assertIs(builder.for_duration(60), builder)


class TestEvaluationResponseBuilder(unittest.TestCase):
    """Test cases for EvaluationResponseBuilder"""

    def test_answer_question(self):
        """Test adding question answer"""
        result = (
            EvaluationResponseBuilder()
            .answer_question("q1", "Excellent communication")
            .build()
        )

        self.assertEqual(len(result["questions"]), 1)
        self.assertEqual(result["questions"][0]["id"], "q1")
        self.assertEqual(result["questions"][0]["answer"], "Excellent communication")

    def test_score_question(self):
        """Test adding question score"""
        result = (
            EvaluationResponseBuilder().score_question("q1", 5, max_score=5).build()
        )

        self.assertEqual(len(result["questions"]), 1)
        self.assertEqual(result["questions"][0]["id"], "q1")
        self.assertEqual(result["questions"][0]["score"], 5)
        self.assertEqual(result["questions"][0]["max_score"], 5)

    def test_combined_answer_and_score(self):
        """Test combining answer and score for same question"""
        result = (
            EvaluationResponseBuilder()
            .answer_question("q1", "Strong technical skills")
            .score_question("q1", 4, max_score=5)
            .build()
        )

        self.assertEqual(len(result["questions"]), 1)
        self.assertEqual(result["questions"][0]["id"], "q1")
        self.assertEqual(result["questions"][0]["answer"], "Strong technical skills")
        self.assertEqual(result["questions"][0]["score"], 4)

    def test_overall_score(self):
        """Test setting overall score"""
        result = (
            EvaluationResponseBuilder()
            .answer_question("q1", "Good")
            .with_overall_score(8, max_score=10)
            .build()
        )

        self.assertEqual(result["overall_score"], 8)
        self.assertEqual(result["max_overall_score"], 10)

    def test_recommendation(self):
        """Test setting recommendation"""
        result = (
            EvaluationResponseBuilder()
            .answer_question("q1", "Excellent")
            .with_recommendation("strong_yes")
            .build()
        )

        self.assertEqual(result["recommendation"], "strong_yes")

    def test_invalid_recommendation_raises_error(self):
        """Test that invalid recommendation raises ValueError"""
        with self.assertRaises(ValueError) as cm:
            (
                EvaluationResponseBuilder()
                .answer_question("q1", "Good")
                .with_recommendation("definitely_hire")
            )

        self.assertIn("Invalid recommendation", str(cm.exception))

    def test_notes(self):
        """Test adding notes"""
        result = (
            EvaluationResponseBuilder()
            .answer_question("q1", "Good")
            .with_notes("Great culture fit")
            .build()
        )

        self.assertEqual(result["notes"], "Great culture fit")

    def test_complete_evaluation(self):
        """Test building complete evaluation"""
        result = (
            EvaluationResponseBuilder()
            .answer_question("q1", "Excellent communication skills")
            .score_question("q1", 5, max_score=5)
            .answer_question("q2", "Strong technical background")
            .score_question("q2", 4, max_score=5)
            .with_overall_score(9, max_score=10)
            .with_recommendation("strong_yes")
            .with_notes("Highly recommend for next round")
            .build()
        )

        self.assertEqual(len(result["questions"]), 2)
        self.assertEqual(result["overall_score"], 9)
        self.assertEqual(result["recommendation"], "strong_yes")
        self.assertEqual(result["notes"], "Highly recommend for next round")

    def test_no_questions_raises_error(self):
        """Test that evaluation with no questions raises ValueError"""
        with self.assertRaises(ValueError) as cm:
            EvaluationResponseBuilder().build()

        self.assertIn("question", str(cm.exception).lower())


class TestTimelineCommentBuilder(unittest.TestCase):
    """Test cases for TimelineCommentBuilder"""

    def test_basic_comment(self):
        """Test building basic comment"""
        result = TimelineCommentBuilder().with_content("This is a comment").build()

        self.assertEqual(result["content"], "This is a comment")
        self.assertEqual(result["content_type"], "text/plain")

    def test_markdown_comment(self):
        """Test building markdown comment"""
        result = (
            TimelineCommentBuilder()
            .with_content("# Heading\n\n**Bold text**")
            .as_markdown()
            .build()
        )

        self.assertEqual(result["content"], "# Heading\n\n**Bold text**")
        self.assertEqual(result["content_type"], "text/markdown")

    def test_empty_content_raises_error(self):
        """Test that empty content raises ValueError"""
        with self.assertRaises(ValueError) as cm:
            TimelineCommentBuilder().build()

        self.assertIn("content", str(cm.exception).lower())

    def test_method_chaining(self):
        """Test that all methods return self for chaining"""
        builder = TimelineCommentBuilder()

        self.assertIs(builder.with_content("Test"), builder)
        self.assertIs(builder.as_markdown(), builder)


class TestBuilderIntegration(unittest.TestCase):
    """Integration tests for builder workflows"""

    def test_complete_candidacy_workflow(self):
        """Test complete workflow from candidacy to evaluation"""
        # Build candidacy
        candidacy = (
            CandidacyBuilder()
            .with_name("Jane Doe")
            .with_email("jane@example.com")
            .for_requisition("req_001")
            .at_step("interview")
            .build()
        )

        # Build contact
        contact = (
            ContactBuilder()
            .of_type("technical_interview")
            .with_title("Backend Engineer Interview")
            .for_duration(60)
            .build()
        )

        # Build evaluation
        evaluation = (
            EvaluationResponseBuilder()
            .answer_question("q1", "Strong technical skills")
            .score_question("q1", 5, max_score=5)
            .with_recommendation("strong_yes")
            .build()
        )

        # Build comment
        comment = (
            TimelineCommentBuilder()
            .with_content("Candidate performed exceptionally well")
            .build()
        )

        # Verify all parts are built correctly
        self.assertEqual(candidacy["name"], "Jane Doe")
        self.assertEqual(contact["type"], "technical_interview")
        self.assertEqual(evaluation["recommendation"], "strong_yes")
        self.assertEqual(comment["content"], "Candidate performed exceptionally well")


if __name__ == "__main__":
    unittest.main()
