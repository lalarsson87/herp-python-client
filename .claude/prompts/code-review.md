# Code Review Prompt Template

Use this template for reviewing code changes in the HERP Python Client project.

## Review Checklist

### 1. Code Quality

**Type Safety**:
- [ ] TypedDict schemas used for API responses
- [ ] Type hints on function signatures
- [ ] No `Any` types without justification
- [ ] MyPy checks pass

**Error Handling**:
- [ ] Appropriate exception types used
- [ ] Transient vs permanent errors classified correctly
- [ ] Error messages are clear and actionable
- [ ] No bare `except:` clauses

**Naming**:
- [ ] Functions/variables use descriptive names
- [ ] camelCase for API field names (matches HERP API)
- [ ] snake_case for Python code
- [ ] Constants are UPPERCASE

### 2. API Integration

**HERP API**:
- [ ] Uses correct camelCase field names
- [ ] Rate limiting respected (100 req/min)
- [ ] Retry logic for transient errors
- [ ] Proper authentication headers

**Notion API**:
- [ ] Uses Notion MCP server tools
- [ ] Rate limiting respected (3 req/sec)
- [ ] Error handling for Notion failures
- [ ] Proper data mapping

### 3. Testing

**Coverage**:
- [ ] Unit tests for new code
- [ ] Integration tests with VCR cassettes
- [ ] Edge cases covered
- [ ] Error paths tested

**Test Quality**:
- [ ] Tests are focused and clear
- [ ] No flaky tests
- [ ] Fast execution (unit: <5s)
- [ ] Meaningful assertions

### 4. Documentation

**Code Comments**:
- [ ] Docstrings for public functions
- [ ] Complex logic explained
- [ ] No obvious comments
- [ ] Type hints documented

**External Docs**:
- [ ] README updated (if needed)
- [ ] API docs updated (if needed)
- [ ] CHANGELOG.md entry
- [ ] Migration guide (if breaking change)

### 5. Performance

**Efficiency**:
- [ ] Async used for I/O-bound operations
- [ ] Batch operations for bulk work
- [ ] Caching for repeated queries
- [ ] No N+1 query patterns

**Resource Usage**:
- [ ] No memory leaks
- [ ] File handles closed
- [ ] Connections cleaned up
- [ ] No infinite loops

### 6. Security

**Sensitive Data**:
- [ ] No hardcoded tokens/credentials
- [ ] PII handled appropriately
- [ ] Secrets in `.env` only
- [ ] No sensitive data in logs

**Input Validation**:
- [ ] User input validated
- [ ] SQL injection prevention (if applicable)
- [ ] XSS prevention (if applicable)
- [ ] HMAC signature verification (webhooks)

## Review Template

```markdown
## Summary
[Brief description of changes]

## Strengths
- ✅ [What was done well]
- ✅ [Another strength]

## Issues

### Critical (Must Fix)
- ❌ [Critical issue with explanation]

### Major (Should Fix)
- ⚠️ [Important issue]

### Minor (Consider Fixing)
- 💡 [Suggestion for improvement]

## Specific Comments

### File: src/core/herp/client.py

**Line 45**: [Comment about specific code]
```python
# Current
def get_candidacy(id: str):
    return self.get(f"/v1/candidacies/{id}")

# Suggested
def get_candidacy(self, candidacy_id: str) -> Dict[str, Any]:
    """Get candidacy by ID.

    Args:
        candidacy_id: The candidacy ID

    Returns:
        Candidacy data with camelCase fields

    Raises:
        HerpNotFoundError: If candidacy doesn't exist
    """
    return self.get(f"/v1/candidacies/{candidacy_id}")
```

## Testing Recommendations
- [ ] Add test for error case
- [ ] Add integration test with VCR
- [ ] Test with actual API (optional)

## Documentation Needs
- [ ] Update README with new feature
- [ ] Add docstrings
- [ ] Update API docs

## Performance Considerations
[Any performance notes]

## Security Considerations
[Any security notes]

## Overall Assessment
**Status**: [APPROVED | CHANGES REQUESTED | NEEDS DISCUSSION]

**Reasoning**: [Why this status]

**Next Steps**:
1. [Action item]
2. [Action item]
```

## Example Review

```markdown
## Summary
Adds batch candidacy fetching with ThreadPoolExecutor for 10x performance
improvement. Includes automatic retry on transient errors.

## Strengths
- ✅ Well-structured batch implementation
- ✅ Comprehensive error handling with retry logic
- ✅ Good test coverage (12 new tests)
- ✅ Clear documentation and examples
- ✅ Performance metrics included

## Issues

### Critical (Must Fix)
*None*

### Major (Should Fix)
- ⚠️ **Type hints incomplete**: `fetch_candidacies_batch` return type should be
  `BatchResult` not `Any`
- ⚠️ **Rate limiting**: Need to respect HERP API rate limit (100 req/min) when
  using max_workers=10

### Minor (Consider Fixing)
- 💡 Consider adding progress callback parameter for long-running batches
- 💡 Could extract retry logic into a decorator for reuse

## Specific Comments

### File: src/core/herp/batch_client.py

**Line 89-95**: Good use of ThreadPoolExecutor, but consider rate limiting:

```python
# Suggested addition
from src.core.herp.rate_limiter import RateLimiter

class BatchHerpClient:
    def __init__(self, client, max_workers=10):
        self.client = client
        self.rate_limiter = RateLimiter(requests_per_minute=100)
        # ...
```

**Line 145-160**: Retry logic is solid, but could be extracted:

```python
# Could extract to decorator
@retry_on_transient(max_attempts=3)
def fetch_one(candidacy_id):
    return self.client.get_candidacy(candidacy_id)
```

### File: tests/unit/core/herp/test_batch_client.py

**Line 45**: Good test coverage, but add timeout test:

```python
def test_batch_fetch_with_timeout():
    """Ensure batch operations timeout appropriately"""
    # Test that long-running batches don't hang indefinitely
```

## Testing Recommendations
- [x] Unit tests added ✓
- [x] Integration tests with VCR ✓
- [ ] Load test with 1000+ candidates
- [ ] Test rate limiting behavior

## Documentation Needs
- [x] README updated ✓
- [x] Docstrings added ✓
- [ ] Add batch operations guide to docs/
- [ ] Update CHANGELOG.md

## Performance Considerations
Excellent performance improvement from 150s → 15s for 1000 candidates.
Consider adding metrics collection for monitoring in production.

## Security Considerations
No security issues identified. Batch client properly handles authentication
and doesn't expose credentials in logs.

## Overall Assessment
**Status**: CHANGES REQUESTED

**Reasoning**: Core implementation is excellent and well-tested. Need to add
rate limiting to prevent overwhelming the HERP API and complete type hints.
These are important but straightforward fixes.

**Next Steps**:
1. Add rate limiter integration
2. Complete type hints on all methods
3. Add batch operations guide to docs/
4. Update CHANGELOG.md
5. Re-review after changes
```

## Usage

```bash
# In Claude Code
Use the code review template from .claude/prompts/code-review.md to review
the changes in pull request #123
```

Or copy template to clipboard and paste into review.

## Notes

- Focus on important issues, not nitpicks
- Provide specific, actionable feedback
- Include code examples when suggesting changes
- Balance criticism with praise
- Consider the PR author's experience level
