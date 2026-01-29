"""
Tests for Configuration Module
"""

import logging
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.utils.config import (
    AnalysisConfig,
    AppConfig,
    HerpConfig,
    LoggingConfig,
    NotionConfig,
    ValidationConfig,
    ValidationMode,
    load_analysis_config,
    load_config,
    load_herp_config,
    load_logging_config,
    load_notion_config,
    load_validation_config,
    validate_config,
)


class TestHerpConfig:
    """Test HERP configuration dataclass"""

    def test_initialization(self):
        """Test HerpConfig initialization"""
        config = HerpConfig(
            api_key="test_key",
            base_url="https://api.example.com",
            rate_limit=100,
            timeout=30,
        )

        assert config.api_key == "test_key"
        assert config.base_url == "https://api.example.com"
        assert config.rate_limit == 100
        assert config.timeout == 30

    def test_rate_limit_delay_calculation(self):
        """Test rate limit delay calculation"""
        config = HerpConfig(
            api_key="test_key",
            base_url="https://api.example.com",
            rate_limit=60,  # 60 requests per minute
        )

        # 60 requests per minute = 1 request per second
        assert config.rate_limit_delay == 1.0

    def test_rate_limit_delay_100_rpm(self):
        """Test rate limit delay for 100 requests per minute"""
        config = HerpConfig(
            api_key="test_key",
            base_url="https://api.example.com",
            rate_limit=100,
        )

        # 100 requests per minute = 0.6 seconds per request
        assert config.rate_limit_delay == 0.6


class TestNotionConfig:
    """Test Notion configuration dataclass"""

    def test_initialization_minimal(self):
        """Test NotionConfig with minimal fields"""
        config = NotionConfig(api_key="test_key")

        assert config.api_key == "test_key"
        assert config.api_version == "2022-06-28"
        assert config.rate_limit == 3
        assert config.candidates_db_id is None

    def test_initialization_complete(self):
        """Test NotionConfig with all fields"""
        config = NotionConfig(
            api_key="test_key",
            api_version="2023-01-01",
            rate_limit=5,
            candidates_db_id="db_candidates",
            interviews_db_id="db_interviews",
            evaluations_db_id="db_evaluations",
        )

        assert config.api_version == "2023-01-01"
        assert config.rate_limit == 5
        assert config.candidates_db_id == "db_candidates"
        assert config.interviews_db_id == "db_interviews"
        assert config.evaluations_db_id == "db_evaluations"

    def test_rate_limit_delay_calculation(self):
        """Test Notion rate limit delay calculation"""
        config = NotionConfig(api_key="test_key", rate_limit=3)

        # 3 requests per second = 0.333... seconds per request
        assert abs(config.rate_limit_delay - 0.3333333) < 0.0001


class TestValidationConfig:
    """Test validation configuration"""

    def test_initialization_defaults(self):
        """Test ValidationConfig default values"""
        config = ValidationConfig()

        assert config.mode == ValidationMode.LENIENT
        assert config.log_errors is True
        assert config.collect_errors is False

    def test_is_strict(self):
        """Test is_strict check"""
        strict_config = ValidationConfig(mode=ValidationMode.STRICT)
        lenient_config = ValidationConfig(mode=ValidationMode.LENIENT)

        assert strict_config.is_strict() is True
        assert lenient_config.is_strict() is False

    def test_is_enabled(self):
        """Test is_enabled check"""
        enabled = ValidationConfig(mode=ValidationMode.LENIENT)
        disabled = ValidationConfig(mode=ValidationMode.DISABLED)

        assert enabled.is_enabled() is True
        assert disabled.is_enabled() is False


class TestLoggingConfig:
    """Test logging configuration"""

    def test_initialization_defaults(self):
        """Test LoggingConfig default values"""
        config = LoggingConfig()

        assert config.level == logging.INFO
        assert config.format == "console"
        assert config.file_path is None

    def test_level_name_property(self):
        """Test level_name property"""
        debug_config = LoggingConfig(level=logging.DEBUG)
        info_config = LoggingConfig(level=logging.INFO)
        error_config = LoggingConfig(level=logging.ERROR)

        assert debug_config.level_name == "DEBUG"
        assert info_config.level_name == "INFO"
        assert error_config.level_name == "ERROR"


class TestAnalysisConfig:
    """Test analysis configuration"""

    def test_initialization_defaults(self):
        """Test AnalysisConfig default values"""
        config = AnalysisConfig()

        assert config.use_claude_cli is True
        assert config.enable_github_analysis is True
        assert config.enable_linkedin_analysis is False
        assert config.generate_interview_questions is True
        assert config.update_notion is True


class TestLoadHerpConfig:
    """Test loading HERP configuration from environment"""

    @patch.dict(
        os.environ,
        {
            "HERP_API_KEY": "test_api_key",
            "HERP_API_BASE_URL": "https://test.api.com",
            "HERP_RATE_LIMIT": "200",
            "HERP_TIMEOUT": "60",
        },
    )
    def test_load_with_all_env_vars(self):
        """Test loading HERP config with all environment variables"""
        config = load_herp_config()

        assert config.api_key == "test_api_key"
        assert config.base_url == "https://test.api.com"
        assert config.rate_limit == 200
        assert config.timeout == 60

    @patch.dict(os.environ, {"HERP_API_KEY": "test_key"}, clear=True)
    def test_load_with_defaults(self):
        """Test loading HERP config uses defaults"""
        config = load_herp_config()

        assert config.api_key == "test_key"
        assert config.base_url == "https://public-api.herp.cloud/hire"
        assert config.rate_limit == 100
        assert config.timeout == 30

    @patch.dict(os.environ, {}, clear=True)
    def test_load_without_api_key_raises(self):
        """Test loading without API key raises ValueError"""
        with pytest.raises(
            ValueError, match="HERP_API_KEY environment variable is required"
        ):
            load_herp_config()


class TestLoadNotionConfig:
    """Test loading Notion configuration from environment"""

    @patch.dict(
        os.environ,
        {
            "NOTION_API_KEY": "test_notion_key",
            "NOTION_API_VERSION": "2023-01-01",
            "NOTION_RATE_LIMIT": "5",
            "NOTION_CANDIDATES_DB_ID": "db_cand",
            "NOTION_INTERVIEWS_DB_ID": "db_int",
            "NOTION_EVALUATIONS_DB_ID": "db_eval",
        },
    )
    def test_load_with_all_env_vars(self):
        """Test loading Notion config with all environment variables"""
        config = load_notion_config()

        assert config.api_key == "test_notion_key"
        assert config.api_version == "2023-01-01"
        assert config.rate_limit == 5
        assert config.candidates_db_id == "db_cand"
        assert config.interviews_db_id == "db_int"
        assert config.evaluations_db_id == "db_eval"

    @patch.dict(os.environ, {"NOTION_API_KEY": "test_key"}, clear=True)
    def test_load_with_defaults(self):
        """Test loading Notion config uses defaults"""
        config = load_notion_config()

        assert config.api_key == "test_key"
        assert config.api_version == "2022-06-28"
        assert config.rate_limit == 3
        assert config.candidates_db_id is None

    @patch.dict(os.environ, {}, clear=True)
    def test_load_without_api_key_raises(self):
        """Test loading without API key raises ValueError"""
        with pytest.raises(
            ValueError, match="NOTION_API_KEY environment variable is required"
        ):
            load_notion_config()


class TestLoadValidationConfig:
    """Test loading validation configuration from environment"""

    @patch.dict(
        os.environ,
        {
            "VALIDATION_MODE": "strict",
            "VALIDATION_LOG_ERRORS": "true",
            "VALIDATION_COLLECT_ERRORS": "true",
        },
    )
    def test_load_strict_mode(self):
        """Test loading strict validation mode"""
        config = load_validation_config()

        assert config.mode == ValidationMode.STRICT
        assert config.log_errors is True
        assert config.collect_errors is True

    @patch.dict(os.environ, {"VALIDATION_MODE": "disabled"})
    def test_load_disabled_mode(self):
        """Test loading disabled validation mode"""
        config = load_validation_config()

        assert config.mode == ValidationMode.DISABLED

    @patch.dict(os.environ, {"VALIDATION_MODE": "off"})
    def test_load_off_mode_maps_to_disabled(self):
        """Test 'off' mode maps to disabled"""
        config = load_validation_config()

        assert config.mode == ValidationMode.DISABLED

    @patch.dict(os.environ, {}, clear=True)
    def test_load_with_defaults(self):
        """Test loading validation config uses defaults"""
        config = load_validation_config()

        assert config.mode == ValidationMode.LENIENT
        assert config.log_errors is True
        assert config.collect_errors is False

    @patch.dict(
        os.environ,
        {"VALIDATION_LOG_ERRORS": "false", "VALIDATION_COLLECT_ERRORS": "true"},
    )
    def test_load_boolean_parsing(self):
        """Test boolean environment variable parsing"""
        config = load_validation_config()

        assert config.log_errors is False
        assert config.collect_errors is True


class TestLoadLoggingConfig:
    """Test loading logging configuration from environment"""

    @patch.dict(
        os.environ,
        {
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT": "json",
            "LOG_FILE": "/var/log/app.log",
        },
    )
    def test_load_with_all_env_vars(self):
        """Test loading logging config with all environment variables"""
        config = load_logging_config()

        assert config.level == logging.DEBUG
        assert config.format == "json"
        assert config.file_path == Path("/var/log/app.log")

    @patch.dict(os.environ, {}, clear=True)
    def test_load_with_defaults(self):
        """Test loading logging config uses defaults"""
        config = load_logging_config()

        assert config.level == logging.INFO
        assert config.format == "console"
        assert config.file_path is None

    @patch.dict(os.environ, {"LOG_LEVEL": "WARNING"})
    def test_load_warning_level(self):
        """Test loading WARNING log level"""
        config = load_logging_config()

        assert config.level == logging.WARNING

    @patch.dict(os.environ, {"LOG_LEVEL": "INVALID_LEVEL"})
    def test_load_invalid_level_defaults_to_info(self):
        """Test invalid log level defaults to INFO"""
        config = load_logging_config()

        # getattr with default returns INFO for invalid level name
        assert config.level == logging.INFO


class TestLoadAnalysisConfig:
    """Test loading analysis configuration from environment"""

    @patch.dict(
        os.environ,
        {
            "USE_CLAUDE_CLI": "false",
            "ENABLE_GITHUB_ANALYSIS": "false",
            "ENABLE_LINKEDIN_ANALYSIS": "true",
            "GENERATE_INTERVIEW_QUESTIONS": "false",
            "UPDATE_NOTION": "false",
        },
    )
    def test_load_with_custom_values(self):
        """Test loading analysis config with custom values"""
        config = load_analysis_config()

        assert config.use_claude_cli is False
        assert config.enable_github_analysis is False
        assert config.enable_linkedin_analysis is True
        assert config.generate_interview_questions is False
        assert config.update_notion is False

    @patch.dict(os.environ, {}, clear=True)
    def test_load_with_defaults(self):
        """Test loading analysis config uses defaults"""
        config = load_analysis_config()

        assert config.use_claude_cli is True
        assert config.enable_github_analysis is True
        assert config.enable_linkedin_analysis is False


class TestLoadConfig:
    """Test loading complete application configuration"""

    @patch.dict(
        os.environ,
        {
            "HERP_API_KEY": "herp_key",
            "NOTION_API_KEY": "notion_key",
        },
        clear=True,
    )
    def test_load_complete_config(self):
        """Test loading complete application config"""
        config = load_config()

        assert isinstance(config, AppConfig)
        assert isinstance(config.herp, HerpConfig)
        assert isinstance(config.notion, NotionConfig)
        assert isinstance(config.validation, ValidationConfig)
        assert isinstance(config.logging, LoggingConfig)
        assert isinstance(config.analysis, AnalysisConfig)

        assert config.herp.api_key == "herp_key"
        assert config.notion.api_key == "notion_key"

    @patch.dict(os.environ, {"HERP_API_KEY": "herp_key"}, clear=True)
    def test_load_config_missing_notion_key(self):
        """Test loading config without Notion API key raises"""
        with pytest.raises(
            ValueError, match="NOTION_API_KEY environment variable is required"
        ):
            load_config()

    @patch.dict(os.environ, {"NOTION_API_KEY": "notion_key"}, clear=True)
    def test_load_config_missing_herp_key(self):
        """Test loading config without HERP API key raises"""
        with pytest.raises(
            ValueError, match="HERP_API_KEY environment variable is required"
        ):
            load_config()


class TestAppConfig:
    """Test AppConfig dataclass"""

    @patch.dict(
        os.environ,
        {
            "HERP_API_KEY": "herp_key",
            "NOTION_API_KEY": "notion_key",
        },
        clear=True,
    )
    def test_post_init_creates_directories(self, tmp_path):
        """Test __post_init__ creates necessary directories"""
        # Use temporary paths
        files_dir = tmp_path / "files"
        logs_dir = tmp_path / "logs"
        metrics_dir = tmp_path / "metrics"

        config = AppConfig(
            herp=HerpConfig(api_key="test", base_url="https://api.test.com"),
            notion=NotionConfig(api_key="test"),
            validation=ValidationConfig(),
            logging=LoggingConfig(),
            analysis=AnalysisConfig(),
            files_dir=files_dir,
            logs_dir=logs_dir,
            metrics_export_path=metrics_dir / "metrics.json",
        )

        # Directories should be created
        assert files_dir.exists()
        assert logs_dir.exists()
        assert metrics_dir.exists()


class TestValidateConfig:
    """Test configuration validation"""

    def test_validate_valid_config(self):
        """Test validating valid configuration"""
        config = AppConfig(
            herp=HerpConfig(api_key="test_key", base_url="https://api.test.com"),
            notion=NotionConfig(api_key="test_key", candidates_db_id="db_123"),
            validation=ValidationConfig(),
            logging=LoggingConfig(),
            analysis=AnalysisConfig(),
        )

        assert validate_config(config) is True

    def test_validate_missing_herp_api_key(self):
        """Test validation fails with missing HERP API key"""
        config = AppConfig(
            herp=HerpConfig(api_key="", base_url="https://api.test.com"),
            notion=NotionConfig(api_key="test_key", candidates_db_id="db_123"),
            validation=ValidationConfig(),
            logging=LoggingConfig(),
            analysis=AnalysisConfig(),
        )

        with pytest.raises(ValueError, match="HERP API key is required"):
            validate_config(config)

    def test_validate_missing_herp_base_url(self):
        """Test validation fails with missing HERP base URL"""
        config = AppConfig(
            herp=HerpConfig(api_key="test_key", base_url=""),
            notion=NotionConfig(api_key="test_key", candidates_db_id="db_123"),
            validation=ValidationConfig(),
            logging=LoggingConfig(),
            analysis=AnalysisConfig(),
        )

        with pytest.raises(ValueError, match="HERP base URL is required"):
            validate_config(config)

    def test_validate_missing_notion_api_key(self):
        """Test validation fails with missing Notion API key"""
        config = AppConfig(
            herp=HerpConfig(api_key="test_key", base_url="https://api.test.com"),
            notion=NotionConfig(api_key=""),
            validation=ValidationConfig(),
            logging=LoggingConfig(),
            analysis=AnalysisConfig(),
        )

        with pytest.raises(ValueError, match="Notion API key is required"):
            validate_config(config)

    def test_validate_missing_notion_db_when_required(self):
        """Test validation fails with missing Notion database ID when required"""
        config = AppConfig(
            herp=HerpConfig(api_key="test_key", base_url="https://api.test.com"),
            notion=NotionConfig(api_key="test_key", candidates_db_id=None),
            validation=ValidationConfig(),
            logging=LoggingConfig(),
            analysis=AnalysisConfig(),
        )

        with pytest.raises(
            ValueError, match="Notion candidates database ID is required"
        ):
            validate_config(config, require_notion_db=True)

    def test_validate_without_notion_db_requirement(self):
        """Test validation passes without Notion DB when not required"""
        config = AppConfig(
            herp=HerpConfig(api_key="test_key", base_url="https://api.test.com"),
            notion=NotionConfig(api_key="test_key", candidates_db_id=None),
            validation=ValidationConfig(),
            logging=LoggingConfig(),
            analysis=AnalysisConfig(),
        )

        assert validate_config(config, require_notion_db=False) is True


class TestValidationMode:
    """Test ValidationMode enum"""

    def test_enum_values(self):
        """Test ValidationMode enum values"""
        assert ValidationMode.STRICT.value == "strict"
        assert ValidationMode.LENIENT.value == "lenient"
        assert ValidationMode.DISABLED.value == "disabled"

    def test_enum_comparison(self):
        """Test ValidationMode enum comparison"""
        mode = ValidationMode.STRICT

        assert mode == ValidationMode.STRICT
        assert mode != ValidationMode.LENIENT


class TestConfigIntegration:
    """Integration tests for configuration module"""

    @patch.dict(
        os.environ,
        {
            "HERP_API_KEY": "integration_herp_key",
            "HERP_API_BASE_URL": "https://integration.api.com",
            "HERP_RATE_LIMIT": "150",
            "NOTION_API_KEY": "integration_notion_key",
            "NOTION_CANDIDATES_DB_ID": "db_candidates_123",
            "VALIDATION_MODE": "strict",
            "LOG_LEVEL": "DEBUG",
            "USE_CLAUDE_CLI": "false",
        },
        clear=True,
    )
    def test_complete_workflow(self):
        """Test complete configuration loading and validation workflow"""
        # Load config
        config = load_config()

        # Verify all configs loaded correctly
        assert config.herp.api_key == "integration_herp_key"
        assert config.herp.base_url == "https://integration.api.com"
        assert config.herp.rate_limit == 150

        assert config.notion.api_key == "integration_notion_key"
        assert config.notion.candidates_db_id == "db_candidates_123"

        assert config.validation.mode == ValidationMode.STRICT
        assert config.logging.level == logging.DEBUG
        assert config.analysis.use_claude_cli is False

        # Validate config
        assert validate_config(config) is True

    @patch.dict(
        os.environ,
        {
            "HERP_API_KEY": "test_key",
            "NOTION_API_KEY": "test_key",
        },
        clear=True,
    )
    def test_rate_limit_calculations(self):
        """Test rate limit delay calculations for both APIs"""
        config = load_config()

        # HERP: 100 requests/minute = 0.6 seconds/request
        assert config.herp.rate_limit_delay == 0.6

        # Notion: 3 requests/second = 0.333... seconds/request
        assert abs(config.notion.rate_limit_delay - 0.3333333) < 0.0001
