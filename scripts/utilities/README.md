# Utility Scripts

Optional utility scripts for HERP API client development. These are not part of the core workflow but can be useful for specific tasks.

## Available Utilities

### 1. extract_api_schemas.py

**Purpose**: Extract actual API response schemas from VCR cassettes

**Usage**:
```bash
python scripts/utilities/extract_api_schemas.py
```

**What it does**:
- Analyzes recorded VCR cassettes in `tests/integration/fixtures/cassettes/`
- Extracts actual field structures from API responses
- Identifies common fields vs optional fields
- Generates schema coverage report
- Helps verify TypedDict schemas match reality

**When to use**:
- After recording new VCR cassettes
- When HERP API changes and you need to update schemas
- To validate that `src/core/herp/schemas.py` matches actual API responses
- During schema migration or version upgrades

**Output**:
```
Analyzing cassettes...

CandidacySchema:
  Common fields (100%):
    - id
    - name
    - status
  Optional fields (50-99%):
    - email (85%)
    - step (70%)
    - stepUpdatedAt (65%)
  Rare fields (<50%):
    - channel (15%)
    - tags (5%)

Recommendations:
  - Mark 'email' as NotRequired (appears in 85% of samples)
  - Mark 'channel' as NotRequired (appears in 15% of samples)
```

---

### 2. obfuscate_cassettes.py

**Purpose**: Obfuscate sensitive PII in VCR cassettes before committing

**Usage**:
```bash
# Obfuscate all cassettes
python scripts/utilities/obfuscate_cassettes.py

# Obfuscate specific cassette
python scripts/utilities/obfuscate_cassettes.py tests/integration/fixtures/cassettes/get_candidacy.yaml
```

**What it does**:
- Replaces candidate names with `Candidate_XXX`
- Replaces email addresses with `candidateXXX@example.com`
- Replaces phone numbers with fake numbers
- Preserves data structure and types
- Uses consistent hashing for reproducibility

**When to use**:
- Before committing new VCR cassettes to version control
- When cassettes contain real candidate PII
- During test data preparation
- To comply with privacy regulations

**Example transformation**:
```yaml
# Before
name: "John Doe"
email: "john.doe@realcompany.com"
phone: "+81-90-1234-5678"

# After
name: "Candidate_7234"
email: "candidate7234@example.com"
phone: "+81-90-0000-7234"
```

---

### 3. check_docs.py

**Purpose**: Validate documentation quality and consistency

**Usage**:
```bash
python scripts/utilities/check_docs.py
```

**What it does**:
- Checks for broken internal links
- Validates code block syntax
- Verifies heading hierarchy
- Checks for common spelling errors (while allowing technical terms)
- Ensures consistent formatting

**When to use**:
- After updating documentation in `docs/`
- Before submitting documentation PRs
- As part of documentation review process
- To maintain documentation quality

**Output**:
```
Checking documentation...

README.md:
  ✓ No broken links
  ✓ Code blocks valid
  ✓ Heading hierarchy correct

docs/DEVELOPMENT_WORKFLOW.md:
  ⚠ Warning: Potential broken link: /docs/missing.md
  ⚠ Warning: Code block missing language: line 45

Summary:
  Files checked: 12
  Errors: 0
  Warnings: 2
```

## Integration with Core Workflow

These scripts are **not** part of the core development workflow (`make pre-push`). They are optional tools for specific scenarios.

### Core Workflow (Always Used)
- `make pre-push` - Comprehensive pre-push checks (REQUIRED)
- `make test` - Run test suite
- `make format` - Format code
- `make lint` - Run linters

### Utility Scripts (Use as Needed)
- `extract_api_schemas.py` - Schema validation
- `obfuscate_cassettes.py` - Privacy compliance
- `check_docs.py` - Documentation quality

## Dependencies

Utilities may have additional dependencies not in core requirements:

```bash
# Install utilities dependencies
pip install pyyaml  # For cassette processing
```

## Best Practices

1. **Extract schemas regularly**: After recording new cassettes
2. **Always obfuscate**: Before committing cassettes with real data
3. **Check docs periodically**: Maintain documentation quality
4. **Don't automate yet**: These are manual tools for specific needs
5. **Review output**: Utilities may flag issues that need human judgment

## Adding New Utilities

To add a new utility script:

1. Create script in `scripts/utilities/`
2. Add shebang: `#!/usr/bin/env python3`
3. Add docstring explaining purpose
4. Document usage in this README
5. Add to `.gitignore` if it generates output files
6. Test thoroughly before committing

## Future Enhancements

Potential improvements for these utilities:

- **extract_api_schemas.py**:
  - Auto-generate TypedDict definitions
  - Compare against existing schemas
  - Track schema changes over time

- **obfuscate_cassettes.py**:
  - Support for additional PII types
  - Reversible obfuscation with key file
  - Integration with pre-commit hooks

- **check_docs.py**:
  - Auto-fix common issues
  - Spell check with custom dictionary
  - Link validation against external URLs

## Support

For issues with utility scripts:
1. Check script docstrings for detailed documentation
2. Review usage examples in this README
3. Check main project documentation
4. Open issue with error details if needed

---

**Last Updated**: 2024-01-28
**Maintained By**: Development Team
