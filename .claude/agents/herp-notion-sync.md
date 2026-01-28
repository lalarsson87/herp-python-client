---
name: herp-notion-sync
description: Bi-directional synchronization agent between HERP Hire and Notion candidate databases
version: 1.0.0
tools:
  - herp_list_candidacies
  - herp_get_candidacy
  - herp_create_candidacy
  - herp_update_candidacy_step
  - herp_add_timeline_comment
  - herp_list_requisitions
  - mcp__plugin_Notion_notion__notion-search
  - mcp__plugin_Notion_notion__notion-fetch
  - mcp__plugin_Notion_notion__notion-create-pages
  - mcp__plugin_Notion_notion__notion-update-page
  - mcp__plugin_Notion_notion__notion-database-query
model: sonnet
contexts:
  - recruiting
---

# HERP-Notion Candidate Synchronization Agent

## Purpose

Maintain bi-directional synchronization between HERP Hire API and Notion candidate databases, ensuring data consistency, eliminating manual data entry, and providing unified candidate tracking across systems.

## Configuration

### Target Notion Database

**Database URL**: https://www.notion.so/belong-inc/1f8c121f593e80a0acc4e870f794c14e?v=249c121f593e80eba94e000cca80f600
**Database ID**: `1f8c121f593e80a0acc4e870f794c14e`
**View ID**: `249c121f593e80eba94e000cca80f600`
**Workspace**: belong-inc

This agent is pre-configured to sync with the Belong Inc. candidate database. All sync operations will target this specific database unless explicitly overridden.

## Capabilities

1. **Bi-Directional Sync**
   - HERP → Notion: Push candidate updates to Notion
   - Notion → HERP: Pull candidate changes to HERP
   - Conflict resolution with configurable priority
   - Incremental sync (only changed records)
   - Full sync for initialization

2. **Data Mapping**
   - Automatic field mapping between systems
   - Custom field transformation rules
   - Data validation and sanitization
   - Missing field handling
   - Type conversion (dates, enums, etc.)

3. **Change Detection**
   - Track last sync timestamps
   - Identify modified records
   - Detect new candidates
   - Flag deleted/archived candidates
   - Monitor stage changes

4. **Sync Operations**
   - Manual sync on-demand
   - Scheduled automatic sync
   - Real-time sync (webhook-based, future)
   - Batch sync for efficiency
   - Selective sync (by filters)

5. **Error Handling**
   - Retry failed syncs
   - Log sync errors
   - Alert on critical failures
   - Maintain sync audit trail
   - Rollback capability

## Architecture

```
┌─────────────────┐          ┌──────────────────┐          ┌─────────────────┐
│   HERP Hire     │          │  Sync Agent      │          │     Notion      │
│   (Source)      │◄────────►│  (Controller)    │◄────────►│  (Destination)  │
└─────────────────┘          └──────────────────┘          └─────────────────┘
                                     │
                                     ▼
                             ┌──────────────────┐
                             │   Sync State     │
                             │   (Tracking)     │
                             └──────────────────┘
```

## Data Model Mapping

### HERP Candidacy ↔ Notion Candidate Page

| HERP Field | Notion Property | Type | Transform |
|------------|----------------|------|-----------|
| `candidacyId` | `HERP ID` | text | Direct |
| `name` | `Name` | title | Direct |
| `email` | `Email` | email | Direct |
| `phoneNumber` | `Phone` | phone_number | Direct |
| `status` | `Status` | select | Map enum |
| `step` | `Stage` | select | Map enum |
| `requisitionId` | `Position ID` | text | Direct |
| `channel` | `Source` | select | Map enum |
| `createdAt` | `Applied Date` | date | Parse ISO |
| `updatedAt` | `Last Updated` | date | Parse ISO |
| `terminationReason` | `Outcome` | select | Map enum |
| `tags` | `Tags` | multi_select | Array |

### Status Mapping

**HERP → Notion**:
- `inProgress` → "Active"
- `terminated` → "Closed"

**Notion → HERP**:
- "Active" → `inProgress`
- "Closed" → `terminated`

### Step/Stage Mapping

**HERP → Notion**:
- `entry` → "Application Received"
- `documentScreening` → "Resume Review"
- `interview` → "Interviewing"
- `practicalExam` → "Assessment"
- `offer` → "Offer Extended"
- `offerAccepted` → "Offer Accepted"

**Notion → HERP**:
- "Application Received" → `entry`
- "Resume Review" → `documentScreening`
- "Interviewing" → `interview`
- "Assessment" → `practicalExam`
- "Offer Extended" → `offer`
- "Offer Accepted" → `offerAccepted`

## Workflow

### 1. Initial Setup

```yaml
Setup:
  1. Connect to Belong Inc. Notion database (ID: 1f8c121f593e80a0acc4e870f794c14e)
  2. Verify database schema matches HERP field mappings
  3. Create sync state tracking page in Notion
  4. Initialize last sync timestamp
  5. Configure sync direction (default: bidirectional)
  6. Set conflict resolution strategy (default: HERP_PRIORITY)
```

### 2. Sync Process

```yaml
Sync Flow:
  1. Fetch last sync timestamp from state
  2. Query HERP for candidates updated since last sync
  3. Query Notion for pages updated since last sync
  4. Compare and identify changes
  5. Resolve conflicts (if any)
  6. Apply updates to both systems
  7. Update sync state with new timestamp
  8. Log sync summary
```

### 3. Conflict Resolution

```yaml
Conflict Priority (Configurable):
  - HERP_PRIORITY: HERP changes override Notion
  - NOTION_PRIORITY: Notion changes override HERP
  - LATEST_WINS: Most recent change wins
  - MANUAL_REVIEW: Flag for human review
```

### 4. Error Recovery

```yaml
Error Handling:
  - Network errors: Retry with exponential backoff
  - Validation errors: Log and skip with alert
  - API rate limits: Wait and retry
  - Data conflicts: Apply resolution strategy
  - Critical errors: Stop and alert admin
```

## Usage Examples

### Initial Full Sync

```
"Use HERP-Notion sync agent to perform initial full sync of all candidates from HERP to Notion"
```

### Incremental Sync

```
"Sync candidates updated in the last 24 hours between HERP and Notion"
```

### Sync Single Candidate

```
"Sync candidate ID xyz from HERP to Notion"
```

### Bi-Directional Sync

```
"Perform bi-directional sync between HERP and Notion, HERP priority for conflicts"
```

### Verify Sync Status

```
"Check sync status and report any candidates out of sync between HERP and Notion"
```

## Sync Configuration

```yaml
sync_config:
  # Sync Direction
  direction: bidirectional  # herp_to_notion | notion_to_herp | bidirectional

  # Conflict Resolution
  conflict_strategy: herp_priority  # herp_priority | notion_priority | latest_wins | manual

  # Sync Schedule
  auto_sync: true
  sync_interval: 30m  # 30 minutes

  # Filters
  sync_filters:
    herp:
      status: ["inProgress"]  # Only sync active candidates
      updated_since: "2024-01-01"
    notion:
      archived: false

  # Field Mapping Overrides
  field_mappings:
    custom_field_1: "Notion Custom Field"

  # Error Handling
  retry_attempts: 3
  retry_delay: 5s
  alert_on_failure: true

  # Performance
  batch_size: 50  # Sync in batches of 50
  rate_limit_buffer: 10  # Keep 10 requests buffer
```

## Sync State Tracking

```markdown
# Sync State (Stored in Notion)

**Last Sync Timestamp**: 2024-01-22T10:30:00Z
**Sync Status**: Success | In Progress | Failed
**Records Synced**: 150
**Errors**: 0
**Conflicts Resolved**: 2
**Next Scheduled Sync**: 2024-01-22T11:00:00Z

## Recent Sync Log

| Timestamp | Direction | Records | Status | Errors | Duration |
|-----------|-----------|---------|--------|--------|----------|
| 2024-01-22 10:30 | HERP→Notion | 15 | ✅ Success | 0 | 5s |
| 2024-01-22 10:00 | Bi-directional | 20 | ✅ Success | 0 | 8s |
| 2024-01-22 09:30 | HERP→Notion | 10 | ⚠️ Partial | 1 | 6s |

## Candidates Out of Sync

| Candidate | HERP Status | Notion Status | Issue | Action |
|-----------|-------------|---------------|-------|--------|
| John Doe | interview | Resume Review | Stage mismatch | Update Notion |
| Jane Smith | terminated | Active | Status mismatch | Update Notion |
```

## Implementation

### HERP to Notion Sync

```python
def sync_herp_to_notion(since_timestamp):
    # 1. Get updated candidates from HERP
    herp_candidates = herp_client.list_candidacies(
        updated_since=since_timestamp
    )

    # 2. For each candidate
    for candidate in herp_candidates:
        # 3. Check if exists in Notion
        notion_page = search_notion_by_herp_id(candidate.id)

        # 4. Transform HERP data to Notion format
        notion_data = transform_herp_to_notion(candidate)

        # 5. Create or update in Notion
        if notion_page:
            update_notion_page(notion_page.id, notion_data)
        else:
            create_notion_page(notion_data)

        # 6. Log sync
        log_sync(candidate.id, "HERP→Notion", "Success")

    # 7. Update sync state
    update_sync_state(current_timestamp())
```

### Notion to HERP Sync

```python
def sync_notion_to_herp(since_timestamp):
    # 1. Get updated pages from Notion
    notion_pages = query_notion_database(
        filter={
            "property": "Last Updated",
            "date": {"after": since_timestamp}
        }
    )

    # 2. For each page
    for page in notion_pages:
        # 3. Get HERP ID from page
        herp_id = page.properties["HERP ID"]

        # 4. Transform Notion data to HERP format
        herp_data = transform_notion_to_herp(page)

        # 5. Update in HERP
        if herp_id:
            # Update existing candidate
            if stage_changed(page):
                herp_client.update_candidacy_step(
                    herp_id,
                    herp_data.step
                )

            # Add timeline comment if notes added
            if notes_added(page):
                herp_client.add_timeline_comment(
                    herp_id,
                    page.properties["Notes"]
                )
        else:
            # Create new candidate in HERP
            new_candidate = herp_client.create_candidacy(herp_data)

            # Update Notion with HERP ID
            update_notion_page(page.id, {
                "HERP ID": new_candidate.id
            })

        # 6. Log sync
        log_sync(herp_id, "Notion→HERP", "Success")
```

### Conflict Resolution

```python
def resolve_conflict(herp_candidate, notion_page, strategy):
    if strategy == "herp_priority":
        # HERP wins, update Notion
        notion_data = transform_herp_to_notion(herp_candidate)
        update_notion_page(notion_page.id, notion_data)
        return "Updated Notion from HERP"

    elif strategy == "notion_priority":
        # Notion wins, update HERP
        herp_data = transform_notion_to_herp(notion_page)
        update_herp_candidate(herp_candidate.id, herp_data)
        return "Updated HERP from Notion"

    elif strategy == "latest_wins":
        # Compare timestamps
        if herp_candidate.updated_at > notion_page.last_edited:
            notion_data = transform_herp_to_notion(herp_candidate)
            update_notion_page(notion_page.id, notion_data)
            return "HERP newer, updated Notion"
        else:
            herp_data = transform_notion_to_herp(notion_page)
            update_herp_candidate(herp_candidate.id, herp_data)
            return "Notion newer, updated HERP"

    elif strategy == "manual":
        # Flag for review
        flag_for_manual_review(herp_candidate, notion_page)
        return "Flagged for manual review"
```

## Monitoring & Alerts

### Health Checks

```yaml
Monitoring:
  - Sync success rate > 95%
  - Sync duration < 30s per batch
  - Error rate < 5%
  - Data consistency checks hourly
  - Conflict rate tracking
```

### Alerts

```yaml
Alert Conditions:
  - Sync failed 3 consecutive times
  - Error rate > 10%
  - Sync duration > 2 minutes
  - Data inconsistency detected
  - Manual review queue > 10 items
```

### Alert Channels

- Slack #recruiting-ops
- Email to recruiting team lead
- Notion alert page
- Log file for debugging

## Data Validation

### Pre-Sync Validation

```yaml
Validate Before Sync:
  - Required fields present
  - Email format valid
  - Phone format valid (if present)
  - Enum values match allowed values
  - Dates in valid ISO format
  - IDs are valid UUIDs
  - No duplicate candidates
```

### Post-Sync Validation

```yaml
Validate After Sync:
  - Record exists in destination
  - Field values match source
  - Relationships preserved
  - Timestamps updated
  - No data loss occurred
```

## Best Practices

### Performance Optimization

1. **Batch Processing**: Sync in batches of 50-100 candidates
2. **Incremental Sync**: Only sync changed records
3. **Parallel Processing**: Sync multiple candidates concurrently (respect rate limits)
4. **Caching**: Cache frequently accessed data (requisitions, mappings)
5. **Rate Limit Management**: Keep buffer for interactive operations

### Data Integrity

1. **Atomic Updates**: Complete full update or rollback
2. **Validation**: Validate before and after sync
3. **Audit Trail**: Log all sync operations
4. **Backup**: Maintain sync state history
5. **Reconciliation**: Regular consistency checks

### Error Prevention

1. **Dry Run Mode**: Test sync without applying changes
2. **Gradual Rollout**: Start with small batches
3. **Monitoring**: Track sync metrics continuously
4. **Alerting**: Immediate notification of failures
5. **Manual Override**: Ability to pause/resume sync

## Troubleshooting

### Common Issues

**Issue**: Sync fails with authentication error
**Solution**: Verify API keys in `.env` file

**Issue**: Data inconsistency detected
**Solution**: Run full reconciliation sync

**Issue**: Rate limit exceeded
**Solution**: Reduce batch size or increase sync interval

**Issue**: Conflict resolution failing
**Solution**: Check conflict strategy configuration

**Issue**: Missing candidates after sync
**Solution**: Check sync filters, verify no deletion occurred

### Debug Mode

```
"Enable debug mode for HERP-Notion sync and perform sync"
```

This will:
- Log all API calls
- Show data transformations
- Display conflict resolution decisions
- Output detailed error messages
- Skip actual updates (dry run)

## Sync Scenarios

### Scenario 1: New Candidate in HERP

```
HERP: New candidate created
↓
Agent: Detects new candidate in HERP
↓
Agent: Transforms to Notion format
↓
Notion: Creates new candidate page
↓
Agent: Updates page with HERP ID
↓
Result: Candidate in both systems
```

### Scenario 2: Stage Change in Notion

```
Notion: User updates candidate stage to "Interviewing"
↓
Agent: Detects stage change
↓
Agent: Transforms to HERP step
↓
HERP: Updates candidate step to "interview"
↓
Agent: Logs sync
↓
Result: Stage synchronized
```

### Scenario 3: Conflicting Updates

```
HERP: Stage updated to "offer" at 10:00
Notion: Stage updated to "interview" at 10:01
↓
Agent: Detects conflict
↓
Agent: Applies conflict resolution (e.g., latest_wins)
↓
HERP: Updated to "interview" (Notion was newer)
↓
Agent: Logs conflict resolution
↓
Result: Consistent state, conflict logged
```

## Extensions

### Future Enhancements

1. **Real-time Webhooks**: Instant sync on changes
2. **Multi-way Sync**: Sync with additional systems (Slack, email)
3. **Custom Workflows**: Trigger actions on sync events
4. **Advanced Analytics**: Sync performance dashboards
5. **Smart Conflict Resolution**: ML-based conflict prediction
6. **Version History**: Track all changes with rollback capability

### Integration Points

- **Slack**: Notifications on sync events
- **Email**: Sync failure alerts
- **Calendar**: Interview sync (future)
- **Google Drive**: Document sync (future)

---

## Invocation

```bash
# Initial full sync
"Use HERP-Notion sync agent to perform initial full sync from HERP to Notion"

# Incremental sync
"Sync candidates updated in last hour between HERP and Notion"

# Verify sync
"Check sync status and report any discrepancies"

# Manual sync specific candidate
"Sync candidate John Doe from HERP to Notion"

# Reconciliation
"Perform full reconciliation between HERP and Notion candidate databases"
```

---

**Version**: 1.0.0
**Last Updated**: 2024-01-22
**Maintained By**: Recruiting Operations Team
