# Development Workflow

This document outlines the required development workflow for the HERP Python Client project.

## Core Principle

**NEVER push code without local verification**

Before every push, you MUST run local tests and CI/CD simulation to catch regressions early. This prevents CI/CD failures and maintains code quality.

## Pre-Push Checklist

### Quick Check (Minimum Required)
```bash
make pre-push
```

This runs:
1. ✅ Code formatting check (black)
2. ✅ Import ordering check (isort)
3. ✅ Critical error check (flake8)
4. ✅ Type checking (mypy)
5. ✅ Full test suite
6. ✅ Multi-Python version simulation
7. ✅ Common issue detection

### Manual Steps

If you don't use the automated script, run these commands manually:

```bash
# 1. Format code
black src/ tests/ scripts/
isort src/ tests/ scripts/ --profile black

# 2. Run linters
flake8 src/ tests/ scripts/ --count --select=E9,F63,F7,F82 --show-source --statistics

# 3. Run tests
pytest tests/ -v

# 4. Verify no regressions
pytest tests/ --tb=short --maxfail=5
```

## Git Workflow

### Standard Development Flow

```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes
# ... edit files ...

# 3. Run pre-push checks
make pre-push

# 4. Commit changes
git add -A
git commit -m "feat: your commit message"

# 5. Push (only after pre-push checks pass)
git push origin feature/your-feature-name

# 6. Create pull request
gh pr create --title "Your PR Title" --body "Description"
```

### Emergency Hotfix Flow

Even for urgent fixes, ALWAYS run pre-push checks:

```bash
# 1. Create hotfix branch
git checkout -b hotfix/critical-fix

# 2. Make minimal fix
# ... edit files ...

# 3. Run pre-push checks (REQUIRED)
make pre-push

# 4. Commit and push
git add -A
git commit -m "fix: critical issue description"
git push origin hotfix/critical-fix
```

## Automated Git Hook (Optional)

To enforce pre-push checks automatically, install the git hook:

```bash
# Install pre-push hook
cp scripts/pre-push-hook.sh .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

This will automatically run `make pre-push` before every `git push`.

To bypass (NOT recommended):
```bash
git push --no-verify
```

## Common Issues and Solutions

### Issue: Black formatting fails

```bash
# Fix automatically
black src/ tests/ scripts/
```

### Issue: Import ordering fails

```bash
# Fix automatically
isort src/ tests/ scripts/ --profile black
```

### Issue: Tests fail

```bash
# Run tests with verbose output
pytest tests/ -v --tb=short

# Run specific test
pytest tests/path/to/test.py::test_function -v

# Run with debugging
pytest tests/ -v -s --pdb
```

### Issue: Type hints fail (mypy)

Type checking failures are warnings but should be addressed:

```bash
# Check specific file
mypy src/path/to/file.py --ignore-missing-imports

# Common fixes:
# - Add type hints to function signatures
# - Import types from typing module
# - Use TYPE_CHECKING for import-only types
```

### Issue: Python version compatibility

```bash
# Test specific Python version
python3.10 -m venv test_venv
source test_venv/bin/activate
pip install -e ".[dev]"
pytest tests/

# Common issues:
# - Use typing_extensions for backports (e.g., NotRequired)
# - Avoid f-string features from Python 3.12+
# - Check match/case statements (Python 3.10+)
```

## CI/CD Simulation

The pre-push script simulates CI/CD locally:

### What it checks:
1. **Code Quality**: black, isort, flake8, pylint
2. **Type Safety**: mypy type checking
3. **Test Coverage**: Full test suite on multiple Python versions
4. **Common Issues**: Debug statements, print statements, incomplete TODOs

### Expected output:
```
==========================================
Pre-Push Verification
==========================================

✓ Virtual environment activated

==========================================
1. Checking code formatting (black)
==========================================
✓ Code formatting passed

==========================================
2. Checking import ordering (isort)
==========================================
✓ Import ordering passed

==========================================
3. Checking for critical errors (flake8)
==========================================
✓ No critical errors found

==========================================
4. Checking type hints (mypy)
==========================================
Success: no issues found in 50 source files

==========================================
5. Running test suite
==========================================
132 passed, 11 skipped in 4.35s
✓ All tests passed

==========================================
6. Simulating CI/CD checks
==========================================
Testing with python3...
Python 3.14.2
✓ Tests passed on python3

==========================================
7. Checking for common issues
==========================================

==========================================
✅ All pre-push checks passed!
==========================================

Safe to push. Recommended command:
  git push origin main
```

## Continuous Integration

### GitHub Actions Workflow

The project uses GitHub Actions for CI/CD:

**Triggers**:
- Push to any branch
- Pull request creation/update

**Jobs**:
1. **Lint Code**: black, isort, flake8, pylint
2. **Validate Documentation**: Sphinx documentation build
3. **Test Python 3.10**: Full test suite on Python 3.10
4. **Test Python 3.11**: Full test suite on Python 3.11
5. **Test Python 3.12**: Full test suite on Python 3.12
6. **Build Package**: Verify package builds successfully

### Viewing CI/CD Results

```bash
# List recent workflow runs
gh run list --limit 5

# View specific run
gh run view <run-id>

# View logs for specific job
gh run view --job=<job-id> --log

# Re-run failed jobs
gh run rerun <run-id>
```

## Best Practices

### Before Starting Work

1. Pull latest changes: `git pull origin main`
2. Create feature branch: `git checkout -b feature/name`
3. Install dependencies: `make install`

### During Development

1. Run tests frequently: `pytest tests/ -v`
2. Format code as you go: `make format`
3. Check for issues: `make lint`

### Before Committing

1. Run full test suite: `make test`
2. Format code: `make format`
3. Review changes: `git diff`

### Before Pushing (REQUIRED)

1. **Run pre-push checks**: `make pre-push`
2. **Verify all checks pass**: No errors in output
3. **Only then push**: `git push origin <branch>`

### Code Review

1. **Self-review**: Review your own diff before requesting review
2. **Test coverage**: Ensure new code has tests
3. **Documentation**: Update docs for API changes
4. **Breaking changes**: Clearly mark and document

## Performance Tips

### Speed up pre-push checks

The full pre-push check can be slow. For faster iteration during development:

```bash
# Quick format + test (no multi-version check)
make format && make test

# Only run changed tests
pytest tests/path/to/changed_test.py

# Skip slow integration tests during development
pytest tests/unit/ -v
```

### When to run full pre-push

- **Always** before pushing to remote
- Before creating a pull request
- After rebasing or merging
- When working on CI/CD changes
- When changing dependencies or Python version support

## Troubleshooting

### Pre-push script fails to run

```bash
# Make sure script is executable
chmod +x scripts/pre-push-check.sh

# Run with bash explicitly
bash scripts/pre-push-check.sh

# Check for shell errors
shellcheck scripts/pre-push-check.sh
```

### Virtual environment issues

```bash
# Recreate virtual environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### CI/CD passes locally but fails remotely

Common causes:
- **Platform differences**: macOS vs Linux
- **Python version**: Different patch version
- **Dependencies**: Outdated local dependencies
- **Environment variables**: Missing in CI/CD

Solution: Check CI/CD logs and reproduce exact environment locally.

## Support

For issues with the development workflow:
1. Check this documentation
2. Review recent commits in `docs/DEVELOPMENT_LOG.md`
3. Check GitHub Actions logs
4. Contact the development team

## Updates

This workflow may be updated as the project evolves. Check git history for changes:

```bash
git log -- docs/DEVELOPMENT_WORKFLOW.md
```

---

**Remember**: The few minutes spent running pre-push checks saves hours of debugging CI/CD failures.
