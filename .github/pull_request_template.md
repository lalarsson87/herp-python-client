# Pull Request

## Description

Brief description of the changes in this PR.

## Type of Change

Please select the relevant option:

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] ♻️ Code refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] ✅ Test updates

## Related Issues

Closes # (issue number)
Related to # (issue number)

## Changes Made

### Core Changes
- Change 1
- Change 2
- Change 3

### Files Modified
- `path/to/file1.py`: Description
- `path/to/file2.py`: Description

## Testing

### Test Coverage
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] E2E tests added/updated
- [ ] All tests passing locally
- [ ] Coverage maintained/improved

### Manual Testing
Describe any manual testing performed:
1. Test scenario 1
2. Test scenario 2

## Code Quality Checklist

- [ ] Code follows style guidelines (black, isort, flake8)
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated (README, CHANGELOG, docstrings)
- [ ] No new warnings or errors
- [ ] Type hints added where appropriate
- [ ] Pre-commit hooks pass
- [ ] CI/CD pipeline passes

## Design Guidelines Compliance

Per HitoHana Application Design Guideline:

- [ ] **Searchable Naming**: All names are grep-friendly
- [ ] **Transaction Management**: No external API calls within DB transactions
- [ ] **REST API Design**: Follows OpenAPI specifications (if applicable)

## Security Checklist

- [ ] No hardcoded secrets or API keys
- [ ] PII handling reviewed
- [ ] Error messages sanitized
- [ ] Dependencies reviewed for vulnerabilities
- [ ] Security scan passes (bandit)

## Performance Impact

- [ ] No significant performance degradation
- [ ] Performance improvements quantified (if applicable)
- [ ] Resource usage considered

## Documentation

- [ ] README updated (if needed)
- [ ] CHANGELOG.md updated
- [ ] Docstrings added/updated
- [ ] API documentation updated (if applicable)

## Screenshots (if applicable)

Add screenshots or logs demonstrating the changes.

## Migration Guide (for breaking changes)

If this is a breaking change, provide a migration guide:

### Before
```python
# Old code example
```

### After
```python
# New code example
```

## Deployment Notes

Any special deployment considerations:
- Environment variables to add/update
- Database migrations required
- API version changes
- Configuration changes

## Reviewer Notes

Any specific areas you'd like reviewers to focus on?

## Checklist for Reviewers

- [ ] Code quality and style
- [ ] Test coverage adequate
- [ ] Documentation complete
- [ ] Security considerations addressed
- [ ] Performance impact acceptable
- [ ] Breaking changes properly communicated

---

**By submitting this PR, I confirm that:**
- I have followed the contributing guidelines
- My code follows the project's coding standards
- I have tested my changes thoroughly
- I have updated relevant documentation
