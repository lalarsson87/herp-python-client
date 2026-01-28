#!/usr/bin/env python3
"""
Configuration and Environment Variable Management

Provides centralized configuration loading from environment variables
with validation, defaults, and type safety.

This is the SINGLE SOURCE OF TRUTH for all environment variable configuration.
All modules should import configuration from this module, never read os.getenv directly.
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from ..constants import (
    ANALYSIS_TEMP_DIR,
    METRICS_EXPORT_PATH,
    SYNC_FILES_DIR,
    SYNC_LOG_FILE_PATH,
    SYNC_STATE_FILE_PATH,
)


@dataclass
class HerpConfig:
    """HERP API configuration"""

    api_key: str
    base_url: str
    rate_limit: int = 100  # requests per minute
    timeout: int = 30  # request timeout in seconds

    @property
    def rate_limit_delay(self) -> float:
        """Calculate delay between requests in seconds"""
        return 60.0 / self.rate_limit


@dataclass
class NotionConfig:
    """Notion API configuration"""

    api_key: str
    api_version: str = "2022-06-28"
    rate_limit: int = 3  # requests per second
    candidates_db_id: Optional[str] = None
    interviews_db_id: Optional[str] = None
    evaluations_db_id: Optional[str] = None

    @property
    def rate_limit_delay(self) -> float:
        """Calculate delay between requests in seconds"""
        return 1.0 / self.rate_limit


# ============================================================================
# Validation Configuration
# ============================================================================


class ValidationMode(Enum):
    """Validation strictness modes"""

    STRICT = "strict"  # Fail on any validation error
    LENIENT = "lenient"  # Log warnings but continue
    DISABLED = "disabled"  # Skip validation entirely


@dataclass
class ValidationConfig:
    """Response validation configuration"""

    mode: ValidationMode = ValidationMode.LENIENT
    log_errors: bool = True
    collect_errors: bool = False  # Collect errors for reporting

    def is_strict(self) -> bool:
        """Check if validation is in strict mode"""
        return self.mode == ValidationMode.STRICT

    def is_enabled(self) -> bool:
        """Check if validation is enabled"""
        return self.mode != ValidationMode.DISABLED


# ============================================================================
# Logging Configuration
# ============================================================================


@dataclass
class LoggingConfig:
    """Logging configuration"""

    level: int = logging.INFO
    format: str = "console"  # 'console' or 'json'
    file_path: Optional[Path] = None

    @property
    def level_name(self) -> str:
        """Get logging level name"""
        return logging.getLevelName(self.level)


# ============================================================================
# Analysis Configuration
# ============================================================================


@dataclass
class AnalysisConfig:
    """Candidate analysis configuration"""

    use_claude_cli: bool = True
    enable_github_analysis: bool = True
    enable_linkedin_analysis: bool = False
    generate_interview_questions: bool = True
    update_notion: bool = True
    temp_dir: Path = Path(ANALYSIS_TEMP_DIR)


# ============================================================================
# Application Configuration
# ============================================================================


@dataclass
class AppConfig:
    """
    Application-level configuration (unified config for entire application)

    This is the SINGLE SOURCE OF TRUTH for all configuration.
    All modules should use this config instead of reading environment variables directly.
    """

    # API clients
    herp: HerpConfig
    notion: NotionConfig

    # Feature configs
    validation: ValidationConfig
    logging: LoggingConfig
    analysis: AnalysisConfig

    # Paths
    files_dir: Path = Path(SYNC_FILES_DIR)
    logs_dir: Path = Path(SYNC_LOG_FILE_PATH).parent
    sync_state_file: Path = Path(SYNC_STATE_FILE_PATH)
    metrics_export_path: Path = Path(METRICS_EXPORT_PATH)

    def __post_init__(self):
        """Ensure directories exist"""
        self.files_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_export_path.parent.mkdir(parents=True, exist_ok=True)


def load_herp_config() -> HerpConfig:
    """
    Load HERP API configuration from environment variables

    Required environment variables:
    - HERP_API_KEY: HERP API authentication key

    Optional environment variables:
    - HERP_API_BASE_URL: HERP API base URL (default: https://public-api.herp.cloud/hire/public)
    - HERP_RATE_LIMIT: Rate limit in requests/minute (default: 100)
    - HERP_TIMEOUT: Request timeout in seconds (default: 30)

    Returns:
        HerpConfig instance

    Raises:
        ValueError: If required environment variables are missing
    """
    api_key = os.getenv("HERP_API_KEY", "")
    if not api_key:
        raise ValueError("HERP_API_KEY environment variable is required")

    base_url = os.getenv(
        "HERP_API_BASE_URL",
        "https://public-api.herp.cloud/hire",  # Production URL (not /hire/public)
    )

    rate_limit = int(os.getenv("HERP_RATE_LIMIT", "100"))
    timeout = int(os.getenv("HERP_TIMEOUT", "30"))

    return HerpConfig(
        api_key=api_key, base_url=base_url, rate_limit=rate_limit, timeout=timeout
    )


def load_notion_config() -> NotionConfig:
    """
    Load Notion API configuration from environment variables

    Required environment variables:
    - NOTION_API_KEY: Notion API authentication key

    Optional environment variables:
    - NOTION_API_VERSION: Notion API version (default: 2022-06-28)
    - NOTION_RATE_LIMIT: Rate limit in requests/second (default: 3)
    - NOTION_CANDIDATES_DB_ID: Candidates database ID
    - NOTION_INTERVIEWS_DB_ID: Interviews database ID
    - NOTION_EVALUATIONS_DB_ID: Evaluations database ID

    Returns:
        NotionConfig instance

    Raises:
        ValueError: If required environment variables are missing
    """
    api_key = os.getenv("NOTION_API_KEY", "")
    if not api_key:
        raise ValueError("NOTION_API_KEY environment variable is required")

    api_version = os.getenv("NOTION_API_VERSION", "2022-06-28")
    rate_limit = int(os.getenv("NOTION_RATE_LIMIT", "3"))

    return NotionConfig(
        api_key=api_key,
        api_version=api_version,
        rate_limit=rate_limit,
        candidates_db_id=os.getenv("NOTION_CANDIDATES_DB_ID"),
        interviews_db_id=os.getenv("NOTION_INTERVIEWS_DB_ID"),
        evaluations_db_id=os.getenv("NOTION_EVALUATIONS_DB_ID"),
    )


def load_validation_config() -> ValidationConfig:
    """
    Load validation configuration from environment variables

    Optional environment variables:
    - VALIDATION_MODE: Validation mode (strict/lenient/disabled, default: lenient)
    - VALIDATION_LOG_ERRORS: Log validation errors (true/false, default: true)
    - VALIDATION_COLLECT_ERRORS: Collect errors for reporting (true/false, default: false)

    Returns:
        ValidationConfig instance
    """
    mode_str = os.getenv("VALIDATION_MODE", "lenient").lower()

    # Map string to enum
    mode_map = {
        "strict": ValidationMode.STRICT,
        "lenient": ValidationMode.LENIENT,
        "disabled": ValidationMode.DISABLED,
        "off": ValidationMode.DISABLED,
        "none": ValidationMode.DISABLED,
    }

    mode = mode_map.get(mode_str, ValidationMode.LENIENT)
    log_errors = os.getenv("VALIDATION_LOG_ERRORS", "true").lower() == "true"
    collect_errors = os.getenv("VALIDATION_COLLECT_ERRORS", "false").lower() == "true"

    return ValidationConfig(
        mode=mode, log_errors=log_errors, collect_errors=collect_errors
    )


def load_logging_config() -> LoggingConfig:
    """
    Load logging configuration from environment variables

    Optional environment variables:
    - LOG_LEVEL: Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL, default: INFO)
    - LOG_FORMAT: Log format (console/json, default: console)
    - LOG_FILE: Log file path (optional)

    Returns:
        LoggingConfig instance
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    format_str = os.getenv("LOG_FORMAT", "console").lower()
    file_path_str = os.getenv("LOG_FILE")
    file_path = Path(file_path_str) if file_path_str else None

    return LoggingConfig(level=level, format=format_str, file_path=file_path)


def load_analysis_config() -> AnalysisConfig:
    """
    Load candidate analysis configuration from environment variables

    Optional environment variables:
    - USE_CLAUDE_CLI: Use Claude CLI for analysis (true/false, default: true)
    - ENABLE_GITHUB_ANALYSIS: Enable GitHub profile analysis (true/false, default: true)
    - ENABLE_LINKEDIN_ANALYSIS: Enable LinkedIn analysis (true/false, default: false)
    - GENERATE_INTERVIEW_QUESTIONS: Generate interview questions (true/false, default: true)
    - UPDATE_NOTION: Update Notion with analysis results (true/false, default: true)

    Returns:
        AnalysisConfig instance
    """
    return AnalysisConfig(
        use_claude_cli=os.getenv("USE_CLAUDE_CLI", "true").lower() == "true",
        enable_github_analysis=os.getenv("ENABLE_GITHUB_ANALYSIS", "true").lower()
        == "true",
        enable_linkedin_analysis=os.getenv("ENABLE_LINKEDIN_ANALYSIS", "false").lower()
        == "true",
        generate_interview_questions=os.getenv(
            "GENERATE_INTERVIEW_QUESTIONS", "true"
        ).lower()
        == "true",
        update_notion=os.getenv("UPDATE_NOTION", "true").lower() == "true",
        temp_dir=Path(ANALYSIS_TEMP_DIR),
    )


def load_config() -> AppConfig:
    """
    Load complete application configuration from environment variables

    This is the MAIN configuration loader - use this for production code.
    Loads all configuration from environment variables with sensible defaults.

    Required environment variables:
    - HERP_API_KEY: HERP API authentication key
    - NOTION_API_KEY: Notion API authentication key

    Optional environment variables:

    **HERP API:**
    - HERP_API_BASE_URL: HERP API base URL (default: https://public-api.herp.cloud/hire)
    - HERP_RATE_LIMIT: Rate limit in requests/minute (default: 100)

    **Notion API:**
    - NOTION_API_VERSION: Notion API version (default: 2022-06-28)
    - NOTION_RATE_LIMIT: Rate limit in requests/second (default: 3)
    - NOTION_CANDIDATES_DB_ID: Candidates database ID
    - NOTION_INTERVIEWS_DB_ID: Interviews database ID
    - NOTION_EVALUATIONS_DB_ID: Evaluations database ID

    **Validation:**
    - VALIDATION_MODE: Validation mode (strict/lenient/disabled, default: lenient)
    - VALIDATION_LOG_ERRORS: Log validation errors (true/false, default: true)
    - VALIDATION_COLLECT_ERRORS: Collect errors (true/false, default: false)

    **Logging:**
    - LOG_LEVEL: Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL, default: INFO)
    - LOG_FORMAT: Log format (console/json, default: console)
    - LOG_FILE: Log file path (optional)

    **Analysis:**
    - USE_CLAUDE_CLI: Use Claude CLI (true/false, default: true)
    - ENABLE_GITHUB_ANALYSIS: Enable GitHub analysis (true/false, default: true)
    - ENABLE_LINKEDIN_ANALYSIS: Enable LinkedIn analysis (true/false, default: false)
    - GENERATE_INTERVIEW_QUESTIONS: Generate questions (true/false, default: true)
    - UPDATE_NOTION: Update Notion with results (true/false, default: true)

    **Paths:**
    - SYNC_BASE_DIR: Base directory for all sync files (default: ./data)
    - SYNC_FILES_DIR: Directory for candidate files (default: SYNC_BASE_DIR/candidate-files)
    - SYNC_LOG_FILE: Log file path (default: SYNC_BASE_DIR/logs/sync.log)
    - SYNC_STATE_FILE: Sync state file path (default: SYNC_BASE_DIR/sync-state.json)
    - METRICS_EXPORT_PATH: Metrics export path (default: SYNC_BASE_DIR/metrics/metrics.json)
    - ANALYSIS_TEMP_DIR: Analysis temp directory (default: SYNC_BASE_DIR/analysis)

    Returns:
        AppConfig instance with all configurations loaded

    Raises:
        ValueError: If required environment variables are missing

    Example:
        >>> config = load_config()
        >>> client = HerpClient(config.herp)
        >>> notion = NotionClient(config.notion)
    """
    herp_config = load_herp_config()
    notion_config = load_notion_config()
    validation_config = load_validation_config()
    logging_config = load_logging_config()
    analysis_config = load_analysis_config()

    # Use constants which already read from environment variables
    files_dir = Path(SYNC_FILES_DIR)
    logs_dir = Path(SYNC_LOG_FILE_PATH).parent
    sync_state_file = Path(SYNC_STATE_FILE_PATH)
    metrics_export_path = Path(METRICS_EXPORT_PATH)

    return AppConfig(
        herp=herp_config,
        notion=notion_config,
        validation=validation_config,
        logging=logging_config,
        analysis=analysis_config,
        files_dir=files_dir,
        logs_dir=logs_dir,
        sync_state_file=sync_state_file,
        metrics_export_path=metrics_export_path,
    )


def validate_config(config: AppConfig, require_notion_db: bool = True) -> bool:
    """
    Validate configuration completeness

    Args:
        config: Application configuration to validate
        require_notion_db: Whether to require Notion database IDs

    Returns:
        True if configuration is valid

    Raises:
        ValueError: If configuration is invalid
    """
    # Validate HERP config
    if not config.herp.api_key:
        raise ValueError("HERP API key is required")
    if not config.herp.base_url:
        raise ValueError("HERP base URL is required")

    # Validate Notion config
    if not config.notion.api_key:
        raise ValueError("Notion API key is required")

    if require_notion_db and not config.notion.candidates_db_id:
        raise ValueError("Notion candidates database ID is required")

    return True
