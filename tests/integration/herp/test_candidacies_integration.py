"""
Integration tests for HERP Candidacies API

Uses pytest-vcr to record/replay HTTP interactions with HERP API.
Run with: pytest tests/integration/ -v

Note: First run requires valid HERP_API_KEY to record cassettes.
Subsequent runs replay recorded responses (no API key needed).
"""

import os
import pytest
from unittest.mock import patch

# pytest-vcr configuration
pytest_plugins = ["pytest_vcr"]


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration for test recording/playback"""
    return {
        "filter_headers": ["authorization", "x-api-key"],
        "record_mode": "once",  # Record once, then replay
        "match_on": ["method", "scheme", "host", "port", "path", "query"],
        "cassette_library_dir": "tests/integration/fixtures/cassettes",
    }


@pytest.fixture
def herp_client():
    """Create HERP client for integration testing"""
    from src.core.herp.client import HerpClient
    
    # Use test API key or mock key for playback
    api_key = os.getenv("HERP_API_KEY", "test_api_key")
    
    return HerpClient(
        api_key=api_key,
        base_url=os.getenv("HERP_BASE_URL", "https://public-api.herp.cloud/hire/public")
    )


@pytest.mark.integration
@pytest.mark.vcr()
def test_list_candidacies(herp_client):
    """Test listing candidacies with VCR recording"""
    # This will record the HTTP interaction on first run
    # Subsequent runs will replay from cassette
    
    candidacies = herp_client.candidacies.list(limit=5)
    
    assert isinstance(candidacies, list)
    assert len(candidacies) <= 5
    
    if candidacies:
        candidacy = candidacies[0]
        assert "id" in candidacy
        assert "name" in candidacy
        assert "requisition_id" in candidacy
        assert "status" in candidacy
        assert candidacy["status"] in ["active", "hired", "terminated"]


@pytest.mark.integration
@pytest.mark.vcr()
def test_get_candidacy(herp_client):
    """Test getting a specific candidacy"""
    # First get a list to find a candidacy ID
    candidacies = herp_client.candidacies.list(limit=1)
    
    if not candidacies:
        pytest.skip("No candidacies available for testing")
    
    candidacy_id = candidacies[0]["id"]
    
    # Get the specific candidacy
    candidacy = herp_client.candidacies.get(candidacy_id)
    
    assert candidacy["id"] == candidacy_id
    assert "name" in candidacy
    assert "requisition_id" in candidacy
    assert "created_at" in candidacy
    assert "updated_at" in candidacy


@pytest.mark.integration
@pytest.mark.vcr()
def test_list_candidacies_with_filters(herp_client):
    """Test listing candidacies with filters"""
    candidacies = herp_client.candidacies.list(
        status="active",
        limit=10
    )
    
    assert isinstance(candidacies, list)
    
    # Verify all returned candidacies match filter
    for candidacy in candidacies:
        assert candidacy.get("status") == "active"


@pytest.mark.integration
@pytest.mark.vcr()
def test_candidacy_pagination(herp_client):
    """Test pagination of candidacy list"""
    # Get first page
    page1 = herp_client.candidacies.list(limit=2, offset=0)
    
    # Get second page
    page2 = herp_client.candidacies.list(limit=2, offset=2)
    
    assert isinstance(page1, list)
    assert isinstance(page2, list)
    
    # Pages should have different candidacies
    if page1 and page2:
        assert page1[0]["id"] != page2[0]["id"]


@pytest.mark.integration
@pytest.mark.vcr()
@pytest.mark.skip(reason="Requires write permissions - only run manually")
def test_create_candidacy(herp_client):
    """Test creating a candidacy (skipped by default)"""
    from src.core.herp.builders import CandidacyBuilder
    
    candidacy_data = (
        CandidacyBuilder()
        .with_name("Test Candidate")
        .with_email("test@example.com")
        .for_requisition("req_test_001")
        .build()
    )
    
    candidacy = herp_client.candidacies.create(candidacy_data)
    
    assert candidacy["name"] == "Test Candidate"
    assert candidacy["email"] == "test@example.com"
    assert "id" in candidacy
    
    # Cleanup: terminate the test candidacy
    herp_client.candidacies.terminate(candidacy["id"])


@pytest.mark.integration
@pytest.mark.vcr()
def test_error_handling_not_found(herp_client):
    """Test error handling for non-existent candidacy"""
    from src.core.errors.exceptions import HerpNotFoundError
    
    with pytest.raises(HerpNotFoundError):
        herp_client.candidacies.get("cand_nonexistent_12345")


@pytest.mark.integration
@pytest.mark.vcr()
def test_candidacy_schema_validation(herp_client):
    """Test that returned candidacy matches schema"""
    candidacies = herp_client.candidacies.list(limit=1)
    
    if not candidacies:
        pytest.skip("No candidacies available for testing")
    
    candidacy = candidacies[0]
    
    # Required fields
    assert isinstance(candidacy["id"], str)
    assert isinstance(candidacy["name"], str)
    assert isinstance(candidacy["requisition_id"], str)
    assert candidacy["status"] in ["active", "hired", "terminated"]
    assert isinstance(candidacy["created_at"], str)
    assert isinstance(candidacy["updated_at"], str)
    
    # Optional fields (if present)
    if "email" in candidacy:
        assert isinstance(candidacy["email"], str)
    if "phone" in candidacy:
        assert isinstance(candidacy["phone"], str)
    if "tags" in candidacy:
        assert isinstance(candidacy["tags"], list)
