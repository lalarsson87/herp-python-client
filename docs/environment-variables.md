# Environment Variables

This document lists all environment variables used in the HERP-Notion integration system.

## Required Variables

### HERP API
- **`HERP_API_KEY`** (required)
  - HERP API authentication key
  - Obtain from HERP dashboard

### Notion API
- **`NOTION_API_KEY`** (required)
  - Notion API authentication key
  - Obtain from Notion integrations page

## Optional Variables

### HERP API Configuration

- **`HERP_API_BASE_URL`**
  - HERP API base URL
  - Default: `https://public-api.herp.cloud/hire`
  - Example: `https://public-api.herp.cloud/hire`

- **`HERP_RATE_LIMIT`**
  - Rate limit in requests per minute
  - Default: `100`
  - Example: `100`

### Notion API Configuration

- **`NOTION_API_VERSION`**
  - Notion API version
  - Default: `2022-06-28`
  - Example: `2022-06-28`

- **`NOTION_RATE_LIMIT`**
  - Rate limit in requests per second
  - Default: `3`
  - Example: `3`

- **`NOTION_CANDIDATES_DB_ID`**
  - Notion candidates database ID
  - Optional: Required for candidate sync operations
  - Example: `abc123def456`

- **`NOTION_INTERVIEWS_DB_ID`**
  - Notion interviews database ID
  - Optional: Required for interview tracking
  - Example: `def456ghi789`

- **`NOTION_EVALUATIONS_DB_ID`**
  - Notion evaluations database ID
  - Optional: Required for evaluation tracking
  - Example: `ghi789jkl012`

### Validation Configuration

- **`VALIDATION_MODE`**
  - Validation strictness mode
  - Options: `strict`, `lenient`, `disabled`
  - Default: `lenient`
  - **strict**: Fail on any validation error
  - **lenient**: Log warnings but continue
  - **disabled**: Skip validation entirely

- **`VALIDATION_LOG_ERRORS`**
  - Log validation errors
  - Options: `true`, `false`
  - Default: `true`

- **`VALIDATION_COLLECT_ERRORS`**
  - Collect errors for reporting
  - Options: `true`, `false`
  - Default: `false`

### Logging Configuration

- **`LOG_LEVEL`**
  - Logging level
  - Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
  - Default: `INFO`

- **`LOG_FORMAT`**
  - Log output format
  - Options: `console`, `json`
  - Default: `console`
  - **console**: Human-readable format
  - **json**: Structured JSON format (for log aggregators)

- **`LOG_FILE`**
  - Log file path (optional)
  - Default: None (logs to stdout)
  - Example: `/var/log/herp-sync.log`

### Candidate Analysis Configuration

- **`USE_CLAUDE_CLI`**
  - Use Claude CLI for AI-powered analysis
  - Options: `true`, `false`
  - Default: `true`

- **`ENABLE_GITHUB_ANALYSIS`**
  - Enable GitHub profile analysis
  - Options: `true`, `false`
  - Default: `true`

- **`ENABLE_LINKEDIN_ANALYSIS`**
  - Enable LinkedIn profile analysis
  - Options: `true`, `false`
  - Default: `false`
  - Note: Not yet implemented

- **`GENERATE_INTERVIEW_QUESTIONS`**
  - Generate interview questions from analysis
  - Options: `true`, `false`
  - Default: `true`

- **`UPDATE_NOTION`**
  - Update Notion with analysis results
  - Options: `true`, `false`
  - Default: `true`

### Path Configuration

- **`SYNC_BASE_DIR`**
  - Base directory for all sync files
  - Default: `./data`
  - Example: `/var/app/data`

- **`SYNC_FILES_DIR`**
  - Directory for candidate files
  - Default: `{SYNC_BASE_DIR}/candidate-files`
  - Example: `/var/app/data/candidate-files`

- **`SYNC_LOG_FILE`**
  - Log file path
  - Default: `{SYNC_BASE_DIR}/logs/sync.log`
  - Example: `/var/app/data/logs/sync.log`

- **`SYNC_STATE_FILE`**
  - Sync state file path
  - Default: `{SYNC_BASE_DIR}/sync-state.json`
  - Example: `/var/app/data/sync-state.json`

- **`METRICS_EXPORT_PATH`**
  - Metrics export file path
  - Default: `{SYNC_BASE_DIR}/metrics/metrics.json`
  - Example: `/var/app/data/metrics/metrics.json`

- **`ANALYSIS_TEMP_DIR`**
  - Temporary directory for analysis
  - Default: `{SYNC_BASE_DIR}/analysis`
  - Example: `/var/app/data/analysis`

## Example Configuration

### Development (.env file)

```bash
# Required
HERP_API_KEY=your-herp-api-key
NOTION_API_KEY=your-notion-api-key

# Optional - API Configuration
HERP_API_BASE_URL=https://public-api.herp.cloud/hire
HERP_RATE_LIMIT=100
NOTION_API_VERSION=2022-06-28
NOTION_RATE_LIMIT=3

# Optional - Notion Databases
NOTION_CANDIDATES_DB_ID=abc123def456
NOTION_INTERVIEWS_DB_ID=def456ghi789
NOTION_EVALUATIONS_DB_ID=ghi789jkl012

# Optional - Validation
VALIDATION_MODE=lenient
VALIDATION_LOG_ERRORS=true
VALIDATION_COLLECT_ERRORS=false

# Optional - Logging
LOG_LEVEL=INFO
LOG_FORMAT=console

# Optional - Analysis
USE_CLAUDE_CLI=true
ENABLE_GITHUB_ANALYSIS=true
ENABLE_LINKEDIN_ANALYSIS=false
GENERATE_INTERVIEW_QUESTIONS=true
UPDATE_NOTION=true

# Optional - Paths (defaults are fine for development)
SYNC_BASE_DIR=./data
```

### Production Environment

```bash
# Required
HERP_API_KEY=${SECRET_HERP_API_KEY}
NOTION_API_KEY=${SECRET_NOTION_API_KEY}

# API Configuration
HERP_API_BASE_URL=https://public-api.herp.cloud/hire
HERP_RATE_LIMIT=100
NOTION_API_VERSION=2022-06-28
NOTION_RATE_LIMIT=3

# Notion Databases
NOTION_CANDIDATES_DB_ID=${NOTION_CANDIDATES_DB}
NOTION_INTERVIEWS_DB_ID=${NOTION_INTERVIEWS_DB}
NOTION_EVALUATIONS_DB_ID=${NOTION_EVALUATIONS_DB}

# Validation (strict in production)
VALIDATION_MODE=strict
VALIDATION_LOG_ERRORS=true
VALIDATION_COLLECT_ERRORS=true

# Logging (JSON for log aggregators)
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/herp-sync/app.log

# Analysis
USE_CLAUDE_CLI=true
ENABLE_GITHUB_ANALYSIS=true
ENABLE_LINKEDIN_ANALYSIS=false
GENERATE_INTERVIEW_QUESTIONS=true
UPDATE_NOTION=true

# Paths (production)
SYNC_BASE_DIR=/var/app/data
METRICS_EXPORT_PATH=/var/app/metrics/metrics.json
```

## Usage in Code

**DO NOT** read environment variables directly with `os.getenv()`.
Always use the centralized configuration:

```python
from src.core.utils.config import load_config

# Load configuration (reads all environment variables)
config = load_config()

# Access configuration
herp_client = HerpClient(config.herp)
notion_client = NotionClient(config.notion)

# Check validation mode
if config.validation.is_strict():
    # Handle strict validation
    pass

# Access logging level
logger.setLevel(config.logging.level)

# Check analysis settings
if config.analysis.enable_github_analysis:
    # Run GitHub analysis
    pass
```

## Migration Guide

If you have code that reads environment variables directly:

### Before (BAD - Don't do this)
```python
import os

api_key = os.getenv("HERP_API_KEY")
validation_mode = os.getenv("VALIDATION_MODE", "lenient")
```

### After (GOOD - Do this)
```python
from src.core.utils.config import load_config

config = load_config()
api_key = config.herp.api_key
validation_mode = config.validation.mode
```

## Notes

- All path variables default to subdirectories under `SYNC_BASE_DIR`
- Directories are created automatically on first use
- Boolean values accept `true`/`false` (case-insensitive)
- Rate limits are enforced automatically by the client libraries
- Validation mode `strict` will fail fast on any validation error
- JSON log format is recommended for production (easier to parse)
