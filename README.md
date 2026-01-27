# HERP-Notion Integration Project

Automated synchronization and workflow tools for HERP Hire ATS and Notion databases.

## Overview

This project automates manual work for recruiters by synchronizing candidate data between:
- **HERP Hire**: Applicant Tracking System (ATS) API
- **Notion**: Knowledge base and extended candidate tracking

**Goal**: Reduce recruiter time spent on manual data entry from **≥30% to ≤15%** of their workday.

## Project Structure

```
development/herp/
├── scripts/                    # Executable entry points
│   ├── sync-herp-notion-*.py  # Sync scripts (full, enhanced, with-reports)
│   ├── analyze-candidate-*.py # Candidate analysis tools
│   ├── find-lars-*.py         # User activity tracking
│   └── test-herp-api.py       # API testing utilities
│
├── src/                        # Source code (domain-driven design)
│   ├── domains/
│   │   ├── candidates/        # Candidate management domain
│   │   │   ├── analysis/      # Profile analysis, agent-based analysis
│   │   │   ├── reviews/       # Review generation
│   │   │   ├── evaluation/    # Candidate evaluation logic
│   │   │   └── data_quality/  # Deduplication, validation
│   │   ├── sync/              # HERP-Notion synchronization domain
│   │   │   ├── services/      # Sync implementations (full, enhanced, reports, files)
│   │   │   ├── mappers/       # Data mapping between HERP and Notion
│   │   │   └── conflict_resolution/
│   │   ├── notion/            # Notion-specific operations
│   │   │   └── pages/         # Page population, wiping
│   │   └── user_activity/     # User activity tracking and analysis
│   │       ├── search/        # Activity search and filtering
│   │       └── analysis/      # Comment collection, timeline investigation
│   │
│   ├── core/                   # Shared infrastructure
│   │   ├── herp/              # HERP API client library
│   │   ├── notion/            # Notion API client library
│   │   ├── utils/             # Utilities (logging, config, validation, retry)
│   │   ├── types/             # Shared type definitions
│   │   └── examples/          # Usage examples (logging_example.py)
│   │
│   └── cli/                    # CLI wrappers (future)
│       └── entrypoints/
│
└── tests/                      # Test suite
    ├── unit/                   # Unit tests
    ├── integration/            # Integration tests (with mocks)
    ├── e2e/                    # End-to-end tests
    └── fixtures/               # Test data and mocks
```

## Key Scripts

### Synchronization

**`sync-herp-notion-full.py`**: Full bidirectional sync
- Syncs all candidates from HERP to Notion
- Updates core properties, contacts, evaluations, timeline
- Downloads and links resume files

**`sync-herp-notion-enhanced.py`**: Enhanced sync with advanced features
- Incremental sync using `updatedSince` parameter
- Conflict detection and resolution
- Improved error handling

**`sync-herp-notion-with-reports.py`**: Sync with progress reporting
- Real-time progress updates
- Structured logging integration
- Detailed sync reports

**`sync-candidate-files.py`**: File-only synchronization
- Downloads candidate files from HERP
- Uploads to Notion and links to candidate pages

### Analysis

**`analyze-candidate-profile.py`**: AI-powered candidate profile analysis
- Extracts candidate data from HERP
- Generates AI profile scores
- Predicts engineering levels
- Evaluates "Four Pillars" (People, Product, Process, Platform)

**`analyze-candidates-with-agent.py`**: Agent-based analysis pipeline
- Multi-step analysis workflow
- Structured output generation

**`analyze-candidates-orchestrator.py`**: Batch analysis orchestration
- Processes multiple candidates
- Parallel processing capabilities

### User Activity

**`find-lars-activity.py`**: Search for specific user activity in HERP
- Searches candidacies for user contributions
- Tracks timeline comments, evaluations, assignments

**`collect-lars-comments.py`**: Collect comments from specific user
- Aggregates all comments by user
- Exports to JSON

**`investigate-timeline-authors.py`**: Analyze timeline comment patterns
- Identifies comment authors
- Tracks contribution patterns

### Utilities

**`test-herp-api.py`**: Test HERP API connectivity
- Validates API credentials
- Tests endpoint availability
- Debugging tool

## Core Libraries

### HERP Client (`src/core/herp/`)

Python client for HERP Hire API:
- Authentication and request handling
- Rate limiting (100 req/min)
- Retry logic with exponential backoff
- Structured error handling

**Key Endpoints**:
- Candidacies (list, get, create, update, terminate)
- Contacts (interviews, scheduling)
- Timeline comments
- Files (upload, download)
- Evaluations
- Assignments

### Notion Client (`src/core/notion/`)

Python client for Notion API:
- Page creation and updates
- Database queries
- Block manipulation
- Rate limiting (3 req/sec)

### Logging (`src/core/utils/logging_config.py`)

Structured logging with `structlog`:
- JSON format for production
- Console format for development
- Context binding for automatic field inclusion
- Integration with all scripts

## Configuration

**Environment Variables** (`.env`):
```bash
# HERP API
HERP_API_KEY=your-herp-api-key
HERP_API_BASE_URL=https://public-api.herp.cloud/hire/public

# Notion API
NOTION_API_KEY=your-notion-api-key
NOTION_CANDIDATES_DB_ID=your-database-id
```

**Dependencies**:
- `requirements.txt`: Production dependencies
- `requirements-dev.txt`: Development and testing dependencies

## Development

### Setup

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Install pre-commit hooks
pre-commit install
```

### Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=development/herp/src --cov-report=html

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### Code Quality

```bash
# Format code
black development/herp/src/ development/herp/tests/ development/herp/scripts/
isort development/herp/src/ development/herp/tests/ development/herp/scripts/

# Lint
flake8 development/herp/src/ development/herp/tests/ development/herp/scripts/

# Type check
mypy development/herp/src/

# Security scan
bandit -r development/herp/src/

# Run pre-commit hooks
pre-commit run --all-files
```

## CI/CD

GitHub Actions pipeline (`.github/workflows/ci.yml`):
- **Triggers**: Changes to `development/herp/**` only
- **Jobs**:
  1. Lint & Format Check (black, isort, flake8)
  2. Type Check (mypy)
  3. Security Scan (bandit, credential detection)
  4. Unit Tests (pytest, coverage)
  5. Integration Tests (mocked APIs)
  6. E2E Tests (full pipeline)
  7. Build Status

**CI/CD does NOT trigger** on changes to:
- `knowledge-base/` (documentation)
- `.scrum/` (project management)
- Other non-HERP code

## Metrics

**Outcome Metric**: Recruiter Time Saved on Manual Sync
- **Target**: ≥30% time reduction
- **Baseline**: To be measured via gemba walk (T2.2)
- **Measurement**: Follow-up time study after automation deployment

**Secondary Metrics**:
- Automation coverage: >80% of updates automated
- Sync accuracy: >95% success rate
- Sync latency: <5 minutes
- User adoption: >80% of recruiters using automation
- Recruiter NPS: >40

**See**: `.scrum/outcome-metrics.md` for detailed framework

## Documentation

**Specifications**: `knowledge-base/docs/specifications/`
- Sync service specs
- Candidate analysis specs
- API documentation

**Context**: `knowledge-base/contexts/`
- `herp-notion-mapping.md`: Complete field mapping and data structures
- `recruiting.md`: Recruiting workflows and HERP integration
- `engineering-pr.md`: Technical guidelines and best practices

**Guides**: `.scrum/`
- `gemba-walk-guide.md`: User observation methodology
- `recruiter-interview-guide.md`: Pain point discovery interviews

## Lean Experiments

**EXP-1**: Recruiter Time Study
- **Hypothesis**: Recruiters spend ≥30% time on manual sync
- **Status**: In progress (T2.2 gemba walk pending)
- **Decision**: Persevere (≥30%) / Adapt (15-29%) / Pivot (<15%)

**EXP-2**: Sustainable Velocity
- **Hypothesis**: 15-point velocity cap maintains quality + morale
- **Status**: In progress (Sprint 2)
- **Measurement**: Team health survey, velocity analysis

## Contributing

1. Follow domain-driven design principles
2. Use structured logging (not print statements)
3. Write tests for all new code
4. Update documentation
5. Run pre-commit hooks before committing
6. Ensure CI/CD pipeline passes

## License

[Add license information]

## Contact

Product Manager: [Contact info]
Team: Engineering HR

---

**Last Updated**: January 2026
**Current Sprint**: Sprint 2 - Validate & Stabilize
**Project Status**: Active development
