# Report Sync Service Guide

## Overview

The Report Sync Service provides comprehensive HERP-to-Notion synchronization with enhanced reviewer report generation. It extends the FullSyncService with scorecard generation, interview summaries, and hiring recommendations.

---

## Quick Start

### CLI Usage

```bash
# 1. Set environment variables
export HERP_API_KEY="your-herp-api-key"
export NOTION_API_KEY="your-notion-api-key"
export NOTION_CANDIDATES_DB_ID="your-database-id"

# 2. Run sync
python3 src/cli/entrypoints/sync_herp_notion_with_reports.py
```

### Programmatic Usage

```python
from src.core.herp.client import HerpClient
from src.core.notion.client import NotionClient
from src.domains.sync.services import ReportSyncService, SyncConfig

# Initialize
herp = HerpClient(api_key="...")
notion = NotionClient(api_key="...")

service = ReportSyncService(
    herp_client=herp,
    notion_client=notion,
    candidates_db_id="...",
    config=SyncConfig(incremental=True)
)

# Sync
metrics = service.sync_all_with_reports()
```

---

## Features

### Comprehensive Scorecards

**Score Categories** (1-5 scale):
- 💻 Technical Skills
- 💬 Communication
- 🧩 Problem Solving
- 🤝 Culture Fit

**Scorecard Components**:
- Average scores per category
- Score distribution (min/max)
- Visual score bars (█░)
- Evaluation count

### Hiring Confidence

**Confidence Levels**:
- 🟢 High (≥75%): Green background
- 🟡 Medium (50-74%): Yellow background
- 🔴 Low (<50%): Default background

**Calculation**:
```
Hire Percentage = (hire_votes / total_evaluations) × 100
```

Where `hire_votes` includes both "hire" and "strong_hire" recommendations.

### Interview History

**Displayed Information**:
- Interview type with emoji (☕ Casual, 👔 Final, etc.)
- Scheduled date and status
- Recommendation badges (✅ Hire, ⭐ Strong Hire, 🤔 Maybe, ❌ No)
- Interviewer notes (truncated to 2000 chars)

**Contact Types Supported**:
- 📄 Document Screening
- ☕ Casual Interview
- 1️⃣ First Interview
- 2️⃣ Second Interview
- 3️⃣ Third Interview
- 👔 Final Interview
- 💼 Offer Discussion

---

## Configuration

### SyncConfig Options

```python
from pathlib import Path
from src.domains.sync.services import SyncConfig, ConflictResolution

config = SyncConfig(
    # State management
    sync_state_file=Path("/tmp/sync-state.json"),

    # File storage
    files_dir=Path("/tmp/candidate-files"),

    # Logging
    log_file=Path("/tmp/sync.log"),

    # Sync behavior
    incremental=True,  # Only sync updated records

    # Conflict resolution (currently not used)
    conflict_resolution=ConflictResolution.HERP_WINS
)
```

### Environment Variables

**Required**:
- `HERP_API_KEY`: HERP Hire API authentication key
- `NOTION_API_KEY`: Notion API authentication key
- `NOTION_CANDIDATES_DB_ID`: Notion database ID for candidates

**Optional**:
- `HERP_API_BASE_URL`: Override HERP API base URL (default: `https://public-api.herp.cloud/hire/v1`)

---

## Sync Modes

### Incremental Sync (Default)

Syncs only candidates updated since last sync:

```python
metrics = service.sync_all_with_reports(incremental=True)
```

**Benefits**:
- Faster execution
- Reduced API calls
- Lower rate limit impact

**State Tracking**:
- Last sync timestamp stored in state file
- Passed to HERP API as `updatedSince` parameter

### Full Sync

Syncs all candidates regardless of update time:

```python
metrics = service.sync_all_with_reports(incremental=False)
```

**Use Cases**:
- Initial setup
- Data recovery
- Notion database rebuild

---

## Metrics

### ReportMetrics Properties

```python
metrics.start_time              # Sync start timestamp
metrics.end_time                # Sync end timestamp
metrics.duration_seconds        # Total duration

# From SyncMetrics (parent)
metrics.candidates_synced       # Candidates processed
metrics.contacts_synced         # Interviews synced
metrics.evaluations_synced      # Evaluations fetched
metrics.files_synced            # Files downloaded
metrics.timeline_comments_synced # Comments synced

# Report-specific
metrics.reports_generated       # Reports embedded
metrics.scorecards_created      # Scorecards generated
metrics.interview_summaries_created # Summaries created

# Error tracking
metrics.errors                  # List of error messages
len(metrics.errors)            # Error count
```

### Metrics Output

```python
# Export to dict
metrics_dict = metrics.to_dict()

# Access properties
print(f"Duration: {metrics.duration_seconds}s")
print(f"Success rate: {metrics.candidates_synced / total * 100}%")
```

---

## Report Format

### Scorecard Block Structure

```markdown
## 📊 Candidate Evaluation Scorecard

> 🟢 Hiring Confidence: 100.0% (2/2 evaluators recommend hire)

### Evaluation Scores (1-5 scale)

💻 Technical Skills: 4.5/5.0 ████░ (from 2 evaluations)
💬 Communication: 4.5/5.0 ████░ (from 2 evaluations)
🧩 Problem Solving: 4.5/5.0 ████░ (from 2 evaluations)
🤝 Culture Fit: 4.5/5.0 ████░ (from 2 evaluations)

---
```

### Interview Summary Block Structure

```markdown
## 📝 Interview History

### 1️⃣ First Interview - 2026-01-26 (completed)

**Recommendation:** ✅ Hire

> Strong candidate with excellent communication skills.

### 👔 Final Interview - 2026-01-27 (completed)

**Recommendation:** ⭐ Strong Hire

> Outstanding technical abilities and problem-solving.
```

---

## Error Handling

### Graceful Degradation

The service continues syncing even when individual operations fail:

- **Evaluation fetch fails**: Continue without report
- **Report generation fails**: Continue to next candidate
- **File download fails**: Log error, continue sync
- **API rate limit**: Built-in delays prevent rate limit errors

### Error Logging

Errors are:
- Logged to configured log file
- Tracked in metrics.errors list
- Displayed in final summary
- Limited to first 10 in output

### Exit Codes

**CLI Entrypoint**:
- `0`: Success (no errors)
- `1`: Partial failure (some errors occurred)

---

## Advanced Usage

### Single Candidate Sync

```python
from src.domains.sync.services import ReportMetrics
from datetime import datetime, timezone

# Fetch candidate data
candidate = herp.get_candidacy("candidate-id")

# Create metrics
metrics = ReportMetrics(start_time=datetime.now(timezone.utc))

# Sync with report
success = service.sync_candidate_with_report(candidate, metrics)

if success:
    print(f"Report generated: {metrics.reports_generated > 0}")
```

### Custom Report Generation

```python
# Fetch data
contacts = herp.list_contacts("candidate-id")
evaluations = {
    eval_id: herp.get_evaluation(eval_id)
    for contact in contacts
    if (eval_id := contact.get("evaluationRequestId"))
}

# Generate scorecard
scorecard = service.generate_scorecard(contacts, evaluations)

# Create Notion blocks
blocks = []
blocks.extend(service.create_scorecard_blocks(scorecard))
blocks.extend(service.create_interview_summary_blocks(contacts, evaluations))

# Add to page
service.add_reviewer_report_to_page("page-id", contacts, evaluations)
```

### Accessing Parent Functionality

```python
# All FullSyncService methods available
metrics = service.sync_all(incremental=True)  # Standard sync without reports

# Helper methods
page = service._find_notion_page_by_herp_id("herp-123")
page_id = service._create_notion_candidate_page(candidate)
success = service._update_notion_candidate_page(page_id, candidate)
```

---

## Testing

### Running Tests

```bash
# Install dependencies
pip install pytest pytest-cov

# Run all report sync tests
pytest tests/unit/domains/sync/test_report_sync.py -v

# Run with coverage
pytest tests/unit/domains/sync/test_report_sync.py --cov=src/domains/sync/services/report_sync

# Run specific test
pytest tests/unit/domains/sync/test_report_sync.py::test_generate_scorecard_with_evaluations -v
```

### Test Categories

1. **Initialization**: Service setup and inheritance
2. **Scorecard Generation**: Score calculation and aggregation
3. **Scorecard Blocks**: Notion block formatting
4. **Interview Summaries**: Interview history formatting
5. **Report Addition**: Embedding reports in Notion
6. **Candidate Sync**: End-to-end sync with reports
7. **Full Sync**: Bulk operations
8. **Metrics**: Performance tracking

---

## Performance

### Rate Limits

**HERP API**:
- Limit: 100 requests/minute
- Delay: 0.6s between requests
- Implementation: HerpClient

**Notion API**:
- Limit: ~3 requests/second
- Delay: 0.35s between requests
- Implementation: NotionClient

### Optimization Tips

1. **Use Incremental Sync**: Reduces API calls significantly
2. **Batch Operations**: Sync during off-peak hours
3. **Monitor Metrics**: Track duration and error rates
4. **Rate Limit Awareness**: Built-in delays handle rate limits
5. **State Management**: Ensures no duplicate work

### Expected Performance

**Small Dataset** (10 candidates):
- Duration: ~30-60 seconds
- API calls: ~50-100

**Medium Dataset** (100 candidates):
- Duration: ~5-10 minutes
- API calls: ~500-1000

**Large Dataset** (1000+ candidates):
- Duration: ~1-2 hours (incremental recommended)
- API calls: ~5000-10000

---

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'notion_client'`
- **Solution**: Install dependencies: `pip install notion-client`

**Issue**: Missing environment variables
- **Solution**: Set all required env vars (see Quick Start)

**Issue**: Rate limit errors
- **Solution**: Built-in delays should prevent this; check custom configs

**Issue**: No reports generated
- **Solution**: Ensure candidates have evaluations in HERP

**Issue**: Scorecard scores all zero
- **Solution**: Check evaluation response structure matches expected format

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

metrics = service.sync_all_with_reports()
```

Check log file:
```bash
tail -f /tmp/herp-notion-reports-sync.log
```

---

## API Reference

### ReportSyncService

```python
class ReportSyncService(FullSyncService):
    """Extended sync service with report generation"""

    def __init__(
        self,
        herp_client: HerpClient,
        notion_client: NotionClient,
        candidates_db_id: str,
        config: Optional[SyncConfig] = None
    ):
        """Initialize service"""

    def generate_scorecard(
        self,
        contacts: List[Dict],
        evaluations: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """Generate scorecard from evaluations"""

    def create_scorecard_blocks(
        self,
        scorecard: Dict[str, Any]
    ) -> List[Dict]:
        """Create Notion blocks for scorecard"""

    def create_interview_summary_blocks(
        self,
        contacts: List[Dict],
        evaluations: Dict[str, Dict]
    ) -> List[Dict]:
        """Create Notion blocks for interview summaries"""

    def add_reviewer_report_to_page(
        self,
        page_id: str,
        contacts: List[Dict],
        evaluations: Dict[str, Dict]
    ) -> bool:
        """Add report to Notion page"""

    def sync_candidate_with_report(
        self,
        herp_candidate: Dict[str, Any],
        metrics: ReportMetrics
    ) -> bool:
        """Sync single candidate with report"""

    def sync_all_with_reports(
        self,
        incremental: Optional[bool] = None
    ) -> ReportMetrics:
        """Sync all candidates with reports"""
```

### ReportMetrics

```python
@dataclass
class ReportMetrics(SyncMetrics):
    """Extended metrics for report sync"""

    reports_generated: int = 0
    scorecards_created: int = 0
    interview_summaries_created: int = 0
```

---

## Best Practices

### 1. Use Incremental Sync

```python
# Good: Fast, efficient
service.sync_all_with_reports(incremental=True)

# Avoid: Slow, redundant (unless necessary)
service.sync_all_with_reports(incremental=False)
```

### 2. Monitor Metrics

```python
metrics = service.sync_all_with_reports()

if len(metrics.errors) > 0:
    logger.warning(f"{len(metrics.errors)} errors occurred")
    # Take action (alert, retry, etc.)
```

### 3. Handle Errors Gracefully

```python
try:
    metrics = service.sync_all_with_reports()
except Exception as e:
    logger.error(f"Sync failed: {e}")
    # Fallback behavior
```

### 4. Use Appropriate Config

```python
# Development
dev_config = SyncConfig(
    sync_state_file=Path("./dev-state.json"),
    log_file=Path("./dev-sync.log"),
    incremental=False
)

# Production
prod_config = SyncConfig(
    sync_state_file=Path("/var/lib/herp-sync/state.json"),
    log_file=Path("/var/log/herp-sync/sync.log"),
    incremental=True
)
```

### 5. Regular Cleanup

```python
# Clean old files periodically
if config.files_dir.exists():
    # Archive or delete files older than 30 days
    old_files = [
        f for f in config.files_dir.rglob("*")
        if f.is_file() and (time.time() - f.stat().st_mtime) > 30*24*3600
    ]
```

---

## Support

For issues, questions, or contributions:

1. Check this guide and test examples
2. Review error logs in configured log file
3. Check HERP API documentation for evaluation structure
4. Review Notion API documentation for block limits
5. Consult FullSyncService documentation for inherited functionality

---

**Version**: 1.0.0
**Last Updated**: 2026-01-25
