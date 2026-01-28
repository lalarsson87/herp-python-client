# HERP Batch Operations Skill

**Skill ID**: `herp-batch-operations`
**Purpose**: Execute bulk operations on HERP candidacies efficiently
**When to use**: Processing multiple candidates, batch updates, bulk data operations

## Usage

```
/herp-batch-operations [operation] [options]
```

**Operations**:
- `fetch` - Fetch multiple candidacies in parallel
- `update` - Batch update candidacy steps
- `comment` - Add timeline comments to multiple candidates
- `export` - Export candidacy data in bulk
- `migrate` - Migrate data between systems

## What This Skill Does

1. **Validates inputs** - Ensures candidate IDs are valid
2. **Batch processing** - Uses ThreadPoolExecutor for parallel execution
3. **Rate limiting** - Respects HERP API limits (100 req/min)
4. **Error handling** - Collects successful and failed operations
5. **Progress reporting** - Real-time progress updates
6. **Result summary** - Comprehensive success/failure report

## Implementation Patterns

### Batch Fetch Pattern

Uses `BatchHerpClient` from `src/core/herp/batch_client.py`:

```python
from src.core.herp.batch_client import BatchHerpClient
from src.core.herp.client import HerpClient

# Initialize clients
client = HerpClient(api_token=token)
batch_client = BatchHerpClient(client, max_workers=10)

# Fetch multiple candidacies
candidacy_ids = ["id1", "id2", "id3", ...]
result = batch_client.fetch_candidacies_batch(candidacy_ids)

# Process results
print(f"Success: {len(result.successful)}")
print(f"Failed: {len(result.failed)}")
print(f"Success rate: {result.success_rate:.1f}%")
```

### Batch Update Pattern

```python
# Update multiple candidacies to new step
updates = [
    {"candidacy_id": "id1", "step_id": "step_123"},
    {"candidacy_id": "id2", "step_id": "step_123"},
]

result = batch_client.update_candidacies_batch(updates)
```

### Rate Limiting Pattern

```python
from src.core.herp.async_rate_limiter import AsyncRateLimiter

# Respect HERP API rate limit
rate_limiter = AsyncRateLimiter(
    requests_per_minute=100,
    requests_per_second=2
)

# Operations automatically throttled
```

## Examples

### Fetch All Active Candidates

```bash
/herp-batch-operations fetch --status=active --limit=1000
```

This will:
1. Query HERP API for active candidacies
2. Fetch in batches of 100 (parallel workers)
3. Apply rate limiting (100 req/min)
4. Report progress every 50 candidates
5. Export results to JSON/CSV

### Update Multiple Candidates to Interview Stage

```bash
/herp-batch-operations update \
  --ids=id1,id2,id3 \
  --step="Technical Interview" \
  --comment="Advanced to technical round"
```

This will:
1. Validate all candidate IDs exist
2. Update step for each candidate
3. Add timeline comment
4. Handle partial failures gracefully
5. Report success/failure summary

### Bulk Export for Analysis

```bash
/herp-batch-operations export \
  --filter="status:active,step:Interview" \
  --format=csv \
  --output=candidates_$(date +%Y%m%d).csv
```

This will:
1. Fetch candidates matching filter
2. Extract relevant fields
3. Format as CSV with headers
4. Include contacts, evaluations, files
5. Save to file with timestamp

## Performance Considerations

### Optimal Batch Sizes

- **Fetch operations**: 50-100 per batch
- **Update operations**: 20-50 per batch
- **Complex operations**: 10-20 per batch

### Rate Limit Management

**HERP API Limits**:
- 100 requests/minute per tenant
- Monitor `x-remaining-request` header
- Implement exponential backoff

**Best Practices**:
```python
# Use adaptive rate limiting
batch_client = BatchHerpClient(
    client,
    max_workers=10,  # Parallel workers
    rate_limit=100,  # Requests per minute
    adaptive=True    # Auto-adjust based on headers
)
```

### Memory Management

For large batches (1000+ candidates):
```python
# Process in chunks
chunk_size = 100
for i in range(0, len(all_ids), chunk_size):
    chunk = all_ids[i:i+chunk_size]
    result = batch_client.fetch_candidacies_batch(chunk)
    # Process immediately, don't accumulate
    process_and_save(result)
```

## Error Handling

### Retry Strategy

```python
from src.core.retry import RetryConfig

retry_config = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2,
    jitter=True
)
```

### Partial Failure Handling

```python
result = batch_client.fetch_candidacies_batch(ids)

# Check success rate
if result.success_rate < 50:
    print(f"WARNING: High failure rate {100-result.success_rate:.1f}%")

# Retry failed items
failed_ids = [f.candidacy_id for f in result.failed]
if failed_ids:
    retry_result = batch_client.fetch_candidacies_batch(failed_ids)
```

## Integration with HERP-Notion Sync

This skill can be combined with HERP-Notion sync:

```bash
# 1. Fetch candidates in bulk
/herp-batch-operations fetch --status=active

# 2. Sync to Notion
/herp-sync incremental --batch-size=50
```

### Sync Pattern

```python
# Fetch from HERP
herp_result = batch_client.fetch_candidacies_batch(ids)

# Transform for Notion
notion_pages = [
    transform_candidacy_to_notion(c)
    for c in herp_result.successful
]

# Batch update Notion
notion_batch_client.update_pages(notion_pages)
```

## Output Formats

### JSON Output

```json
{
  "operation": "fetch",
  "total": 100,
  "successful": 98,
  "failed": 2,
  "success_rate": 98.0,
  "duration_seconds": 15.3,
  "results": [
    {
      "id": "candidacy_123",
      "name": "John Doe",
      "status": "active",
      "step": "Technical Interview"
    }
  ],
  "errors": [
    {
      "id": "candidacy_456",
      "error": "Not found",
      "code": 404
    }
  ]
}
```

### CSV Output

```csv
candidacy_id,name,email,status,step,created_at,updated_at
candidacy_123,John Doe,john@example.com,active,Technical Interview,2024-01-01,2024-01-15
candidacy_456,Jane Smith,jane@example.com,active,Phone Screen,2024-01-02,2024-01-16
```

## Success Criteria

- ✅ All operations complete within timeout
- ✅ Success rate > 95%
- ✅ No rate limit errors
- ✅ Detailed error reporting for failures
- ✅ Results exported in requested format

## Common Issues

### Rate Limit Exceeded

**Symptom**: `HerpRateLimitError: Rate limit exceeded`
**Solution**: Reduce max_workers or add delay between batches

```python
batch_client = BatchHerpClient(client, max_workers=5)  # Reduce from 10
```

### Timeout Errors

**Symptom**: Operations taking too long
**Solution**: Process in smaller chunks

```python
# Reduce batch size
chunk_size = 50  # Instead of 100
```

### Memory Issues

**Symptom**: High memory usage with large batches
**Solution**: Stream results instead of accumulating

```python
# Don't do this
all_results = []
for chunk in chunks:
    all_results.extend(batch_fetch(chunk))  # Accumulates in memory

# Do this instead
for chunk in chunks:
    result = batch_fetch(chunk)
    process_and_save(result)  # Process immediately
    del result  # Free memory
```

## Best Practices

1. **Start small**: Test with 10-20 items before scaling up
2. **Monitor metrics**: Track success rate, duration, errors
3. **Use timeouts**: Set reasonable timeouts for operations
4. **Log everything**: Maintain audit trail of all operations
5. **Validate first**: Check data before batch operations
6. **Handle failures**: Always plan for partial failures
7. **Test rollback**: Know how to undo batch operations

## Related Documentation

- `src/core/herp/batch_client.py` - BatchHerpClient implementation
- `src/core/herp/async_rate_limiter.py` - Rate limiting
- `src/core/retry.py` - Retry strategies
- `.claude/skills/herp-sync.md` - HERP-Notion synchronization
- `.claude/CLAUDE.md` - Project patterns and conventions

## Notes

- Batch operations are 10x faster than sequential for 100+ items
- Always respect rate limits to avoid IP blocking
- Monitor `x-remaining-request` header for quota
- Use VCR cassettes for testing batch operations
- Consider async operations for I/O-bound batch tasks
