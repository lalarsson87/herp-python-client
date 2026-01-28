"""
Health Check Utilities

Provides health checking and validation for HERP client operations.
"""

import os
from typing import Any, Dict

from ..herp import HerpClient
from .config import load_herp_config
from .logging import get_logger

logger = get_logger(__name__)


def check_api_connectivity() -> Dict[str, Any]:
    """
    Check HERP API connectivity

    Returns:
        Health check result with status and details
    """
    try:
        config = load_herp_config()
        client = HerpClient(config)

        # Try to fetch a small amount of data
        candidacies = client.candidacies.list(page=1, limit=1)

        return {
            "healthy": True,
            "message": "API is accessible",
            "details": {
                "base_url": config.base_url,
                "response_received": len(candidacies) >= 0,
            },
        }

    except Exception as e:
        return {
            "healthy": False,
            "message": f"API connection failed: {str(e)}",
            "details": {
                "error_type": type(e).__name__,
            },
        }


def check_rate_limiter() -> Dict[str, Any]:
    """
    Check rate limiter health

    Returns:
        Health check result
    """
    try:
        config = load_herp_config()
        client = HerpClient(config)

        # Check rate limiter state
        rate_limiter = client.base_client.rate_limiter

        return {
            "healthy": True,
            "message": "Rate limiter operational",
            "details": {
                "requests_per_minute": rate_limiter.requests_per_minute,
                "current_tokens": getattr(rate_limiter, "current_tokens", "N/A"),
            },
        }

    except Exception as e:
        return {
            "healthy": False,
            "message": f"Rate limiter check failed: {str(e)}",
        }


def check_cache() -> Dict[str, Any]:
    """
    Check cache health

    Returns:
        Health check result
    """
    try:
        from ..cache.manager import CacheManager

        # Try to get global cache manager instance
        cache_manager = None
        try:
            from ..cache.manager import _global_cache_manager
            cache_manager = _global_cache_manager
        except (ImportError, AttributeError):
            pass

        if cache_manager is None:
            return {
                "healthy": True,
                "message": "Cache disabled",
                "details": {"enabled": False},
            }

        stats = cache_manager.get_stats()

        return {
            "healthy": True,
            "message": "Cache operational",
            "details": {
                "size": stats.get("size", 0),
                "max_size": stats.get("max_size", 0),
                "enabled": True,
            },
        }

    except Exception as e:
        return {
            "healthy": False,
            "message": f"Cache check failed: {str(e)}",
        }


def check_configuration() -> Dict[str, Any]:
    """
    Check configuration validity

    Returns:
        Health check result
    """
    try:
        config = load_herp_config()

        issues = []

        # Check required fields
        if not config.api_token:
            issues.append("API token not set")

        if not config.base_url:
            issues.append("Base URL not set")

        if config.rate_limit <= 0:
            issues.append("Invalid rate limit")

        if config.timeout <= 0:
            issues.append("Invalid timeout")

        if issues:
            return {
                "healthy": False,
                "message": f"Configuration issues: {', '.join(issues)}",
            }

        return {
            "healthy": True,
            "message": "Configuration valid",
            "details": {
                "base_url": config.base_url,
                "rate_limit": config.rate_limit,
                "timeout": config.timeout,
            },
        }

    except Exception as e:
        return {
            "healthy": False,
            "message": f"Configuration check failed: {str(e)}",
        }


def perform_health_check() -> Dict[str, Dict[str, Any]]:
    """
    Perform comprehensive health check

    Returns:
        Dictionary of health check results
    """
    return {
        "Configuration": check_configuration(),
        "API Connectivity": check_api_connectivity(),
        "Rate Limiter": check_rate_limiter(),
        "Cache": check_cache(),
    }


def validate_configuration() -> Dict[str, Dict[str, Any]]:
    """
    Validate configuration settings

    Returns:
        Dictionary of validation results
    """
    results = {}

    # Check environment variables
    api_token = os.getenv("HERP_API_TOKEN")
    base_url = os.getenv("HERP_BASE_URL")

    results["API Token"] = {
        "valid": bool(api_token),
        "message": "API token is set" if api_token else "API token not found",
        "suggestion": (
            "Set HERP_API_TOKEN environment variable" if not api_token else None
        ),
    }

    results["Base URL"] = {
        "valid": bool(base_url),
        "message": "Base URL is set" if base_url else "Base URL not found",
        "suggestion": (
            "Set HERP_BASE_URL environment variable" if not base_url else None
        ),
    }

    # Check optional settings
    rate_limit = os.getenv("HERP_RATE_LIMIT", "100")
    try:
        rate_limit_int = int(rate_limit)
        valid_rate = 1 <= rate_limit_int <= 1000
        results["Rate Limit"] = {
            "valid": valid_rate,
            "message": (
                f"Rate limit: {rate_limit_int} req/min"
                if valid_rate
                else f"Invalid rate limit: {rate_limit_int}"
            ),
            "suggestion": (
                "Set HERP_RATE_LIMIT between 1-1000" if not valid_rate else None
            ),
        }
    except ValueError:
        results["Rate Limit"] = {
            "valid": False,
            "message": f"Invalid rate limit value: {rate_limit}",
            "suggestion": "HERP_RATE_LIMIT must be an integer",
        }

    timeout = os.getenv("HERP_TIMEOUT", "30")
    try:
        timeout_int = int(timeout)
        valid_timeout = 1 <= timeout_int <= 300
        results["Timeout"] = {
            "valid": valid_timeout,
            "message": (
                f"Timeout: {timeout_int}s"
                if valid_timeout
                else f"Invalid timeout: {timeout_int}s"
            ),
            "suggestion": (
                "Set HERP_TIMEOUT between 1-300" if not valid_timeout else None
            ),
        }
    except ValueError:
        results["Timeout"] = {
            "valid": False,
            "message": f"Invalid timeout value: {timeout}",
            "suggestion": "HERP_TIMEOUT must be an integer",
        }

    # Check cache settings
    cache_enabled = os.getenv("HERP_CACHE_ENABLED", "false").lower() == "true"
    results["Cache"] = {
        "valid": True,
        "message": f"Cache {'enabled' if cache_enabled else 'disabled'}",
    }

    return results


def get_system_info() -> Dict[str, Any]:
    """
    Get system information for debugging

    Returns:
        System information dictionary
    """
    import platform
    import sys

    try:
        from importlib.metadata import version

        package_version = version("herp-python-client")
    except Exception:
        package_version = "unknown"

    return {
        "package_version": package_version,
        "python_version": sys.version,
        "platform": platform.platform(),
        "architecture": platform.machine(),
    }
