"""
Tests for HERP Batch Client
"""

from pathlib import Path
from unittest.mock import Mock, call, patch

import pytest

from src.core.errors.exceptions import HerpAPIError, HerpRateLimitError
from src.core.herp.batch_client import BatchHerpClient, BatchResult
from src.core.herp.client import HerpClient
from src.core.utils.config import HerpConfig


@pytest.fixture(autouse=True)
def mock_metrics():
    """Mock metrics collector for all tests"""
    with patch("src.core.herp.batch_client.get_metrics_collector") as mock:
        mock_collector = Mock()
        mock.return_value = mock_collector
        yield mock_collector


class TestBatchResult:
    """Test BatchResult dataclass"""

    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        result = BatchResult(total=100)
        result.successful = [{"id": f"item_{i}"} for i in range(85)]
        result.failed = {f"item_{i}": "error" for i in range(85, 100)}

        assert result.success_rate == 85.0

    def test_success_rate_zero_total(self):
        """Test success rate with zero total"""
        result = BatchResult(total=0)

        assert result.success_rate == 0.0

    def test_success_rate_all_successful(self):
        """Test success rate with all successful"""
        result = BatchResult(total=50)
        result.successful = [{"id": f"item_{i}"} for i in range(50)]

        assert result.success_rate == 100.0

    def test_success_rate_all_failed(self):
        """Test success rate with all failed"""
        result = BatchResult(total=50)
        result.failed = {f"item_{i}": "error" for i in range(50)}

        assert result.success_rate == 0.0

    def test_str_representation(self):
        """Test string representation"""
        result = BatchResult(total=100, duration_seconds=15.5)
        result.successful = [{"id": "item_1"}] * 90
        result.failed = {f"item_{i}": "error" for i in range(10)}

        str_repr = str(result)

        assert "total=100" in str_repr
        assert "successful=90" in str_repr
        assert "failed=10" in str_repr
        assert "90.0%" in str_repr  # Success rate
        assert "15.50s" in str_repr


class TestBatchHerpClient:
    """Test BatchHerpClient class"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HerpConfig(
            api_key="test_token_123",
            base_url="https://test-api.herp.cloud/hire/public",
        )

    @pytest.fixture
    def mock_client(self, config):
        """Create mock HerpClient"""
        client = Mock(spec=HerpClient)
        client.config = config
        return client

    @pytest.fixture
    def batch_client(self, mock_client):
        """Create BatchHerpClient instance"""
        return BatchHerpClient(mock_client, max_workers=5)

    def test_initialization(self, mock_client):
        """Test batch client initialization"""
        batch_client = BatchHerpClient(
            mock_client, max_workers=10, retry_transient=True, max_retries=5
        )

        assert batch_client.client == mock_client
        assert batch_client.max_workers == 10
        assert batch_client.retry_transient is True
        assert batch_client.max_retries == 5

    def test_initialization_defaults(self, mock_client):
        """Test initialization with default parameters"""
        batch_client = BatchHerpClient(mock_client)

        assert batch_client.max_workers == 10  # Default
        assert batch_client.retry_transient is True
        assert batch_client.max_retries == 3

    def test_execute_with_retry_success_first_attempt(self, batch_client):
        """Test execute_with_retry succeeds on first attempt"""
        operation = Mock(return_value={"id": "success"})

        result, error = batch_client._execute_with_retry(
            operation, "item_1", "test_operation"
        )

        assert result == {"id": "success"}
        assert error is None
        assert operation.call_count == 1

    def test_execute_with_retry_transient_error_then_success(self, batch_client):
        """Test retry on transient error then success"""
        operation = Mock(
            side_effect=[
                HerpRateLimitError("Rate limited"),
                {"id": "success"},
            ]
        )

        with patch("time.sleep"):  # Don't actually sleep
            result, error = batch_client._execute_with_retry(
                operation, "item_1", "test_operation"
            )

        assert result == {"id": "success"}
        assert error is None
        assert operation.call_count == 2

    def test_execute_with_retry_non_transient_error(self, batch_client):
        """Test non-transient error fails immediately"""
        non_transient_error = ValueError("Invalid data")
        operation = Mock(side_effect=non_transient_error)

        result, error = batch_client._execute_with_retry(
            operation, "item_1", "test_operation"
        )

        assert result is None
        assert "Invalid data" in error
        assert operation.call_count == 1  # No retry

    def test_execute_with_retry_max_retries_exceeded(self, batch_client):
        """Test max retries exceeded"""
        transient_error = HerpRateLimitError("Rate limited")
        operation = Mock(side_effect=transient_error)

        with patch("time.sleep"):
            result, error = batch_client._execute_with_retry(
                operation, "item_1", "test_operation"
            )

        assert result is None
        assert error is not None
        # Should try: initial + max_retries (3) = 4 attempts
        assert operation.call_count == 4

    def test_execute_with_retry_exponential_backoff(self, batch_client):
        """Test exponential backoff delays"""
        operation = Mock(
            side_effect=[
                HerpRateLimitError("Rate limited"),
                HerpRateLimitError("Rate limited"),
                {"id": "success"},
            ]
        )

        with patch("time.sleep") as mock_sleep:
            batch_client._execute_with_retry(operation, "item_1", "test_operation")

            # Should have slept with exponential backoff: 2^1=2, 2^2=4
            assert mock_sleep.call_count == 2
            assert mock_sleep.call_args_list[0] == call(2)  # First retry
            assert mock_sleep.call_args_list[1] == call(4)  # Second retry

    def test_execute_with_retry_disabled(self, mock_client):
        """Test retry disabled"""
        batch_client = BatchHerpClient(mock_client, retry_transient=False)
        operation = Mock(side_effect=HerpRateLimitError("Rate limited"))

        result, error = batch_client._execute_with_retry(
            operation, "item_1", "test_operation"
        )

        assert result is None
        assert operation.call_count == 1  # No retry even for transient error

    # ========================================================================
    # fetch_candidacies_batch
    # ========================================================================

    def test_fetch_candidacies_batch_success(self, batch_client, mock_client):
        """Test batch fetch candidacies all successful"""
        mock_client.get_candidacy = Mock(
            side_effect=lambda cid: {"id": cid, "name": f"Candidate {cid}"}
        )

        result = batch_client.fetch_candidacies_batch(["cand_1", "cand_2", "cand_3"])

        assert result.total == 3
        assert len(result.successful) == 3
        assert len(result.failed) == 0
        assert result.success_rate == 100.0
        assert result.duration_seconds > 0

    def test_fetch_candidacies_batch_with_failures(self, batch_client, mock_client):
        """Test batch fetch with some failures"""

        def mock_get(cid):
            if cid == "cand_2":
                raise HerpAPIError("Not found")
            return {"id": cid}

        mock_client.get_candidacy = Mock(side_effect=mock_get)

        result = batch_client.fetch_candidacies_batch(["cand_1", "cand_2", "cand_3"])

        assert result.total == 3
        assert len(result.successful) == 2
        assert len(result.failed) == 1
        assert "cand_2" in result.failed
        assert result.success_rate == pytest.approx(66.7, rel=0.1)

    def test_fetch_candidacies_batch_progress_callback(self, batch_client, mock_client):
        """Test batch fetch with progress callback"""
        mock_client.get_candidacy = Mock(side_effect=lambda cid: {"id": cid})
        progress_calls = []

        def progress_callback(completed, total):
            progress_calls.append((completed, total))

        result = batch_client.fetch_candidacies_batch(
            ["cand_1", "cand_2", "cand_3"], progress_callback=progress_callback
        )

        assert result.total == 3
        # Should have 3 progress updates
        assert len(progress_calls) == 3
        # Last call should be (3, 3)
        assert progress_calls[-1] == (3, 3)

    def test_fetch_candidacies_batch_empty_list(self, batch_client):
        """Test batch fetch with empty list"""
        result = batch_client.fetch_candidacies_batch([])

        assert result.total == 0
        assert len(result.successful) == 0
        assert len(result.failed) == 0

    def test_fetch_candidacies_batch_concurrent_execution(
        self, batch_client, mock_client
    ):
        """Test concurrent execution actually happens"""
        import time

        call_times = []

        def slow_get(cid):
            call_times.append(time.time())
            time.sleep(0.05)  # Simulate slow API call
            return {"id": cid}

        mock_client.get_candidacy = Mock(side_effect=slow_get)

        start = time.time()
        result = batch_client.fetch_candidacies_batch([f"cand_{i}" for i in range(5)])
        duration = time.time() - start

        # With concurrent execution (max_workers=5), should take ~0.05s
        # Sequential would take ~0.25s
        assert duration < 0.15  # Allow some overhead
        assert len(result.successful) == 5

    # ========================================================================
    # create_candidacies_batch
    # ========================================================================

    def test_create_candidacies_batch_success(self, batch_client, mock_client):
        """Test batch create candidacies all successful"""
        mock_client.create_candidacy = Mock(
            side_effect=lambda data: {"id": f"cand_new", **data}
        )

        data_list = [
            {"name": "John Doe", "email": "john@example.com"},
            {"name": "Jane Smith", "email": "jane@example.com"},
        ]

        result = batch_client.create_candidacies_batch(data_list)

        assert result.total == 2
        assert len(result.successful) == 2
        assert len(result.failed) == 0
        assert result.success_rate == 100.0

    def test_create_candidacies_batch_with_failures(self, batch_client, mock_client):
        """Test batch create with some failures"""
        call_count = [0]

        def mock_create(data):
            call_count[0] += 1
            if call_count[0] == 2:
                raise HerpAPIError("Duplicate email")
            return {"id": f"cand_{call_count[0]}"}

        mock_client.create_candidacy = Mock(side_effect=mock_create)

        data_list = [{"name": f"Name {i}"} for i in range(3)]

        result = batch_client.create_candidacies_batch(data_list)

        assert result.total == 3
        assert len(result.successful) == 2
        assert len(result.failed) == 1

    def test_create_candidacies_batch_progress_callback(
        self, batch_client, mock_client
    ):
        """Test batch create with progress callback"""
        mock_client.create_candidacy = Mock(side_effect=lambda data: {"id": "new"})
        progress_calls = []

        def progress_callback(completed, total):
            progress_calls.append((completed, total))

        data_list = [{"name": f"Name {i}"} for i in range(3)]
        result = batch_client.create_candidacies_batch(
            data_list, progress_callback=progress_callback
        )

        assert len(progress_calls) == 3
        assert progress_calls[-1] == (3, 3)

    # ========================================================================
    # update_candidacies_batch
    # ========================================================================

    def test_update_candidacies_batch_success(self, batch_client, mock_client):
        """Test batch update candidacies all successful"""
        # Note: batch_client calls with 3 params even though API only needs 2
        mock_client.update_candidacy_step = Mock(
            side_effect=lambda cid, step, data: {"id": cid, "step": step}
        )

        updates = [
            ("cand_1", "interview", {}),
            ("cand_2", "offer", {}),
            ("cand_3", "hired", {}),
        ]

        result = batch_client.update_candidacies_batch(updates)

        assert result.total == 3
        assert len(result.successful) == 3
        assert len(result.failed) == 0
        assert result.success_rate == 100.0

    def test_update_candidacies_batch_with_failures(self, batch_client, mock_client):
        """Test batch update with some failures"""

        def mock_update(cid, step, data):
            if cid == "cand_2":
                raise HerpAPIError("Invalid step")
            return {"id": cid, "step": step}

        mock_client.update_candidacy_step = Mock(side_effect=mock_update)

        updates = [
            ("cand_1", "interview", {}),
            ("cand_2", "invalid_step", {}),
            ("cand_3", "offer", {}),
        ]

        result = batch_client.update_candidacies_batch(updates)

        assert result.total == 3
        assert len(result.successful) == 2
        assert len(result.failed) == 1
        assert "cand_2" in result.failed

    def test_update_candidacies_batch_progress_callback(
        self, batch_client, mock_client
    ):
        """Test batch update with progress callback"""
        mock_client.update_candidacy_step = Mock(
            side_effect=lambda cid, step, data: {"id": cid}
        )
        progress_calls = []

        def progress_callback(completed, total):
            progress_calls.append((completed, total))

        updates = [("cand_1", "step1", {}), ("cand_2", "step2", {})]
        result = batch_client.update_candidacies_batch(
            updates, progress_callback=progress_callback
        )

        assert len(progress_calls) == 2
        assert progress_calls[-1] == (2, 2)

    # ========================================================================
    # download_files_batch
    # ========================================================================

    def test_download_files_batch_success(self, batch_client, mock_client, tmp_path):
        """Test batch download files all successful"""
        mock_client.download_file = Mock(side_effect=lambda cid, fid: b"File content")

        file_requests = [
            ("cand_1", "file_1"),
            ("cand_1", "file_2"),
            ("cand_2", "file_3"),
        ]

        result = batch_client.download_files_batch(file_requests, tmp_path)

        assert result.total == 3
        assert len(result.successful) == 3
        assert len(result.failed) == 0
        assert result.success_rate == 100.0

        # Verify files were created
        assert (tmp_path / "cand_1_file_1").exists()
        assert (tmp_path / "cand_1_file_2").exists()
        assert (tmp_path / "cand_2_file_3").exists()

    def test_download_files_batch_with_failures(
        self, batch_client, mock_client, tmp_path
    ):
        """Test batch download with some failures"""

        def mock_download(cid, fid):
            if fid == "file_2":
                raise HerpAPIError("File not found")
            return b"Content"

        mock_client.download_file = Mock(side_effect=mock_download)

        file_requests = [
            ("cand_1", "file_1"),
            ("cand_1", "file_2"),
            ("cand_2", "file_3"),
        ]

        result = batch_client.download_files_batch(file_requests, tmp_path)

        assert result.total == 3
        assert len(result.successful) == 2
        assert len(result.failed) == 1
        assert "cand_1_file_2" in result.failed

    def test_download_files_batch_creates_directory(
        self, batch_client, mock_client, tmp_path
    ):
        """Test batch download creates output directory"""
        mock_client.download_file = Mock(return_value=b"Content")

        output_dir = tmp_path / "downloads" / "nested"
        assert not output_dir.exists()

        result = batch_client.download_files_batch([("cand_1", "file_1")], output_dir)

        assert output_dir.exists()
        assert len(result.successful) == 1

    def test_download_files_batch_progress_callback(
        self, batch_client, mock_client, tmp_path
    ):
        """Test batch download with progress callback"""
        mock_client.download_file = Mock(return_value=b"Content")
        progress_calls = []

        def progress_callback(completed, total):
            progress_calls.append((completed, total))

        file_requests = [("cand_1", "file_1"), ("cand_2", "file_2")]
        result = batch_client.download_files_batch(
            file_requests, tmp_path, progress_callback=progress_callback
        )

        assert len(progress_calls) == 2
        assert progress_calls[-1] == (2, 2)

    def test_download_files_batch_file_content(
        self, batch_client, mock_client, tmp_path
    ):
        """Test downloaded files have correct content"""
        file_content = b"PDF file content here"
        mock_client.download_file = Mock(return_value=file_content)

        result = batch_client.download_files_batch([("cand_1", "file_1")], tmp_path)

        file_path = tmp_path / "cand_1_file_1"
        assert file_path.read_bytes() == file_content


class TestBatchHerpClientIntegration:
    """Integration-style tests for BatchHerpClient"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HerpConfig(
            api_key="test_token_123",
            base_url="https://test-api.herp.cloud/hire/public",
        )

    @pytest.fixture
    def mock_client(self, config):
        """Create mock HerpClient"""
        client = Mock(spec=HerpClient)
        client.config = config
        return client

    def test_metrics_recording(self, mock_client):
        """Test metrics are recorded for batch operations"""
        batch_client = BatchHerpClient(mock_client)
        mock_client.get_candidacy = Mock(side_effect=lambda cid: {"id": cid})

        with patch.object(batch_client.metrics, "increment_counter") as mock_counter:
            with patch.object(
                batch_client.metrics, "record_histogram"
            ) as mock_histogram:
                result = batch_client.fetch_candidacies_batch(["cand_1", "cand_2"])

                # Should record metrics
                assert mock_counter.call_count >= 3  # total, successful, failed
                assert mock_histogram.call_count >= 1  # duration

    def test_concurrent_with_different_worker_counts(self, mock_client):
        """Test batch operations with different worker counts"""
        mock_client.get_candidacy = Mock(side_effect=lambda cid: {"id": cid})

        # Test with 1 worker (sequential)
        batch_1 = BatchHerpClient(mock_client, max_workers=1)
        result_1 = batch_1.fetch_candidacies_batch([f"cand_{i}" for i in range(5)])

        # Test with 10 workers (highly concurrent)
        batch_10 = BatchHerpClient(mock_client, max_workers=10)
        result_10 = batch_10.fetch_candidacies_batch([f"cand_{i}" for i in range(5)])

        # Both should succeed
        assert result_1.success_rate == 100.0
        assert result_10.success_rate == 100.0


class TestBatchHerpClientEdgeCases:
    """Test edge cases for BatchHerpClient"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HerpConfig(
            api_key="test_token_123",
            base_url="https://test-api.herp.cloud/hire/public",
        )

    @pytest.fixture
    def mock_client(self, config):
        """Create mock HerpClient"""
        client = Mock(spec=HerpClient)
        client.config = config
        return client

    def test_large_batch_size(self, mock_client):
        """Test with large batch size"""
        batch_client = BatchHerpClient(mock_client, max_workers=20)
        mock_client.get_candidacy = Mock(side_effect=lambda cid: {"id": cid})

        # Test with 1000 items
        result = batch_client.fetch_candidacies_batch([f"cand_{i}" for i in range(1000)])

        assert result.total == 1000
        assert len(result.successful) == 1000

    def test_all_failures(self, mock_client):
        """Test batch operation where all items fail"""
        batch_client = BatchHerpClient(mock_client, retry_transient=False)
        mock_client.get_candidacy = Mock(side_effect=HerpAPIError("Server error"))

        result = batch_client.fetch_candidacies_batch(["cand_1", "cand_2", "cand_3"])

        assert result.total == 3
        assert len(result.successful) == 0
        assert len(result.failed) == 3
        assert result.success_rate == 0.0

    def test_update_batch_with_empty_data(self, mock_client):
        """Test update batch with empty data dictionaries"""
        batch_client = BatchHerpClient(mock_client)
        mock_client.update_candidacy_step = Mock(
            side_effect=lambda cid, step, data: {"id": cid, "step": step}
        )

        updates = [
            ("cand_1", "interview", {}),  # Empty data
            ("cand_2", "offer", {}),  # Empty data
        ]

        result = batch_client.update_candidacies_batch(updates)

        assert result.total == 2
        assert len(result.successful) == 2

    def test_exponential_backoff_max_delay(self, mock_client):
        """Test exponential backoff caps at 10 seconds"""
        batch_client = BatchHerpClient(mock_client, max_retries=10)
        operation = Mock(side_effect=[HerpRateLimitError("Rate limited")] * 11)

        with patch("time.sleep") as mock_sleep:
            batch_client._execute_with_retry(operation, "item_1", "test_op")

            # Check that no sleep is longer than 10 seconds
            for call_args in mock_sleep.call_args_list:
                assert call_args[0][0] <= 10

    def test_batch_result_with_no_operations(self):
        """Test BatchResult with no operations"""
        result = BatchResult()

        assert result.total == 0
        assert len(result.successful) == 0
        assert len(result.failed) == 0
        assert result.success_rate == 0.0
        assert result.duration_seconds == 0.0
