#!/usr/bin/env python3
"""
Unit tests for BatchHerpClient

Tests batch operations including concurrent processing,
retry logic, error handling, and performance characteristics.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import time

from src.core.herp.batch_client import BatchHerpClient, BatchResult
from src.core.herp.client import HerpClient
from src.core.utils.config import HerpConfig
from src.core.errors.exceptions import HerpRateLimitError, HerpAPIError


@pytest.fixture
def herp_config():
    """Create test HERP configuration"""
    return HerpConfig(
        api_key="test-key",
        base_url="https://test.example.com",
        rate_limit=100
    )


@pytest.fixture
def mock_herp_client(herp_config):
    """Create a mocked HERP client"""
    client = Mock(spec=HerpClient)
    client.config = herp_config
    return client


@pytest.fixture
def batch_client(mock_herp_client):
    """Create BatchHerpClient with mocked client"""
    return BatchHerpClient(
        mock_herp_client,
        max_workers=5,
        retry_transient=True,
        max_retries=3
    )


class TestBatchResult:
    """Tests for BatchResult dataclass"""

    def test_create_batch_result(self):
        """Test creating a BatchResult"""
        result = BatchResult(
            successful=[1, 2, 3],
            failed={'item4': 'error'},
            total=4,
            duration_seconds=1.5
        )

        assert len(result.successful) == 3
        assert len(result.failed) == 1
        assert result.total == 4
        assert result.duration_seconds == 1.5

    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        result = BatchResult(
            successful=[1, 2, 3],
            failed={'item4': 'error', 'item5': 'error'},
            total=5
        )

        assert result.success_rate == 60.0  # 3/5 = 60%

    def test_success_rate_all_successful(self):
        """Test success rate when all successful"""
        result = BatchResult(
            successful=[1, 2, 3, 4, 5],
            total=5
        )

        assert result.success_rate == 100.0

    def test_success_rate_all_failed(self):
        """Test success rate when all failed"""
        result = BatchResult(
            failed={'1': 'err', '2': 'err', '3': 'err'},
            total=3
        )

        assert result.success_rate == 0.0

    def test_success_rate_empty(self):
        """Test success rate with zero total"""
        result = BatchResult(total=0)
        assert result.success_rate == 0.0

    def test_str_representation(self):
        """Test string representation"""
        result = BatchResult(
            successful=[1, 2],
            failed={'3': 'error'},
            total=3,
            duration_seconds=1.234
        )

        result_str = str(result)
        assert 'total=3' in result_str
        assert 'successful=2' in result_str
        assert 'failed=1' in result_str
        assert '66.7%' in result_str
        assert '1.23s' in result_str


class TestBatchHerpClientInit:
    """Tests for BatchHerpClient initialization"""

    def test_create_batch_client(self, mock_herp_client):
        """Test creating a batch client"""
        client = BatchHerpClient(mock_herp_client)

        assert client.client is mock_herp_client
        assert client.max_workers == 10  # default
        assert client.retry_transient is True
        assert client.max_retries == 3

    def test_create_batch_client_custom_params(self, mock_herp_client):
        """Test creating batch client with custom parameters"""
        client = BatchHerpClient(
            mock_herp_client,
            max_workers=20,
            retry_transient=False,
            max_retries=5
        )

        assert client.max_workers == 20
        assert client.retry_transient is False
        assert client.max_retries == 5


class TestFetchCandidaciesBatch:
    """Tests for fetch_candidacies_batch"""

    def test_fetch_candidacies_batch_success(self, batch_client, mock_herp_client):
        """Test successful batch fetch"""
        # Mock get_candidacy to return data
        candidacies = [
            {'id': 'cand_1', 'name': 'John'},
            {'id': 'cand_2', 'name': 'Jane'},
            {'id': 'cand_3', 'name': 'Bob'}
        ]
        mock_herp_client.get_candidacy = Mock(
            side_effect=lambda cid: next(c for c in candidacies if c['id'] == cid)
        )

        result = batch_client.fetch_candidacies_batch(['cand_1', 'cand_2', 'cand_3'])

        assert result.total == 3
        assert len(result.successful) == 3
        assert len(result.failed) == 0
        assert result.success_rate == 100.0
        assert result.duration_seconds > 0

    def test_fetch_candidacies_batch_partial_failure(self, batch_client, mock_herp_client):
        """Test batch fetch with partial failures"""
        def mock_get(cid):
            if cid == 'cand_2':
                raise HerpAPIError("Not found")
            return {'id': cid, 'name': 'Test'}

        mock_herp_client.get_candidacy = Mock(side_effect=mock_get)

        result = batch_client.fetch_candidacies_batch(['cand_1', 'cand_2', 'cand_3'])

        assert result.total == 3
        assert len(result.successful) == 2
        assert len(result.failed) == 1
        assert 'cand_2' in result.failed
        assert result.success_rate == pytest.approx(66.67, rel=0.1)

    def test_fetch_candidacies_batch_with_progress(self, batch_client, mock_herp_client):
        """Test batch fetch with progress callback"""
        mock_herp_client.get_candidacy = Mock(return_value={'id': 'test', 'name': 'Test'})

        progress_calls = []

        def progress_callback(completed, total):
            progress_calls.append((completed, total))

        result = batch_client.fetch_candidacies_batch(
            ['cand_1', 'cand_2', 'cand_3'],
            progress_callback=progress_callback
        )

        assert len(progress_calls) == 3
        assert progress_calls[-1] == (3, 3)  # Final call should be (3, 3)

    def test_fetch_candidacies_batch_empty_list(self, batch_client):
        """Test batch fetch with empty list"""
        result = batch_client.fetch_candidacies_batch([])

        assert result.total == 0
        assert len(result.successful) == 0
        assert len(result.failed) == 0


class TestCreateCandidaciesBatch:
    """Tests for create_candidacies_batch"""

    def test_create_candidacies_batch_success(self, batch_client, mock_herp_client):
        """Test successful batch creation"""
        mock_herp_client.create_candidacy = Mock(
            side_effect=lambda data: {**data, 'id': f"cand_{data['name']}"}
        )

        candidacies_data = [
            {'name': 'John', 'email': 'john@example.com'},
            {'name': 'Jane', 'email': 'jane@example.com'}
        ]

        result = batch_client.create_candidacies_batch(candidacies_data)

        assert result.total == 2
        assert len(result.successful) == 2
        assert len(result.failed) == 0
        assert result.success_rate == 100.0

    def test_create_candidacies_batch_with_failures(self, batch_client, mock_herp_client):
        """Test batch creation with some failures"""
        def mock_create(data):
            if data['name'] == 'Invalid':
                raise HerpAPIError("Invalid data")
            return {**data, 'id': f"cand_{data['name']}"}

        mock_herp_client.create_candidacy = Mock(side_effect=mock_create)

        candidacies_data = [
            {'name': 'John', 'email': 'john@example.com'},
            {'name': 'Invalid', 'email': 'invalid@example.com'},
            {'name': 'Jane', 'email': 'jane@example.com'}
        ]

        result = batch_client.create_candidacies_batch(candidacies_data)

        assert result.total == 3
        assert len(result.successful) == 2
        assert len(result.failed) == 1
        assert 'candidacy_1' in result.failed  # Index 1 is the invalid one


class TestUpdateCandidaciesBatch:
    """Tests for update_candidacies_batch"""

    def test_update_candidacies_batch_success(self, batch_client, mock_herp_client):
        """Test successful batch update"""
        mock_herp_client.update_candidacy_step = Mock(
            return_value={'success': True}
        )

        updates = [
            ('cand_1', 'interview', {}),
            ('cand_2', 'offer', {}),
            ('cand_3', 'hired', {})
        ]

        result = batch_client.update_candidacies_batch(updates)

        assert result.total == 3
        assert len(result.successful) == 3
        assert len(result.failed) == 0
        assert mock_herp_client.update_candidacy_step.call_count == 3

    def test_update_candidacies_batch_with_failures(self, batch_client, mock_herp_client):
        """Test batch update with failures"""
        def mock_update(cid, step, data):
            if cid == 'cand_2':
                raise HerpAPIError("Update failed")
            return {'success': True}

        mock_herp_client.update_candidacy_step = Mock(side_effect=mock_update)

        updates = [
            ('cand_1', 'interview', {}),
            ('cand_2', 'offer', {}),
            ('cand_3', 'hired', {})
        ]

        result = batch_client.update_candidacies_batch(updates)

        assert result.total == 3
        assert len(result.successful) == 2
        assert len(result.failed) == 1
        assert 'cand_2' in result.failed


class TestDownloadFilesBatch:
    """Tests for download_files_batch"""

    def test_download_files_batch_success(self, batch_client, mock_herp_client, tmp_path):
        """Test successful batch file download"""
        mock_herp_client.download_file = Mock(return_value=b'file content')

        file_requests = [
            ('cand_1', 'file_1'),
            ('cand_1', 'file_2'),
            ('cand_2', 'file_3')
        ]

        result = batch_client.download_files_batch(file_requests, tmp_path)

        assert result.total == 3
        assert len(result.successful) == 3
        assert len(result.failed) == 0

        # Check files were actually written
        assert (tmp_path / 'cand_1_file_1').exists()
        assert (tmp_path / 'cand_1_file_2').exists()
        assert (tmp_path / 'cand_2_file_3').exists()

    def test_download_files_batch_creates_directory(self, batch_client, mock_herp_client, tmp_path):
        """Test that output directory is created"""
        mock_herp_client.download_file = Mock(return_value=b'content')

        output_dir = tmp_path / 'downloads' / 'nested'
        assert not output_dir.exists()

        file_requests = [('cand_1', 'file_1')]
        result = batch_client.download_files_batch(file_requests, output_dir)

        assert output_dir.exists()
        assert len(result.successful) == 1

    def test_download_files_batch_with_failures(self, batch_client, mock_herp_client, tmp_path):
        """Test batch download with some failures"""
        def mock_download(cid, fid):
            if fid == 'file_2':
                raise HerpAPIError("Download failed")
            return b'file content'

        mock_herp_client.download_file = Mock(side_effect=mock_download)

        file_requests = [
            ('cand_1', 'file_1'),
            ('cand_1', 'file_2'),
            ('cand_2', 'file_3')
        ]

        result = batch_client.download_files_batch(file_requests, tmp_path)

        assert result.total == 3
        assert len(result.successful) == 2
        assert len(result.failed) == 1
        assert 'cand_1_file_2' in result.failed


class TestRetryLogic:
    """Tests for retry logic"""

    def test_retry_on_transient_error(self, batch_client, mock_herp_client):
        """Test retry on transient errors"""
        # Fail twice, then succeed
        call_count = {'count': 0}

        def mock_get(cid):
            call_count['count'] += 1
            if call_count['count'] <= 2:
                raise HerpRateLimitError("Rate limit")
            return {'id': cid, 'name': 'Test'}

        mock_herp_client.get_candidacy = Mock(side_effect=mock_get)

        result = batch_client.fetch_candidacies_batch(['cand_1'])

        assert len(result.successful) == 1
        assert len(result.failed) == 0
        assert call_count['count'] == 3  # Failed twice, succeeded on third

    def test_no_retry_on_permanent_error(self, batch_client, mock_herp_client):
        """Test no retry on permanent errors"""
        call_count = {'count': 0}

        def mock_get(cid):
            call_count['count'] += 1
            raise HerpAPIError("Not found")  # Permanent error

        mock_herp_client.get_candidacy = Mock(side_effect=mock_get)

        # Disable retry for this test
        batch_client.retry_transient = False

        result = batch_client.fetch_candidacies_batch(['cand_1'])

        assert len(result.successful) == 0
        assert len(result.failed) == 1
        assert call_count['count'] == 1  # Only called once, no retry

    def test_max_retries_exceeded(self, batch_client, mock_herp_client):
        """Test failure when max retries exceeded"""
        # Always fail
        mock_herp_client.get_candidacy = Mock(
            side_effect=HerpRateLimitError("Rate limit")
        )

        batch_client.max_retries = 2

        result = batch_client.fetch_candidacies_batch(['cand_1'])

        assert len(result.successful) == 0
        assert len(result.failed) == 1
        # Called 3 times: initial + 2 retries
        assert mock_herp_client.get_candidacy.call_count == 3


class TestPerformance:
    """Performance-related tests"""

    def test_concurrent_execution_faster_than_sequential(self, mock_herp_client):
        """Test that concurrent execution is faster"""
        # Simulate slow operation (100ms each)
        def slow_get(cid):
            time.sleep(0.1)
            return {'id': cid}

        mock_herp_client.get_candidacy = Mock(side_effect=slow_get)

        # Sequential would take 1 second for 10 items (10 * 0.1s)
        # Concurrent with 5 workers should take ~0.2s (2 batches)

        batch_client = BatchHerpClient(mock_herp_client, max_workers=5)

        start = time.time()
        result = batch_client.fetch_candidacies_batch(
            [f'cand_{i}' for i in range(10)]
        )
        duration = time.time() - start

        assert len(result.successful) == 10
        # Should be significantly faster than sequential (< 0.5s instead of 1s)
        assert duration < 0.5

    def test_records_duration(self, batch_client, mock_herp_client):
        """Test that duration is recorded"""
        mock_herp_client.get_candidacy = Mock(return_value={'id': 'test'})

        result = batch_client.fetch_candidacies_batch(['cand_1', 'cand_2'])

        assert result.duration_seconds > 0
        assert isinstance(result.duration_seconds, float)
