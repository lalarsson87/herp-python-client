# HERP-Notion Sync Skill

**Skill ID**: `herp-sync`
**Purpose**: Synchronize candidate data between HERP and Notion
**When to use**: When candidate data needs to be synced, updated, or exported

## Usage

```
/herp-sync [operation] [options]
```

**Operations**:
- `full` - Full bidirectional sync (all candidates)
- `incremental` - Sync only recent changes (last 24 hours)
- `candidate <id>` - Sync specific candidate
- `report` - Generate sync status report

**Options**:
- `--dry-run` - Preview changes without applying
- `--force` - Force sync even if no changes detected
- `--since <date>` - Sync changes since date (YYYY-MM-DD)

## What This Skill Does

1. **Fetches from HERP** - Gets candidate data via API
2. **Queries Notion** - Checks existing Notion pages
3. **Detects changes** - Compares data between systems
4. **Applies updates** - Creates/updates Notion pages
5. **Handles conflicts** - Resolves data conflicts
6. **Reports results** - Shows sync summary

## Prerequisites

**Environment variables required**:
```bash
HERP_API_TOKEN=your_herp_token
NOTION_API_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_database_id
```

**MCP server required**:
- Notion MCP server must be enabled

## Examples

### Full Sync

```bash
# Sync all candidates (dry run first)
/herp-sync full --dry-run

# Execute full sync
/herp-sync full
```

### Incremental Sync

```bash
# Sync last 24 hours
/herp-sync incremental

# Sync since specific date
/herp-sync incremental --since 2026-01-20
```

### Single Candidate

```bash
# Sync specific candidate
/herp-sync candidate cand_abc123
```

### Sync Report

```bash
# Generate sync status report
/herp-sync report
```

## Implementation

Uses scripts and agents:

**Scripts** (`scripts/`):
- `sync-herp-notion-full.py` - Full sync implementation
- `sync-candidate-files.py` - File attachment sync

**Agents** (`agents/`):
- `herp-notion-sync.md` - Sync orchestration logic

**Process**:
1. Load configuration from `.env`
2. Initialize HERP client and Notion MCP server
3. Fetch candidates from HERP (with filters)
4. Query Notion database for existing pages
5. Compare and detect changes
6. Apply updates via Notion MCP tools
7. Handle errors and conflicts
8. Generate sync report

## Data Mapping

**HERP → Notion**:
- `name` → Notion page title
- `email` → Email property
- `status` → Status select
- `step` → Hiring Stage select
- `appliedAt` → Application Date
- `timeline_comments` → Comments relation
- Files → Attachments

See `docs/herp-notion-mapping.md` for complete mapping.

## Conflict Resolution

**Strategy**: HERP is source of truth

1. **Name changes**: HERP wins
2. **Email changes**: HERP wins
3. **Status changes**: HERP wins
4. **Notes/comments**: Merge (both systems)
5. **Custom fields**: Notion wins (enrichment)

## Error Handling

**Rate limiting**:
- HERP: 100 req/min
- Notion: 3 req/sec
- Auto-throttling implemented

**Transient errors**:
- Automatic retry with exponential backoff
- Max 3 retries per operation

**Permanent errors**:
- Log error
- Continue with other records
- Report failures in summary

## Success Criteria

- ✅ All candidates synced
- ✅ No data loss
- ✅ Conflicts resolved correctly
- ✅ Files attached properly
- ✅ Timeline preserved

## Sync Report Format

```
HERP-Notion Sync Report
=======================
Sync Type: incremental
Time Range: 2026-01-26 to 2026-01-27
Duration: 45.3s

Results:
- Total candidates: 150
- Created in Notion: 12
- Updated in Notion: 38
- No changes: 100
- Errors: 0

Details:
✓ Created: cand_abc123 (Jane Doe)
✓ Updated: cand_xyz789 (Status: active → hired)
...

Performance:
- HERP API calls: 165
- Notion API calls: 52
- Rate limit hit: 0
- Avg response time: 0.3s
```

## Integration with Agents

This skill uses the HERP-Notion Sync agent:

```python
Task(
    subagent_type="general-purpose",
    prompt=f"Use herp-notion-sync agent to sync candidates updated since {date}",
    description="Sync recent candidates"
)
```

## Notes

- Always dry-run first for full syncs
- Incremental sync is safe for automation
- Monitor rate limits during large syncs
- Verify critical candidate data manually
- Keep sync logs for audit trail
