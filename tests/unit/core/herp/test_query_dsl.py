#!/usr/bin/env python3
"""
Unit tests for Query DSL

Tests fluent query builder for complex searches.
"""

import unittest
from datetime import datetime
from typing import Any, Dict, List, Union

from src.core.herp.query_dsl import (
    CandidacyQuery,
    FieldFilter,
    FilterOperator,
    LogicalOperator,
    Query,
    candidacy_query,
    query,
)


class TestFieldFilter(unittest.TestCase):
    """Test cases for FieldFilter"""

    def test_simple_filter(self):
        """Test creating simple field filter"""
        f = FieldFilter("email", FilterOperator.EQUALS, "jane@example.com")

        self.assertEqual(f.field, "email")
        self.assertEqual(f.operator, FilterOperator.EQUALS)
        self.assertEqual(f.value, "jane@example.com")

    def test_to_dict(self):
        """Test filter to_dict conversion"""
        f = FieldFilter("name", FilterOperator.CONTAINS, "Doe")
        result = f.to_dict()

        self.assertEqual(result["field"], "name")
        self.assertEqual(result["operator"], "contains")
        self.assertEqual(result["value"], "Doe")

    def test_null_filter_no_value(self):
        """Test IS_NULL filter has no value in dict"""
        f = FieldFilter("email", FilterOperator.IS_NULL)
        result = f.to_dict()

        self.assertEqual(result["field"], "email")
        self.assertEqual(result["operator"], "is_null")
        self.assertNotIn("value", result)


class TestFilterOperator(unittest.TestCase):
    """Test cases for FilterOperator enum"""

    def test_operator_values(self):
        """Test operator enum values"""
        self.assertEqual(FilterOperator.EQUALS.value, "eq")
        self.assertEqual(FilterOperator.NOT_EQUALS.value, "ne")
        self.assertEqual(FilterOperator.GREATER_THAN.value, "gt")
        self.assertEqual(FilterOperator.LESS_THAN.value, "lt")
        self.assertEqual(FilterOperator.CONTAINS.value, "contains")
        self.assertEqual(FilterOperator.IN.value, "in")
        self.assertEqual(FilterOperator.BETWEEN.value, "between")


class TestLogicalOperator(unittest.TestCase):
    """Test cases for LogicalOperator enum"""

    def test_operator_values(self):
        """Test logical operator enum values"""
        self.assertEqual(LogicalOperator.AND.value, "and")
        self.assertEqual(LogicalOperator.OR.value, "or")
        self.assertEqual(LogicalOperator.NOT.value, "not")


class TestQuery(unittest.TestCase):
    """Test cases for Query"""

    def test_empty_query(self):
        """Test creating empty query"""
        q = Query()

        self.assertEqual(len(q.filters), 0)
        self.assertEqual(q.logical_operator, LogicalOperator.AND)
        self.assertFalse(q.negated)

    def test_equals_filter(self):
        """Test equals filter"""
        q = Query().equals("email", "jane@example.com")

        self.assertEqual(len(q.filters), 1)
        self.assertIsInstance(q.filters[0], FieldFilter)
        self.assertEqual(q.filters[0].field, "email")
        self.assertEqual(q.filters[0].operator, FilterOperator.EQUALS)
        self.assertEqual(q.filters[0].value, "jane@example.com")

    def test_multiple_filters(self):
        """Test adding multiple filters"""
        q = (
            Query()
            .equals("requisition_id", "req_001")
            .contains("name", "Engineer")
            .greater_than("years_experience", 5)
        )

        self.assertEqual(len(q.filters), 3)

    def test_in_list_filter(self):
        """Test in list filter"""
        q = Query().in_list("step", ["interview", "offer"])

        self.assertEqual(len(q.filters), 1)
        self.assertEqual(q.filters[0].operator, FilterOperator.IN)
        self.assertEqual(q.filters[0].value, ["interview", "offer"])

    def test_between_filter(self):
        """Test between filter"""
        q = Query().between("created_at", "2026-01-01", "2026-12-31")

        self.assertEqual(len(q.filters), 1)
        self.assertEqual(q.filters[0].operator, FilterOperator.BETWEEN)
        self.assertEqual(q.filters[0].value, ["2026-01-01", "2026-12-31"])

    def test_null_filters(self):
        """Test null check filters"""
        q = Query().is_not_null("email").is_null("termination_date")

        self.assertEqual(len(q.filters), 2)
        self.assertEqual(q.filters[0].operator, FilterOperator.IS_NOT_NULL)
        self.assertEqual(q.filters[1].operator, FilterOperator.IS_NULL)

    def test_and_operator(self):
        """Test AND logical operator"""
        q1 = Query().equals("status", "active")
        q2 = Query().equals("step", "interview")
        combined = Query().and_(q1, q2)

        self.assertEqual(len(combined.filters), 2)
        self.assertEqual(combined.logical_operator, LogicalOperator.AND)

    def test_or_operator(self):
        """Test OR logical operator"""
        q1 = Query().equals("step", "interview")
        q2 = Query().equals("step", "offer")
        combined = Query().or_(q1, q2)

        self.assertEqual(len(combined.filters), 2)
        self.assertEqual(combined.logical_operator, LogicalOperator.OR)

    def test_not_operator(self):
        """Test NOT logical operator"""
        q = Query().equals("status", "terminated")
        negated = Query().not_(q)

        self.assertEqual(len(negated.filters), 1)
        self.assertTrue(negated.filters[0].negated)

    def test_to_dict(self):
        """Test query to_dict conversion"""
        q = Query().equals("email", "jane@example.com").equals("status", "active")
        result = q.to_dict()

        self.assertEqual(result["logical_operator"], "and")
        self.assertEqual(len(result["filters"]), 2)
        self.assertIsInstance(result["filters"][0], dict)

    def test_to_rest_params_simple(self):
        """Test conversion to REST params (simple case)"""
        q = Query().equals("email", "jane@example.com").equals("status", "active")
        params = q.to_rest_params()

        self.assertIn("email__eq", params)
        self.assertEqual(params["email__eq"], "jane@example.com")
        self.assertIn("status__eq", params)
        self.assertEqual(params["status__eq"], "active")

    def test_to_rest_params_complex(self):
        """Test conversion to REST params (complex case with OR)"""
        q1 = Query().equals("step", "interview")
        q2 = Query().equals("step", "offer")
        q = Query().or_(q1, q2)
        params = q.to_rest_params()

        # Complex queries are serialized to JSON
        self.assertIn("query", params)
        self.assertIsInstance(params["query"], dict)


class TestCandidacyQuery(unittest.TestCase):
    """Test cases for CandidacyQuery"""

    def test_by_email(self):
        """Test by_email convenience method"""
        q = CandidacyQuery().by_email("jane@example.com")

        self.assertEqual(len(q.filters), 1)
        self.assertEqual(q.filters[0].field, "email")
        self.assertEqual(q.filters[0].operator, FilterOperator.EQUALS)

    def test_by_name(self):
        """Test by_name convenience method (uses contains)"""
        q = CandidacyQuery().by_name("Doe")

        self.assertEqual(q.filters[0].field, "name")
        self.assertEqual(q.filters[0].operator, FilterOperator.CONTAINS)

    def test_by_exact_name(self):
        """Test by_exact_name convenience method"""
        q = CandidacyQuery().by_exact_name("Jane Doe")

        self.assertEqual(q.filters[0].operator, FilterOperator.EQUALS)

    def test_by_requisition(self):
        """Test by_requisition convenience method"""
        q = CandidacyQuery().by_requisition("req_001")

        self.assertEqual(q.filters[0].field, "requisition_id")
        self.assertEqual(q.filters[0].value, "req_001")

    def test_by_step(self):
        """Test by_step convenience method"""
        q = CandidacyQuery().by_step("interview")

        self.assertEqual(q.filters[0].field, "step")
        self.assertEqual(q.filters[0].value, "interview")

    def test_by_steps(self):
        """Test by_steps convenience method"""
        q = CandidacyQuery().by_steps(["interview", "offer"])

        self.assertEqual(q.filters[0].operator, FilterOperator.IN)
        self.assertEqual(q.filters[0].value, ["interview", "offer"])

    def test_by_status(self):
        """Test by_status convenience method"""
        q = CandidacyQuery().by_status("active")

        self.assertEqual(q.filters[0].field, "status")
        self.assertEqual(q.filters[0].value, "active")

    def test_active_only(self):
        """Test active_only convenience method"""
        q = CandidacyQuery().active_only()

        self.assertEqual(q.filters[0].field, "status")
        self.assertEqual(q.filters[0].value, "active")

    def test_hired_only(self):
        """Test hired_only convenience method"""
        q = CandidacyQuery().hired_only()

        self.assertEqual(q.filters[0].value, "hired")

    def test_terminated_only(self):
        """Test terminated_only convenience method"""
        q = CandidacyQuery().terminated_only()

        self.assertEqual(q.filters[0].value, "terminated")

    def test_with_tags(self):
        """Test with_tags convenience method"""
        q = CandidacyQuery().with_tags(["backend", "senior"])

        self.assertEqual(len(q.filters), 2)
        self.assertEqual(q.filters[0].operator, FilterOperator.CONTAINS)

    def test_created_after(self):
        """Test created_after convenience method"""
        q = CandidacyQuery().created_after("2026-01-01")

        self.assertEqual(q.filters[0].field, "created_at")
        self.assertEqual(q.filters[0].operator, FilterOperator.GREATER_THAN_OR_EQUAL)

    def test_created_after_datetime(self):
        """Test created_after with datetime object"""
        dt = datetime(2026, 1, 1)
        q = CandidacyQuery().created_after(dt)

        self.assertIn("2026-01-01", q.filters[0].value)

    def test_created_before(self):
        """Test created_before convenience method"""
        q = CandidacyQuery().created_before("2026-12-31")

        self.assertEqual(q.filters[0].operator, FilterOperator.LESS_THAN_OR_EQUAL)

    def test_created_between(self):
        """Test created_between convenience method"""
        q = CandidacyQuery().created_between("2026-01-01", "2026-12-31")

        self.assertEqual(len(q.filters), 1)
        self.assertEqual(q.filters[0].operator, FilterOperator.BETWEEN)
        self.assertEqual(q.filters[0].value, ["2026-01-01", "2026-12-31"])

    def test_has_email(self):
        """Test has_email convenience method"""
        q = CandidacyQuery().has_email()

        self.assertEqual(q.filters[0].field, "email")
        self.assertEqual(q.filters[0].operator, FilterOperator.IS_NOT_NULL)

    def test_no_email(self):
        """Test no_email convenience method"""
        q = CandidacyQuery().no_email()

        self.assertEqual(q.filters[0].operator, FilterOperator.IS_NULL)

    def test_complex_candidacy_query(self):
        """Test complex candidacy query"""
        q = (
            CandidacyQuery()
            .by_requisition("req_001")
            .by_steps(["interview", "offer"])
            .active_only()
            .created_after("2026-01-01")
        )

        self.assertEqual(len(q.filters), 4)
        self.assertEqual(q.logical_operator, LogicalOperator.AND)


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions"""

    def test_query_function(self):
        """Test query() convenience function"""
        q = query()

        self.assertIsInstance(q, Query)
        self.assertEqual(len(q.filters), 0)

    def test_candidacy_query_function(self):
        """Test candidacy_query() convenience function"""
        q = candidacy_query()

        self.assertIsInstance(q, CandidacyQuery)
        self.assertEqual(len(q.filters), 0)


class TestRealWorldScenarios(unittest.TestCase):
    """Test cases for real-world search scenarios"""

    def test_find_active_candidates_for_position(self):
        """Test finding active candidates for a specific position"""
        q = (
            CandidacyQuery()
            .by_requisition("req_backend_senior_001")
            .active_only()
            .by_steps(["interview", "offer"])
        )

        params = q.to_rest_params()
        self.assertEqual(len(q.filters), 3)

    def test_find_recent_applications(self):
        """Test finding recent applications"""
        q = (
            CandidacyQuery()
            .created_after("2026-01-01")
            .has_email()
            .active_only()
        )

        self.assertEqual(len(q.filters), 3)

    def test_find_hired_candidates_in_date_range(self):
        """Test finding hired candidates in date range"""
        q = (
            CandidacyQuery()
            .hired_only()
            .created_between("2025-01-01", "2025-12-31")
        )

        self.assertEqual(len(q.filters), 2)

    def test_search_by_name_and_email(self):
        """Test searching by name or email"""
        q1 = CandidacyQuery().by_name("Doe")
        q2 = CandidacyQuery().by_email("jane@example.com")
        q = CandidacyQuery().or_(q1, q2).active_only()

        self.assertEqual(len(q.filters), 3)

    def test_find_candidates_with_specific_tags(self):
        """Test finding candidates with specific tags"""
        q = (
            CandidacyQuery()
            .with_tags(["backend", "golang"])
            .by_requisition("req_001")
        )

        # with_tags adds 2 filters (one per tag)
        self.assertEqual(len(q.filters), 3)


if __name__ == "__main__":
    unittest.main()
