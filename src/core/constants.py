"""
Configuration constants for HERP-Notion integration

Centralized configuration values for retry logic, rate limits, and timeouts.
"""

# ============================================================================
# Retry Configuration
# ============================================================================

# Default retry settings
RETRY_DEFAULT_MAX_ATTEMPTS = 3
RETRY_DEFAULT_BASE_DELAY = 1.0  # seconds

# Maximum retry delays
RETRY_MAX_DELAY = 60.0  # seconds
RETRY_MAX_TOTAL_DURATION = 300.0  # 5 minutes

# Specific retry delays for different error types
RETRY_RATE_LIMIT_BASE_DELAY = 2.0  # seconds
RETRY_NETWORK_BASE_DELAY = 0.5  # seconds
RETRY_SERVER_ERROR_BASE_DELAY = 5.0  # seconds

# ============================================================================
# Rate Limits
# ============================================================================

# HERP API rate limits
HERP_RATE_LIMIT_PER_MINUTE = 100
HERP_RATE_LIMIT_PER_SECOND = 10

# Notion API rate limits
NOTION_RATE_LIMIT_PER_SECOND = 3
NOTION_RATE_LIMIT_PER_MINUTE = 100

# ============================================================================
# Timeouts
# ============================================================================

# HTTP request timeouts
DEFAULT_REQUEST_TIMEOUT = 30.0  # seconds
UPLOAD_REQUEST_TIMEOUT = 120.0  # seconds
DOWNLOAD_REQUEST_TIMEOUT = 120.0  # seconds

# Connection timeouts
DEFAULT_CONNECT_TIMEOUT = 10.0  # seconds

# ============================================================================
# Batch Operation Settings
# ============================================================================

# Batch processing
DEFAULT_BATCH_SIZE = 10
MAX_BATCH_SIZE = 100
DEFAULT_MAX_WORKERS = 10
MAX_WORKERS = 20

# ============================================================================
# Cache Settings
# ============================================================================

# Cache TTL (Time To Live)
CACHE_DEFAULT_TTL = 300  # 5 minutes
CACHE_MASTER_DATA_TTL = 3600  # 1 hour
CACHE_MAX_SIZE = 1000  # Max number of cache entries

# ============================================================================
# Circuit Breaker Settings
# ============================================================================

# Circuit breaker thresholds
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5  # Number of failures before opening
CIRCUIT_BREAKER_SUCCESS_THRESHOLD = 2  # Successes needed to close
CIRCUIT_BREAKER_TIMEOUT = 60.0  # seconds

# ============================================================================
# Logging
# ============================================================================

# Log levels
DEFAULT_LOG_LEVEL = "INFO"
DEBUG_LOG_LEVEL = "DEBUG"

# Log formatting
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================================================
# File Paths and Directories
# ============================================================================

# Temporary directory for analysis
ANALYSIS_TEMP_DIR = "./tmp/analysis"

# Metrics export path
METRICS_EXPORT_PATH = "./tmp/metrics"

# Sync files directory
SYNC_FILES_DIR = "./tmp/sync_files"

# Sync state file
SYNC_STATE_FILE_PATH = "./tmp/sync_state.json"

# Sync log file
SYNC_LOG_FILE_PATH = "./tmp/sync.log"
