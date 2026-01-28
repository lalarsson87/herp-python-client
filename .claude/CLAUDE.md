# HERP Python Client - Claude Code Configuration

This file configures Claude Code for the HERP Python Client development workspace.

## Project Context

**Project**: HERP Python Client
**Purpose**: Python client library and Notion integration for the HERP Hire API
**Tech Stack**: Python 3.10+, httpx (async), requests (sync), Notion API, Docker
**Repository**: https://github.com/lalarsson87/herp-python-client

## Development Environment

**Isolated Workspace**: This project uses an isolated development container
- VS Code Dev Container (recommended)
- Docker Compose
- Local virtual environment

**Pre-Push Requirement**: ALWAYS run `make pre-push` before pushing code
- Code formatting (black)
- Import ordering (isort)
- Linting (flake8, pylint)
- Type checking (mypy)
- Full test suite
- Multi-Python version testing

## Project Overview

### Core Functionality

**HERP API Client** (`src/core/herp/`):
- Synchronous & async HTTP clients with rate limiting
- Batch operations (10x performance improvement)
- Query DSL for complex searches
- Event sourcing for audit trails
- Webhook integration with HMAC verification
- Builder patterns for API construction
- Comprehensive error handling

**Notion Integration** (`src/core/notion/`):
- Bidirectional sync with Notion workspace
- Candidate data synchronization
- Timeline comments and activity tracking
- File attachment handling

**Key Modules**:
- `client.py` - Main synchronous HERP client
- `async_client.py` - Async HERP client (10-20x faster)
- `batch_client.py` - Bulk operations client
- `query_dsl.py` - Advanced search queries
- `builders.py` - Validated API construction
- `webhooks/` - Webhook event handling
- `events/` - Event sourcing implementation

### Architecture Patterns

- **Type Safety**: TypedDict schemas for all API responses
- **Rate Limiting**: Adaptive rate limiting with backoff
- **Circuit Breaker**: Fault tolerance for external APIs
- **Caching**: Configurable caching layer
- **Observability**: Metrics collection and logging
- **Async-First**: Full async/await support

## MCP Servers Configuration

### Enabled Servers

**Notion** (plugin:Notion:notion):
- Used for: HERP-Notion candidate synchronization
- Operations: Create pages, update database rows, search, query databases
- Context: Recruiting workflow automation
- Skills using this:
  - `notion-create-task` - Create tasks in Notion
  - `notion-create-page` - Create candidate pages
  - `notion-database-query` - Query candidate database
  - `notion-find` - Find pages by title

**GitHub CLI** (via gh command):
- Used for: PR creation, issue management, CI/CD monitoring
- Operations: Create PRs, view issues, check workflow runs
- Context: Development workflow automation
- Always use for GitHub operations instead of WebFetch

### MCP Server Usage Guidelines

**For Notion Operations**:
```python
# When syncing candidates from HERP to Notion
# Use Notion MCP server tools:
# - notion-create-database-row
# - notion-database-query
# - notion-update-page
```

**For GitHub Operations**:
```bash
# Check CI/CD status
gh run list --limit 5

# View PR
gh pr view <number>

# Create PR
gh pr create --title "..." --body "..."
```

## Skills Configuration

### Active Skills

**herp-workspace-specific skills** (to be loaded via Skill tool):

1. **herp-test-runner**
   - Runs test suite before commits
   - Usage: When code changes are made to src/core/herp/
   - Automatically runs appropriate test subset

2. **herp-notion-sync**
   - Syncs candidates between HERP and Notion
   - Usage: When candidate data needs synchronization
   - Uses agents/herp-notion-sync.md instructions

3. **herp-candidate-reviewer**
   - Reviews candidate profiles and provides assessments
   - Usage: When reviewing candidacies in HERP
   - Uses agents/herp-candidate-reviewer.md instructions

4. **documentation-sync-monitor**
   - Ensures documentation stays in sync with code
   - Usage: After significant code changes
   - Uses agents/documentation-sync-monitor.md instructions

5. **recruiting-analytics-exporter**
   - Exports recruiting analytics and reports
   - Usage: When generating reports for stakeholders
   - Uses agents/recruiting-analytics-exporter.md instructions

### Global Skills (Available)

From broader context:
- `code-review:code-review` - PR code reviews
- `frontend-design:frontend-design` - UI/UX design (if web interface added)
- `claude-md-management:revise-claude-md` - Update this CLAUDE.md with learnings

## Agents

### Project-Specific Agents

**Location**: `agents/` directory

1. **HERP-Notion Sync Agent** (`agents/herp-notion-sync.md`)
   - Purpose: Bidirectional sync between HERP and Notion
   - When to use: Candidate data synchronization tasks
   - Capabilities:
     - Fetch candidates from HERP API
     - Create/update Notion database pages
     - Sync timeline comments
     - Handle file attachments
     - Conflict resolution

2. **HERP Candidate Reviewer** (`agents/herp-candidate-reviewer.md`)
   - Purpose: Automated candidate profile review
   - When to use: Reviewing new applications
   - Capabilities:
     - Evidence-based hiring assessment
     - Skill matching against job requirements
     - Experience evaluation
     - Cultural fit analysis
     - Recommendation generation

3. **Documentation Sync Monitor** (`agents/documentation-sync-monitor.md`)
   - Purpose: Keep docs in sync with code changes
   - When to use: After API changes or new features
   - Capabilities:
     - Detect code-documentation drift
     - Update API documentation
     - Verify code examples
     - Check for broken links

4. **Recruiting Analytics Exporter** (`agents/recruiting-analytics-exporter.md`)
   - Purpose: Generate recruiting metrics and reports
   - When to use: Periodic reporting or on-demand analysis
   - Capabilities:
     - Pipeline metrics (conversion rates, time-to-hire)
     - Source effectiveness analysis
     - Interviewer performance metrics
     - Diversity analytics

5. **Employee Performance Reviewer** (`agents/employee-performance-reviewer.md`)
   - Purpose: Performance review assistance
   - When to use: Performance review cycles
   - Capabilities:
     - Aggregate feedback data
     - Identify patterns and trends
     - Generate review summaries
     - Suggest development areas

### How to Use Agents

**Invoking via Task Tool**:
```python
# For candidate review
Task(
    subagent_type="general-purpose",
    prompt="Use the HERP Candidate Reviewer agent to assess candidate ID: cand_123",
    description="Review candidate application"
)

# For Notion sync
Task(
    subagent_type="general-purpose",
    prompt="Use the HERP-Notion Sync agent to sync candidates updated in last 24 hours",
    description="Sync recent candidate updates"
)
```

## Development Workflow

### Before Starting Work

1. **Pull latest changes**: `git pull origin main`
2. **Activate environment**: `source .venv/bin/activate` (or open Dev Container)
3. **Check status**: `git status`

### During Development

**For Code Changes**:
1. Create feature branch: `git checkout -b feature/description`
2. Make changes to code
3. Write/update tests
4. Run tests frequently: `pytest tests/ -v`
5. Format code: `make format`

**For API Changes**:
1. Update TypedDict schemas in `src/core/herp/schemas.py`
2. Update client methods
3. Add/update tests
4. Update documentation
5. Run integration tests with `--integration` flag

**For Notion Integration Changes**:
1. Test with actual Notion workspace if possible
2. Verify rate limiting works correctly
3. Update sync scripts in `scripts/`
4. Document changes in relevant docs

### Before Committing

**REQUIRED**:
```bash
make pre-push
```

This runs:
- ✅ Black formatting check
- ✅ isort import ordering
- ✅ flake8 critical errors
- ✅ mypy type checking
- ✅ Full test suite (132 tests)
- ✅ Multi-Python version simulation

**Manual checks**:
- [ ] All tests pass locally
- [ ] No debug statements (pdb, breakpoint)
- [ ] No print() in production code (use logger)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (for significant changes)

### Commit Message Format

Follow Conventional Commits:

```
<type>(<scope>): <subject>

<body>

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Types**:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Maintenance tasks

**Examples**:
```
feat(herp): add batch candidacy fetching with 10x performance

Implements concurrent fetching of multiple candidacies using
ThreadPoolExecutor. Includes automatic retry on transient errors
and comprehensive error handling.

Performance: 1000 candidacies in 15s vs 150s sequential.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Creating Pull Requests

**IMPORTANT**: Use GitHub CLI for PR operations

```bash
# 1. Ensure all pre-push checks pass
make pre-push

# 2. Push branch
git push origin feature/description

# 3. Create PR using gh CLI
gh pr create \
  --title "feat(herp): description" \
  --body "$(cat <<'EOF'
## Summary
- Key change 1
- Key change 2

## Test Plan
- [ ] Unit tests pass
- [ ] Integration tests pass (if applicable)
- [ ] Manual testing completed

## Documentation
- [ ] README updated (if needed)
- [ ] API docs updated (if needed)
- [ ] CHANGELOG.md updated

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"

# 4. Monitor CI/CD
gh run list --limit 3
```

### CI/CD Pipeline

**GitHub Actions** (`.github/workflows/ci.yml`):
- ✅ Lint Code (black, isort, flake8, pylint)
- ✅ Validate Documentation (markdown lint, link checking)
- ✅ Test Python 3.10
- ✅ Test Python 3.11
- ✅ Test Python 3.12
- ✅ Build Package

**Monitoring**:
```bash
# List recent runs
gh run list --limit 5

# View specific run
gh run view <run-id>

# Re-run failed jobs
gh run rerun <run-id>
```

## Code Patterns & Best Practices

### API Client Usage

**Synchronous** (for simple scripts):
```python
from src.core.herp import HerpClient
from src.core.utils.config import load_herp_config

config = load_herp_config()
client = HerpClient(config)

# Fetch candidacy
candidacy = client.candidacies.get("cand_123")
print(candidacy["name"])  # Use camelCase field names!
```

**Asynchronous** (for performance):
```python
import asyncio
from src.core.herp import AsyncHerpClient

async def main():
    async with AsyncHerpClient(config) as client:
        candidacy = await client.candidacies.get("cand_123")
        print(candidacy["name"])

asyncio.run(main())
```

**Batch Operations** (for bulk work):
```python
from src.core.herp import BatchHerpClient

batch = BatchHerpClient(client, max_workers=10)
result = batch.fetch_candidacies_batch(candidacy_ids)
print(f"Success rate: {result.success_rate:.1f}%")
```

### Builder Pattern

**ALWAYS use builders for API requests**:
```python
from src.core.herp import CandidacyBuilder, ContactBuilder

# Create candidacy
candidacy = (
    CandidacyBuilder()
    .with_name("Jane Doe")
    .with_email("jane@example.com")
    .for_requisition("req_001")
    .build()
)

# Schedule interview
interview = (
    ContactBuilder()
    .with_type("technical_interview")
    .scheduled_at("2026-02-01T10:00:00Z")
    .with_attendees(["interviewer@company.com"])
    .build()
)
```

### Error Handling

```python
from src.core.errors.exceptions import (
    HerpAPIError,
    HerpRateLimitError,
    HerpNotFoundError,
    is_transient_error
)

try:
    candidacy = client.candidacies.get("cand_123")
except HerpNotFoundError:
    logger.error("Candidacy not found")
except HerpRateLimitError as e:
    logger.warning(f"Rate limited, retry after {e.retry_after}s")
    time.sleep(e.retry_after)
except HerpAPIError as e:
    if is_transient_error(e):
        logger.warning("Transient error, retrying...")
        # Retry logic
    else:
        logger.error("Permanent error, failing")
        raise
```

### Field Naming Convention

**CRITICAL**: HERP API uses camelCase, not snake_case

```python
# ✅ CORRECT
candidacy["requisitionId"]
candidacy["appliedAt"]
candidacy["stepUpdatedAt"]

# ❌ WRONG - Will fail!
candidacy["requisition_id"]
candidacy["applied_at"]
candidacy["step_updated_at"]
```

See `src/core/herp/schemas.py` for complete field definitions.

### Testing Patterns

**Unit Tests**:
```python
import pytest
from src.core.herp import CandidacyBuilder

def test_candidacy_builder():
    candidacy = (
        CandidacyBuilder()
        .with_name("Test User")
        .with_email("test@example.com")
        .for_requisition("req_001")
        .build()
    )

    assert candidacy["name"] == "Test User"
    assert candidacy["email"] == "test@example.com"
```

**Integration Tests** (with VCR):
```python
import pytest

@pytest.mark.vcr
def test_fetch_candidacy(herp_client):
    """Test fetching candidacy with recorded API response"""
    candidacy = herp_client.candidacies.get("cand_123")
    assert candidacy["id"] == "cand_123"
    assert "name" in candidacy
```

## File Organization

### Source Code Structure

```
src/core/
├── herp/                    # HERP API client
│   ├── __init__.py         # Main exports
│   ├── client.py           # Sync client
│   ├── async_client.py     # Async client
│   ├── batch_client.py     # Batch operations
│   ├── base_client.py      # HTTP base client
│   ├── async_base_client.py # Async HTTP base client
│   ├── schemas.py          # TypedDict schemas (camelCase!)
│   ├── builders.py         # Builder patterns
│   ├── query_dsl.py        # Query DSL
│   ├── candidates.py       # Candidacies API
│   ├── contacts.py         # Contacts/Interviews API
│   ├── timeline.py         # Timeline comments API
│   ├── files.py            # File operations API
│   ├── evaluations.py      # Evaluations API
│   ├── master_data.py      # Requisitions/Users API
│   ├── assignments.py      # Team assignments API
│   ├── webhooks/           # Webhook handling
│   │   ├── handlers.py     # Event handlers
│   │   ├── server.py       # Webhook server
│   │   └── validators.py   # HMAC verification
│   └── events/             # Event sourcing
│       ├── events.py       # Event definitions
│       └── event_store.py  # Event storage
├── notion/                  # Notion integration
│   ├── client.py           # Notion client
│   └── sync.py             # HERP-Notion sync
├── cache/                   # Caching layer
├── errors/                  # Error handling
├── utils/                   # Utilities
└── observability/           # Metrics & logging
```

### Documentation Structure

```
docs/
├── WORKSPACE_SETUP.md           # Workspace setup guide
├── DEVELOPMENT_WORKFLOW.md      # Development process
├── DEVELOPMENT_LOG.md           # Session logs
├── api-audit-findings.md        # API research
├── async-operations.md          # Async guide
├── batch-operations.md          # Batch operations
├── builder-patterns.md          # Builder usage
├── event-sourcing-guide.md      # Event sourcing
├── query-dsl-guide.md           # Query DSL
├── webhooks-guide.md            # Webhooks
├── environment-variables.md     # Configuration
└── reports/                     # Project reports
```

## Common Tasks

### Adding New HERP API Endpoint

1. **Add TypedDict schema** in `src/core/herp/schemas.py`:
```python
class HerpNewResourceResponse(TypedDict):
    id: str
    name: str
    createdAt: str  # camelCase!
```

2. **Add API method** in appropriate module:
```python
from .schemas import HerpNewResourceResponse

@validate_single_response(HerpNewResourceResponse)
def get_resource(self, resource_id: str) -> Dict[str, Any]:
    """Get resource by ID"""
    return self.client.get(f"/v1/resources/{resource_id}")
```

3. **Add tests** in `tests/unit/core/herp/`:
```python
def test_get_resource(herp_client):
    resource = herp_client.resources.get("res_123")
    assert resource["id"] == "res_123"
```

4. **Update documentation** in relevant docs file

5. **Run pre-push checks**: `make pre-push`

### Adding Notion Integration Feature

1. **Update Notion client** in `src/core/notion/client.py`
2. **Use Notion MCP server** for Notion operations
3. **Add sync logic** if bidirectional sync needed
4. **Test with actual Notion workspace**
5. **Document in docs/NOTION_INTEGRATION.md**

### Debugging API Issues

**Enable debug logging**:
```bash
export LOG_LEVEL=DEBUG
python script.py
```

**Use VCR cassettes**:
```bash
# Record new cassette
pytest tests/integration/ --vcr-record=new_episodes

# Inspect cassette
cat tests/fixtures/cassettes/test_name.yaml
```

**Check API responses**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Will log all HTTP requests/responses
client = HerpClient(config)
```

## Environment Variables

Required in `.env`:
```bash
# HERP API
HERP_API_TOKEN=your_token_here
HERP_BASE_URL=https://public-api.herp.cloud/hire/public

# Notion API (optional, for Notion integration)
NOTION_API_TOKEN=your_notion_token_here
NOTION_DATABASE_ID=your_database_id_here

# Development
LOG_LEVEL=DEBUG
PYTHONPATH=./src
```

Get tokens:
- HERP: https://app.herp.cloud/settings/api
- Notion: https://www.notion.so/my-integrations

## Known Issues & Limitations

### API Quirks

**Field Sets Vary by Endpoint**:
- `GET /v1/candidacies` (LIST) returns 20 fields
- `GET /v1/candidacies/{id}` (SINGLE) returns 12 fields
- Always check schema documentation

**Pagination Issues**:
- `limit` parameter is ignored by API
- Use client-side filtering instead

**Missing Features**:
- No `status` filter in `candidacies.list()`
- `ContactsAPI.get()` not implemented (list-only)

See `README.md` for complete list.

## Performance Optimization

### Use Async for I/O-Bound Work

**10-20x faster** than sync:
```python
# Async parallel fetching
async with AsyncHerpClient(config) as client:
    tasks = [client.candidacies.get(id) for id in ids]
    results = await asyncio.gather(*tasks)
```

### Use Batch Client for Bulk Operations

**10x faster** than sequential:
```python
batch = BatchHerpClient(client, max_workers=10)
result = batch.fetch_candidacies_batch(candidacy_ids)
```

### Cache Master Data

Requisitions and users change infrequently:
```python
# Cached for 5 minutes by default
requisitions = client.master_data.list_requisitions(use_cache=True)
```

## Security

**NEVER commit**:
- `.env` files
- API tokens
- Credentials
- PII data from production

**Use .gitignore**:
- Already configured
- Verify with `git status` before commits

**Rate Limiting**:
- 100 requests/minute (HERP)
- 3 requests/second (Notion)
- Respect `x-remaining-requests` header

## Resources

### Documentation
- `README.md` - Project overview
- `docs/WORKSPACE_SETUP.md` - Setup guide
- `docs/DEVELOPMENT_WORKFLOW.md` - Workflow guide
- `docs/api-audit-findings.md` - API research

### External Resources
- [HERP API Docs](https://public-api.herp.cloud/hire/public)
- [Notion API Docs](https://developers.notion.com/)
- [GitHub CLI Docs](https://cli.github.com/manual/)

### Support
- Issues: https://github.com/lalarsson87/herp-python-client/issues
- Discussions: Use GitHub Discussions
- Documentation: Check `docs/` directory first

---

**Last Updated**: 2026-01-27
**Claude Code Version**: Latest
**Python Version**: 3.10+

**Note**: This CLAUDE.md file should be updated as the project evolves. Use the `claude-md-management:revise-claude-md` skill to update with learnings.
