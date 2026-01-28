# HERP Test Runner Skill

**Skill ID**: `herp-test`
**Purpose**: Run appropriate tests for HERP Python client development
**When to use**: After code changes, before commits, during debugging

## Usage

```
/herp-test [scope]
```

**Scopes**:
- `unit` - Run unit tests only (fast, ~3-4s)
- `integration` - Run integration tests (requires --integration flag)
- `all` - Run all tests
- `changed` - Run tests for changed files (smart detection)
- `coverage` - Run with coverage report

## What This Skill Does

1. **Detects context** - Identifies which files were changed
2. **Selects tests** - Runs relevant test subset
3. **Executes pytest** - With appropriate flags
4. **Reports results** - Summarizes pass/fail status
5. **Suggests fixes** - For common failures

## Examples

```bash
# Quick unit test run
/herp-test unit

# Run all tests with coverage
/herp-test coverage

# Run tests for changed files
/herp-test changed
```

## Implementation

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests (requires VCR cassettes)
pytest tests/integration/ -v --integration

# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Smart changed files
# Detect git diff and run relevant tests
git diff --name-only | grep "src/core/herp" | xargs pytest
```

## Success Criteria

- ✅ All tests pass
- ✅ No warnings or errors
- ✅ Coverage maintained or improved
- ✅ Fast execution (unit: <5s, integration: <30s)

## Failure Handling

**Common failures**:

1. **Import errors**: Missing dependencies
   - Solution: `pip install -e ".[dev]"`

2. **VCR cassette missing**: Integration test without cassette
   - Solution: Record cassette with `--vcr-record=new_episodes`

3. **Type errors**: Schema mismatch
   - Solution: Update TypedDict in `src/core/herp/schemas.py`

4. **API changes**: Real API response different from cassette
   - Solution: Re-record cassettes

## Integration with Workflow

**Pre-commit**:
```bash
make pre-push  # Includes all tests
```

**During development**:
```bash
/herp-test unit  # Fast feedback loop
```

**Before PR**:
```bash
/herp-test all
/herp-test coverage
```

## Notes

- Unit tests are FAST - run frequently
- Integration tests use VCR - no real API calls
- Coverage target: >80% for new code
- Always run pre-push checks before committing
