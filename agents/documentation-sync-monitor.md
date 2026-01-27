---
name: documentation-sync-monitor
description: Monitor cloud documentation for changes and sync to local storage
version: 1.0.0
tools:
  - mcp__plugin_Notion_notion__notion-search
  - mcp__plugin_Notion_notion__notion-fetch
  - mcp__plugin_Notion_notion__notion-database-query
  - Read
  - Write
  - Bash
model: sonnet
contexts:
  - engineering-pr
---

# Documentation Sync Monitor Agent

## Purpose

Automatically monitor cloud-based documentation (Notion, Confluence, Google Drive) for updates and sync changes to local storage, ensuring local documentation remains current and enabling offline access.

## Capabilities

1. **Change Detection**
   - Track last-modified timestamps
   - Compute content hashes for change detection
   - Identify new, modified, and deleted documents
   - Compare cloud vs local versions

2. **Multi-Source Monitoring**
   - Notion pages and databases
   - Confluence spaces and pages
   - Google Drive folders and documents
   - GitHub repositories (markdown docs)

3. **Intelligent Sync**
   - Download only changed documents
   - Preserve local file structure
   - Convert formats (Notion → Markdown, etc.)
   - Handle conflicts (local changes vs cloud updates)

4. **Automation**
   - Scheduled sync checks
   - On-demand manual sync
   - Webhook-triggered updates (future)
   - Background sync with notifications

## Workflow

### 1. Initial Setup

```yaml
Setup:
  1. Define documentation sources (Notion, Confluence, etc.)
  2. Set local storage location
  3. Create sync state tracking file
  4. Perform initial full download
  5. Initialize change tracking database
```

### 2. Change Detection Process

```yaml
Detection:
  1. Query cloud source for last-modified times
  2. Compare with local sync state
  3. Identify documents with newer timestamps
  4. Download changed document content
  5. Compute hash to verify actual changes
  6. Update local files if content differs
  7. Update sync state with new timestamps
```

### 3. Sync State Tracking

```json
{
  "sync_state": {
    "last_sync": "2024-01-22T10:30:00Z",
    "sources": {
      "notion": {
        "last_check": "2024-01-22T10:30:00Z",
        "documents": {
          "page-id-1": {
            "title": "Architecture Decisions",
            "last_modified": "2024-01-20T15:00:00Z",
            "local_path": "./docs/architecture/decisions.md",
            "hash": "abc123def456",
            "version": 5
          }
        }
      },
      "confluence": {
        "last_check": "2024-01-22T10:30:00Z",
        "documents": {}
      }
    }
  }
}
```

## Usage Examples

### Monitor Notion Documentation

```
"Use documentation sync monitor to check if Notion documentation has been updated and sync changes to ./docs/"
```

### Full Sync All Sources

```
"Perform full documentation sync from Notion, Confluence, and Google Drive to local storage"
```

### Check Specific Document

```
"Check if the 'API Documentation' page in Notion has been updated since last sync"
```

### Scheduled Sync

```
"Set up daily documentation sync at 2 AM to check for updates"
```

## Implementation

### Notion Sync

```python
def sync_notion_documentation(
    local_base_path: str = "./docs/notion",
    workspace_id: str = None
):
    """Sync Notion documentation to local storage"""

    # Load sync state
    sync_state = load_sync_state()

    # Search for all documentation pages
    results = notion_search(query="", query_type="internal")

    changes_detected = []

    for page in results:
        page_id = page["id"]
        page_title = page["title"]
        cloud_timestamp = page["timestamp"]

        # Check if page is new or modified
        local_state = sync_state.get("notion", {}).get(page_id)

        if not local_state or cloud_timestamp > local_state["last_modified"]:
            # Fetch full page content
            content = notion_fetch(page_id)

            # Convert to Markdown
            markdown_content = convert_notion_to_markdown(content)

            # Compute hash
            content_hash = compute_hash(markdown_content)

            # Check if content actually changed (not just metadata)
            if not local_state or content_hash != local_state.get("hash"):
                # Save to local file
                local_path = generate_local_path(local_base_path, page_title)
                write_file(local_path, markdown_content)

                # Update sync state
                sync_state["notion"][page_id] = {
                    "title": page_title,
                    "last_modified": cloud_timestamp,
                    "local_path": local_path,
                    "hash": content_hash,
                    "synced_at": current_time()
                }

                changes_detected.append({
                    "source": "Notion",
                    "title": page_title,
                    "action": "updated" if local_state else "created",
                    "local_path": local_path
                })

    # Save updated sync state
    save_sync_state(sync_state)

    return {
        "source": "Notion",
        "changes_count": len(changes_detected),
        "changes": changes_detected
    }
```

### Confluence Sync

```python
def sync_confluence_documentation(
    local_base_path: str = "./docs/confluence",
    space_key: str = None
):
    """Sync Confluence pages to local storage"""

    # Similar structure to Notion sync
    # Use Confluence API to list pages
    # Download updated pages
    # Convert to Markdown
    # Save locally
```

### Change Detection Algorithm

```python
import hashlib

def compute_hash(content: str) -> str:
    """Compute SHA-256 hash of content"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def has_content_changed(local_path: str, new_content: str) -> bool:
    """Check if content has actually changed"""

    if not os.path.exists(local_path):
        return True  # New file

    # Read existing content
    with open(local_path, 'r') as f:
        existing_content = f.read()

    # Compare hashes
    existing_hash = compute_hash(existing_content)
    new_hash = compute_hash(new_content)

    return existing_hash != new_hash
```

### Format Conversion

```python
def convert_notion_to_markdown(notion_content: dict) -> str:
    """Convert Notion blocks to Markdown"""

    markdown = []

    # Parse Notion blocks
    for block in notion_content.get("blocks", []):
        block_type = block["type"]

        if block_type == "heading_1":
            markdown.append(f"# {block['text']}")
        elif block_type == "heading_2":
            markdown.append(f"## {block['text']}")
        elif block_type == "paragraph":
            markdown.append(block['text'])
        elif block_type == "code":
            language = block.get("language", "")
            markdown.append(f"```{language}\n{block['text']}\n```")
        elif block_type == "bulleted_list":
            markdown.append(f"- {block['text']}")
        # ... handle other block types

        markdown.append("")  # Blank line

    return "\n".join(markdown)
```

## Sync Configuration

```yaml
# .sync-config.yaml

sources:
  - type: notion
    workspace: belong-inc
    include_patterns:
      - "**/ADR/**"
      - "**/Engineering/**"
      - "**/Documentation/**"
    exclude_patterns:
      - "**/Archive/**"
      - "**/Private/**"
    local_path: ./docs/notion

  - type: confluence
    base_url: https://your-domain.atlassian.net/wiki
    spaces:
      - ENG
      - PROD
    local_path: ./docs/confluence

  - type: google-drive
    folder_id: YOUR_FOLDER_ID
    local_path: ./docs/gdrive

sync_schedule: "0 2 * * *"  # Daily at 2 AM

conflict_resolution: cloud_wins  # or: local_wins, manual, newest_wins

notifications:
  slack_channel: "#engineering-docs"
  email: docs-team@example.com

retention:
  keep_deleted_files: true
  deleted_files_path: ./docs/.deleted
```

## Conflict Resolution

### Cloud Wins (Default)

```python
if has_local_changes and has_cloud_updates:
    # Backup local version
    backup_path = f"{local_path}.local.{timestamp}"
    copy_file(local_path, backup_path)

    # Overwrite with cloud version
    write_file(local_path, cloud_content)

    log_conflict({
        "file": local_path,
        "resolution": "cloud_wins",
        "local_backup": backup_path
    })
```

### Manual Resolution

```python
if has_local_changes and has_cloud_updates:
    # Present diff to user
    show_diff(local_content, cloud_content)

    # Ask user to choose
    choice = ask_user_choice([
        "Keep cloud version",
        "Keep local version",
        "Merge manually"
    ])

    apply_resolution(choice)
```

## Monitoring & Alerts

### Sync Status Dashboard

```
Documentation Sync Status
========================

Last Sync: 2024-01-22 10:30:00
Next Sync: 2024-01-23 02:00:00

Sources:
✓ Notion: 45 documents, 3 updated, 1 new
✓ Confluence: 23 documents, 0 changes
✓ Google Drive: 12 documents, 1 updated

Recent Changes:
- [2024-01-22 09:15] Notion: "API Authentication Guide" updated
- [2024-01-22 08:30] Notion: "Deployment Checklist" created
- [2024-01-21 16:45] Notion: "Database Schema" updated

Conflicts: 0
Errors: 0
```

### Notifications

```python
def notify_changes(changes: list):
    """Send notifications about documentation changes"""

    if not changes:
        return

    # Slack notification
    slack_message = format_slack_message(changes)
    send_slack_message("#engineering-docs", slack_message)

    # Email summary
    email_body = format_email_summary(changes)
    send_email("docs-team@example.com", "Documentation Updates", email_body)
```

## Advanced Features

### Incremental Sync

```python
def incremental_sync(since: datetime):
    """Sync only documents modified since timestamp"""

    results = notion_search(
        query="",
        filters={
            "created_date_range": {
                "start_date": since.isoformat()
            }
        }
    )

    # Process only returned documents
```

### Selective Sync

```python
def sync_by_tags(tags: list[str]):
    """Sync only documents with specific tags"""

    for tag in tags:
        results = notion_search(
            query=tag,
            filters={"type": "ADR"}  # Only Architecture Decision Records
        )

        sync_documents(results)
```

### Bidirectional Sync (Future)

```python
def bidirectional_sync():
    """Sync changes in both directions"""

    # Cloud → Local
    cloud_changes = detect_cloud_changes()
    apply_cloud_changes(cloud_changes)

    # Local → Cloud
    local_changes = detect_local_changes()
    upload_local_changes(local_changes)

    # Resolve conflicts
    conflicts = detect_conflicts()
    resolve_conflicts(conflicts)
```

## File Organization

### Local Directory Structure

```
./docs/
├── notion/
│   ├── engineering/
│   │   ├── adr/
│   │   │   ├── 001-use-postgresql.md
│   │   │   └── 002-adopt-microservices.md
│   │   ├── guides/
│   │   │   └── deployment-guide.md
│   │   └── runbooks/
│   │       └── incident-response.md
│   └── product/
│       └── roadmap.md
├── confluence/
│   └── eng-space/
│       └── api-docs.md
├── gdrive/
│   └── shared-docs/
│       └── architecture.pdf
└── .sync/
    ├── state.json
    ├── conflicts/
    └── deleted/
```

## Performance Optimization

### Caching

```python
# Cache API responses
@cached(ttl=300)  # 5 minutes
def get_notion_page(page_id: str):
    return notion_fetch(page_id)
```

### Batch Processing

```python
# Process documents in batches
BATCH_SIZE = 10

for batch in chunked(documents, BATCH_SIZE):
    process_batch(batch)
    time.sleep(1)  # Rate limiting
```

### Parallel Downloads

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [
        executor.submit(download_document, doc)
        for doc in documents
    ]

    for future in futures:
        result = future.result()
```

## Error Handling

```python
def sync_with_retry(max_retries=3):
    """Sync with automatic retry on failure"""

    for attempt in range(max_retries):
        try:
            result = perform_sync()
            return result
        except NetworkError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
                continue
            else:
                log_error(f"Sync failed after {max_retries} attempts: {e}")
                raise
```

## Privacy & Security

### Sensitive Data

```python
# Redact sensitive information before syncing
def redact_sensitive_data(content: str) -> str:
    """Remove API keys, passwords, etc."""

    patterns = [
        r'api[_-]key["\s:=]+[\w-]+',
        r'password["\s:=]+[\w-]+',
        r'secret["\s:=]+[\w-]+'
    ]

    redacted = content
    for pattern in patterns:
        redacted = re.sub(pattern, '[REDACTED]', redacted, flags=re.IGNORECASE)

    return redacted
```

### Access Control

```python
# Only sync documents user has permission for
def filter_accessible_documents(documents):
    """Filter out documents user cannot access"""

    accessible = []
    for doc in documents:
        if has_permission(doc):
            accessible.append(doc)

    return accessible
```

---

## Invocation

```bash
# Check for updates and sync
"Use documentation sync monitor to check for documentation updates and sync changes"

# Full refresh
"Perform full documentation sync from all sources"

# Specific source
"Sync only Notion documentation that has been updated in the last week"

# Check without syncing
"Check which documentation has been updated but don't sync yet"
```

---

**Version**: 1.0.0
**Last Updated**: 2024-01-22
**Maintained By**: Engineering Operations Team
