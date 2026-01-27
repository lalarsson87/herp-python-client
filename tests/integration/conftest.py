"""
Shared configuration for integration tests

Provides common fixtures and VCR configuration.
"""

import os

import pytest


@pytest.fixture(scope="session")
def integration_test_config():
    """
    Configuration for integration tests

    Returns dict with test configuration including API credentials.
    """
    return {
        "herp_api_key": os.getenv("HERP_API_KEY", "test_api_key_for_vcr_playback"),
        "herp_base_url": os.getenv(
            "HERP_BASE_URL", "https://public-api.herp.cloud/hire/public"
        ),
        "vcr_mode": os.getenv("VCR_MODE", "once"),  # once, new_episodes, all
    }


@pytest.fixture(scope="session", autouse=True)
def check_vcr_setup():
    """
    Check if pytest-vcr is available and properly configured
    """
    try:
        import vcr  # noqa: F401
    except ImportError:
        pytest.skip("pytest-vcr not installed. Install with: pip install pytest-vcr")


def pytest_configure(config):
    """Register integration test marker"""
    config.addinivalue_line(
        "markers", "integration: Integration tests with real API interactions (use VCR)"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to handle integration tests

    - Skip integration tests if --integration flag not provided
    - Add integration marker to all tests in integration directory
    """
    skip_integration = pytest.mark.skip(
        reason="Use --integration to run integration tests"
    )

    for item in items:
        # Add integration marker to all tests in integration directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Skip integration tests unless --integration flag provided
        if "integration" in item.keywords:
            if not config.getoption("--integration", default=False):
                item.add_marker(skip_integration)


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests (requires API credentials or VCR cassettes)",
    )
    parser.addoption(
        "--record-vcr",
        action="store_true",
        default=False,
        help="Re-record VCR cassettes (requires API credentials)",
    )
