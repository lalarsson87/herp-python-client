"""
Integration tests for HERP Contacts API

Tests interview/contact scheduling endpoints.
"""

import pytest


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration"""
    return {
        "filter_headers": ["authorization", "x-api-key"],
        "record_mode": "once",
        "cassette_library_dir": "tests/integration/fixtures/cassettes",
    }


@pytest.fixture
def herp_client():
    """Create HERP client"""
    import os
    from src.core.herp.client import HerpClient
    from src.core.utils.config import HerpConfig

    api_key = os.getenv("HERP_API_KEY", "test_api_key")
    base_url = os.getenv("HERP_BASE_URL", "https://public-api.herp.cloud/hire")

    config = HerpConfig(api_key=api_key, base_url=base_url)
    return HerpClient(config=config)


@pytest.mark.integration
@pytest.mark.vcr()
def test_list_contacts(herp_client):
    """Test listing contacts for a candidacy"""
    # First get a candidacy
    candidacies = herp_client.candidacies.list(limit=1)
    
    if not candidacies:
        pytest.skip("No candidacies available")
    
    candidacy_id = candidacies[0]["id"]
    
    # List contacts
    contacts = herp_client.contacts.list(candidacy_id)
    
    assert isinstance(contacts, list)
    
    if contacts:
        contact = contacts[0]
        assert "id" in contact
        assert "type" in contact
        # Note: Contact response doesn't include candidacy_id field
        # Type is free-form text (e.g., "書類", "カジュアル面談")
        assert isinstance(contact["type"], str)


@pytest.mark.integration
@pytest.mark.vcr()
@pytest.mark.skip(reason="ContactsAPI.get() method not implemented")
def test_get_contact(herp_client):
    """Test getting a specific contact"""
    # Get a candidacy with contacts
    candidacies = herp_client.candidacies.list(limit=5)
    
    contact_found = False
    for candidacy in candidacies:
        contacts = herp_client.contacts.list(candidacy["id"])
        if contacts:
            contact_id = contacts[0]["id"]
            candidacy_id = candidacy["id"]
            contact_found = True
            break
    
    if not contact_found:
        pytest.skip("No contacts available for testing")
    
    # Get the specific contact
    contact = herp_client.contacts.get(candidacy_id, contact_id)

    assert contact["id"] == contact_id
    assert "type" in contact
    assert "createdAt" in contact
    # Note: Contact response doesn't include candidacy_id field


@pytest.mark.integration
@pytest.mark.vcr()
@pytest.mark.skip(reason="Requires write permissions")
def test_create_contact(herp_client):
    """Test creating a contact/interview"""
    from src.core.herp.builders import ContactBuilder
    from datetime import datetime, timedelta
    
    # Get a test candidacy
    candidacies = herp_client.candidacies.list(limit=1)
    if not candidacies:
        pytest.skip("No candidacies available")
    
    candidacy_id = candidacies[0]["id"]
    
    # Create contact
    scheduled_time = datetime.now() + timedelta(days=7)
    contact_data = (
        ContactBuilder()
        .of_type("technical_interview")
        .with_title("Backend Engineer Interview")
        .scheduled_for(scheduled_time)
        .for_duration(60)
        .at_location("https://zoom.us/j/test")
        .build()
    )
    
    contact = herp_client.contacts.create(candidacy_id, contact_data)

    assert contact["type"] == "technical_interview"
    assert "id" in contact
    # Note: Contact response doesn't include candidacy_id field


@pytest.mark.integration
@pytest.mark.vcr()
def test_contact_schema_validation(herp_client):
    """Test contact response matches schema"""
    candidacies = herp_client.candidacies.list(limit=5)
    
    for candidacy in candidacies:
        contacts = herp_client.contacts.list(candidacy["id"])
        if contacts:
            contact = contacts[0]

            # Required fields (camelCase as per API)
            assert isinstance(contact["id"], str)
            assert isinstance(contact["type"], str)
            assert isinstance(contact["step"], str)
            assert isinstance(contact["createdAt"], str)
            assert isinstance(contact["createdBy"], str)

            # Optional fields (if present, camelCase as per API)
            if "title" in contact:
                assert isinstance(contact["title"], str)
            if "scheduledAt" in contact:
                assert isinstance(contact["scheduledAt"], str)
            if "evaluations" in contact:
                assert isinstance(contact["evaluations"], list)

            return  # Found and validated one contact
    
    pytest.skip("No contacts found for schema validation")
