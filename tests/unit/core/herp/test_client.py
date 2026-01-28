"""
Tests for HERP Client (Facade)
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.core.herp import HerpClient
from src.core.herp.query_dsl import Query
from src.core.utils.config import HerpConfig


class TestHerpClient:
    """Test HerpClient class"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HerpConfig(
            api_key="test_token_123",
            base_url="https://test-api.herp.cloud/hire/public",
        )

    @pytest.fixture
    def client(self, config):
        """Create HerpClient instance"""
        return HerpClient(config)

    def test_initialization(self, config):
        """Test client initialization"""
        client = HerpClient(config)

        # Should have all specialized API clients
        assert client.candidacies is not None
        assert client.contacts is not None
        assert client.files is not None
        assert client.evaluations is not None
        assert client.assignments is not None
        assert client.timeline is not None
        assert client.master_data is not None

    def test_initialization_with_cache_manager(self, config):
        """Test initialization with cache manager"""
        cache_manager = Mock()

        client = HerpClient(config, cache_manager=cache_manager)

        # Should store cache manager
        assert client.cache_manager == cache_manager

    def test_initialization_with_circuit_breaker(self, config):
        """Test initialization with circuit breaker enabled"""
        client = HerpClient(config, enable_circuit_breaker=True)

        # Should have circuit breaker
        assert client.circuit_breaker is not None

    def test_initialization_with_metrics_collector(self, config):
        """Test initialization with custom metrics collector"""
        metrics_collector = Mock()

        client = HerpClient(config, metrics_collector=metrics_collector)

        # Should use custom metrics collector
        assert client.metrics == metrics_collector

    def test_exposes_config_attributes(self, client, config):
        """Test client exposes config attributes"""
        assert client.config == config
        assert client.base_url == config.base_url

    def test_exposes_base_client_attributes(self, client):
        """Test client exposes base client attributes"""
        assert client.rate_limiter is not None
        assert client.metrics is not None
        assert client.session is not None

    # ========================================================================
    # HTTP Methods (should delegate to base client)
    # ========================================================================

    def test_get_delegates_to_base_client(self, client):
        """Test GET request delegates to base client"""
        with patch.object(client._base_client, "get") as mock_get:
            mock_get.return_value = {"result": "data"}

            result = client.get("/test/endpoint", params={"key": "value"})

            mock_get.assert_called_once_with("/test/endpoint", params={"key": "value"})
            assert result == {"result": "data"}

    def test_post_delegates_to_base_client(self, client):
        """Test POST request delegates to base client"""
        with patch.object(client._base_client, "post") as mock_post:
            mock_post.return_value = {"id": "new_123"}

            result = client.post("/test/endpoint", json={"name": "Test"})

            mock_post.assert_called_once_with("/test/endpoint", json={"name": "Test"})
            assert result["id"] == "new_123"

    def test_patch_delegates_to_base_client(self, client):
        """Test PATCH request delegates to base client"""
        with patch.object(client._base_client, "patch") as mock_patch:
            mock_patch.return_value = {"updated": True}

            result = client.patch("/test/endpoint", json={"status": "updated"})

            mock_patch.assert_called_once_with(
                "/test/endpoint", json={"status": "updated"}
            )
            assert result["updated"] is True

    def test_put_delegates_to_base_client(self, client):
        """Test PUT request delegates to base client"""
        with patch.object(client._base_client, "put") as mock_put:
            mock_put.return_value = {"replaced": True}

            result = client.put("/test/endpoint", json={"data": "new"})

            mock_put.assert_called_once_with("/test/endpoint", json={"data": "new"})
            assert result["replaced"] is True

    def test_delete_delegates_to_base_client(self, client):
        """Test DELETE request delegates to base client"""
        with patch.object(client._base_client, "delete") as mock_delete:
            mock_delete.return_value = {"deleted": True}

            result = client.delete("/test/endpoint")

            mock_delete.assert_called_once_with("/test/endpoint")
            assert result["deleted"] is True

    # ========================================================================
    # Candidacies (backward compatibility delegation)
    # ========================================================================

    def test_list_candidacies_delegates(self, client):
        """Test list_candidacies delegates to candidacies.list"""
        with patch.object(client.candidacies, "list") as mock_list:
            mock_list.return_value = [{"id": "cand_1"}]

            result = client.list_candidacies(
                updated_since="2026-01-01", page=2, limit=100
            )

            mock_list.assert_called_once_with("2026-01-01", 2, 100)
            assert len(result) == 1

    def test_iter_candidacies_delegates(self, client):
        """Test iter_candidacies delegates to candidacies.iter"""
        with patch.object(client.candidacies, "iter") as mock_iter:
            mock_iter.return_value = iter([{"id": "cand_1"}])

            result = client.iter_candidacies(
                updated_since="2026-01-01", limit=50, max_pages=5
            )

            mock_iter.assert_called_once_with("2026-01-01", 50, 5)
            assert list(result) == [{"id": "cand_1"}]

    def test_list_all_candidacies_delegates(self, client):
        """Test list_all_candidacies delegates to candidacies.fetch_all"""
        with patch.object(client.candidacies, "fetch_all") as mock_fetch_all:
            mock_fetch_all.return_value = [{"id": "cand_1"}, {"id": "cand_2"}]

            result = client.list_all_candidacies(updated_since="2026-01-01")

            mock_fetch_all.assert_called_once_with("2026-01-01", 100, None)
            assert len(result) == 2

    def test_search_candidacies_delegates(self, client):
        """Test search_candidacies delegates to candidacies.search"""
        query = Query()
        with patch.object(client.candidacies, "search") as mock_search:
            mock_search.return_value = [{"id": "cand_1"}]

            result = client.search_candidacies(query=query, limit=50, status="active")

            mock_search.assert_called_once_with(query, 50, status="active")
            assert len(result) == 1

    def test_get_candidacy_delegates(self, client):
        """Test get_candidacy delegates to candidacies.get"""
        with patch.object(client.candidacies, "get") as mock_get:
            mock_get.return_value = {"id": "cand_123", "name": "Test"}

            result = client.get_candidacy("cand_123")

            mock_get.assert_called_once_with("cand_123")
            assert result["id"] == "cand_123"

    def test_create_candidacy_delegates(self, client):
        """Test create_candidacy delegates to candidacies.create"""
        with patch.object(client.candidacies, "create") as mock_create:
            mock_create.return_value = {"id": "cand_new"}
            data = {"name": "New Candidate", "email": "test@example.com"}

            result = client.create_candidacy(data)

            mock_create.assert_called_once_with(data)
            assert result["id"] == "cand_new"

    def test_update_candidacy_step_delegates(self, client):
        """Test update_candidacy_step delegates to candidacies.update_step"""
        with patch.object(client.candidacies, "update_step") as mock_update:
            mock_update.return_value = {"id": "cand_123", "step": "interview"}

            result = client.update_candidacy_step("cand_123", "interview")

            mock_update.assert_called_once_with("cand_123", "interview")
            assert result["step"] == "interview"

    def test_terminate_candidacy_delegates(self, client):
        """Test terminate_candidacy delegates to candidacies.terminate"""
        with patch.object(client.candidacies, "terminate") as mock_terminate:
            mock_terminate.return_value = {"id": "cand_123", "terminated": True}

            result = client.terminate_candidacy("cand_123", "not_qualified")

            mock_terminate.assert_called_once_with("cand_123", "not_qualified")
            assert result["terminated"] is True

    # ========================================================================
    # Contacts (backward compatibility delegation)
    # ========================================================================

    def test_list_contacts_delegates(self, client):
        """Test list_contacts delegates to contacts.list"""
        with patch.object(client.contacts, "list") as mock_list:
            mock_list.return_value = [{"id": "contact_1"}]

            result = client.list_contacts("cand_123")

            mock_list.assert_called_once_with("cand_123")
            assert len(result) == 1

    def test_list_contacts_for_multiple_delegates(self, client):
        """Test list_contacts_for_multiple delegates to contacts.list_for_multiple"""
        with patch.object(client.contacts, "list_for_multiple") as mock_list_multi:
            mock_list_multi.return_value = {"cand_1": [{"id": "contact_1"}]}

            result = client.list_contacts_for_multiple(
                ["cand_1", "cand_2"], max_workers=10
            )

            mock_list_multi.assert_called_once_with(["cand_1", "cand_2"], 10)
            assert "cand_1" in result

    def test_create_contact_delegates(self, client):
        """Test create_contact delegates to contacts.create"""
        with patch.object(client.contacts, "create") as mock_create:
            mock_create.return_value = {"id": "contact_new"}
            contact_data = {"type": "interview", "scheduledAt": "2026-02-01"}

            result = client.create_contact("cand_123", contact_data)

            mock_create.assert_called_once_with("cand_123", contact_data)
            assert result["id"] == "contact_new"

    # ========================================================================
    # Timeline (backward compatibility delegation)
    # ========================================================================

    def test_list_timeline_comments_delegates(self, client):
        """Test list_timeline_comments delegates to timeline.list"""
        with patch.object(client.timeline, "list") as mock_list:
            mock_list.return_value = [{"id": "comment_1"}]

            result = client.list_timeline_comments("cand_123")

            mock_list.assert_called_once_with("cand_123")
            assert len(result) == 1

    def test_add_timeline_comment_delegates(self, client):
        """Test add_timeline_comment delegates to timeline.add_comment"""
        with patch.object(client.timeline, "add_comment") as mock_add:
            mock_add.return_value = {"id": "comment_new"}

            result = client.add_timeline_comment(
                "cand_123", "Great candidate!", "text/plain"
            )

            mock_add.assert_called_once_with(
                "cand_123", "Great candidate!", "text/plain"
            )
            assert result["id"] == "comment_new"

    def test_add_timeline_comment_default_content_type(self, client):
        """Test add_timeline_comment uses text/plain by default"""
        with patch.object(client.timeline, "add_comment") as mock_add:
            mock_add.return_value = {"id": "comment_new"}

            client.add_timeline_comment("cand_123", "Comment")

            # Should use text/plain as default
            call_args = mock_add.call_args
            assert call_args[0][2] == "text/plain"

    # ========================================================================
    # Files (backward compatibility delegation)
    # ========================================================================

    def test_list_files_delegates(self, client):
        """Test list_files delegates to files.list"""
        with patch.object(client.files, "list") as mock_list:
            mock_list.return_value = [{"id": "file_1"}]

            result = client.list_files("cand_123")

            mock_list.assert_called_once_with("cand_123")
            assert len(result) == 1

    def test_list_files_for_multiple_delegates(self, client):
        """Test list_files_for_multiple delegates to files.list_for_multiple"""
        with patch.object(client.files, "list_for_multiple") as mock_list_multi:
            mock_list_multi.return_value = {"cand_1": [{"id": "file_1"}]}

            result = client.list_files_for_multiple(["cand_1", "cand_2"], max_workers=8)

            mock_list_multi.assert_called_once_with(["cand_1", "cand_2"], 8)
            assert "cand_1" in result

    def test_download_file_delegates(self, client):
        """Test download_file delegates to files.download"""
        with patch.object(client.files, "download") as mock_download:
            mock_download.return_value = b"PDF content"

            result = client.download_file("cand_123", "file_456")

            mock_download.assert_called_once_with("cand_123", "file_456")
            assert result == b"PDF content"

    def test_upload_file_delegates(self, client):
        """Test upload_file delegates to files.upload"""
        with patch.object(client.files, "upload") as mock_upload:
            mock_upload.return_value = {"id": "file_new"}
            file_path = Path("/tmp/resume.pdf")

            result = client.upload_file("cand_123", file_path, file_type="resume")

            mock_upload.assert_called_once_with("cand_123", file_path, "resume")
            assert result["id"] == "file_new"

    def test_upload_file_default_type(self, client):
        """Test upload_file uses 'other' as default type"""
        with patch.object(client.files, "upload") as mock_upload:
            mock_upload.return_value = {"id": "file_new"}
            file_path = Path("/tmp/document.pdf")

            client.upload_file("cand_123", file_path)

            # Should use 'other' as default
            call_args = mock_upload.call_args
            assert call_args[0][2] == "other"

    # ========================================================================
    # Evaluations (backward compatibility delegation)
    # ========================================================================

    def test_get_evaluation_delegates(self, client):
        """Test get_evaluation delegates to evaluations.get"""
        with patch.object(client.evaluations, "get") as mock_get:
            mock_get.return_value = {"id": "eval_123"}

            result = client.get_evaluation("eval_123")

            mock_get.assert_called_once_with("eval_123")
            assert result["id"] == "eval_123"

    def test_submit_evaluation_delegates(self, client):
        """Test submit_evaluation delegates to evaluations.submit"""
        with patch.object(client.evaluations, "submit") as mock_submit:
            mock_submit.return_value = {"id": "eval_123", "status": "completed"}
            responses = {"q1": {"rating": 5}}

            result = client.submit_evaluation("eval_123", responses)

            mock_submit.assert_called_once_with("eval_123", responses)
            assert result["status"] == "completed"

    # ========================================================================
    # Assignments (backward compatibility delegation)
    # ========================================================================

    def test_list_assignments_delegates(self, client):
        """Test list_assignments delegates to assignments.list"""
        with patch.object(client.assignments, "list") as mock_list:
            mock_list.return_value = [{"id": "assign_1"}]

            result = client.list_assignments("cand_123")

            mock_list.assert_called_once_with("cand_123")
            assert len(result) == 1

    def test_assign_team_member_delegates(self, client):
        """Test assign_team_member delegates to assignments.assign"""
        with patch.object(client.assignments, "assign") as mock_assign:
            mock_assign.return_value = {"id": "assign_new"}

            result = client.assign_team_member("cand_123", "user_456")

            mock_assign.assert_called_once_with("cand_123", "user_456")
            assert result["id"] == "assign_new"

    def test_remove_team_member_delegates(self, client):
        """Test remove_team_member delegates to assignments.remove"""
        with patch.object(client.assignments, "remove") as mock_remove:
            mock_remove.return_value = {"deleted": True}

            result = client.remove_team_member("cand_123", "assign_456")

            mock_remove.assert_called_once_with("cand_123", "assign_456")
            assert result["deleted"] is True

    # ========================================================================
    # Master Data (backward compatibility delegation)
    # ========================================================================

    def test_list_requisitions_delegates(self, client):
        """Test list_requisitions delegates to master_data.list_requisitions"""
        with patch.object(client.master_data, "list_requisitions") as mock_list:
            mock_list.return_value = [{"id": "req_1"}]

            result = client.list_requisitions()

            mock_list.assert_called_once_with()
            assert len(result) == 1

    def test_list_users_delegates(self, client):
        """Test list_users delegates to master_data.list_users"""
        with patch.object(client.master_data, "list_users") as mock_list:
            mock_list.return_value = [{"id": "user_1"}]

            result = client.list_users()

            mock_list.assert_called_once_with()
            assert len(result) == 1


class TestHerpClientIntegration:
    """Integration-style tests for HerpClient"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HerpConfig(
            api_key="test_token_123",
            base_url="https://test-api.herp.cloud/hire/public",
        )

    def test_client_composition(self, config):
        """Test client properly composes specialized API clients"""
        client = HerpClient(config)

        # All specialized clients should share the same base client
        assert client.candidacies.client == client._base_client
        assert client.contacts.client == client._base_client
        assert client.files.client == client._base_client
        assert client.evaluations.client == client._base_client
        assert client.assignments.client == client._base_client
        assert client.timeline.client == client._base_client
        assert client.master_data.client == client._base_client

    def test_cache_manager_propagation(self, config):
        """Test cache manager is propagated to all components"""
        cache_manager = Mock()
        client = HerpClient(config, cache_manager=cache_manager)

        # Cache manager should be available to base client
        assert client._base_client.cache_manager == cache_manager

    def test_metrics_collector_propagation(self, config):
        """Test metrics collector is propagated to all components"""
        metrics_collector = Mock()
        client = HerpClient(config, metrics_collector=metrics_collector)

        # Metrics collector should be available
        assert client._base_client.metrics == metrics_collector


class TestHerpClientEdgeCases:
    """Test edge cases for HerpClient"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HerpConfig(
            api_key="test_token_123",
            base_url="https://test-api.herp.cloud/hire/public",
        )

    def test_initialization_without_optional_parameters(self, config):
        """Test client can be initialized with minimal parameters"""
        client = HerpClient(config)

        # Should work with just config
        assert client.config == config
        assert client.cache_manager is None
        assert client.circuit_breaker is None  # Disabled by default

    def test_backward_compatible_methods_exist(self, config):
        """Test all backward compatible methods exist"""
        client = HerpClient(config)

        # Candidacies
        assert hasattr(client, "list_candidacies")
        assert hasattr(client, "get_candidacy")
        assert hasattr(client, "create_candidacy")
        assert hasattr(client, "search_candidacies")

        # Contacts
        assert hasattr(client, "list_contacts")
        assert hasattr(client, "create_contact")

        # Files
        assert hasattr(client, "list_files")
        assert hasattr(client, "download_file")
        assert hasattr(client, "upload_file")

        # Timeline
        assert hasattr(client, "list_timeline_comments")
        assert hasattr(client, "add_timeline_comment")

        # Evaluations
        assert hasattr(client, "get_evaluation")
        assert hasattr(client, "submit_evaluation")

        # Assignments
        assert hasattr(client, "list_assignments")
        assert hasattr(client, "assign_team_member")
        assert hasattr(client, "remove_team_member")

        # Master Data
        assert hasattr(client, "list_requisitions")
        assert hasattr(client, "list_users")

    def test_new_api_properties_exist(self, config):
        """Test new API properties exist"""
        client = HerpClient(config)

        # New modular API properties
        assert hasattr(client, "candidacies")
        assert hasattr(client, "contacts")
        assert hasattr(client, "files")
        assert hasattr(client, "evaluations")
        assert hasattr(client, "assignments")
        assert hasattr(client, "timeline")
        assert hasattr(client, "master_data")

    def test_http_methods_exist(self, config):
        """Test HTTP methods are exposed"""
        client = HerpClient(config)

        assert hasattr(client, "get")
        assert hasattr(client, "post")
        assert hasattr(client, "patch")
        assert hasattr(client, "put")
        assert hasattr(client, "delete")
