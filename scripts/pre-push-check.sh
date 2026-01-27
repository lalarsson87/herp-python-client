#!/bin/bash
# Pre-push verification script
# Run this before every push to ensure no regressions

set -e  # Exit on first error

echo "=========================================="
echo "Pre-Push Verification"
echo "=========================================="
echo ""

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ No virtual environment found (.venv or venv)"
    exit 1
fi

echo "✓ Virtual environment activated"
echo ""

# 1. Code Formatting Check
echo "=========================================="
echo "1. Checking code formatting (black)"
echo "=========================================="
black --check src/ tests/ scripts/ || {
    echo "❌ Code formatting failed. Run: black src/ tests/ scripts/"
    exit 1
}
echo "✓ Code formatting passed"
echo ""

# 2. Import Ordering Check
echo "=========================================="
echo "2. Checking import ordering (isort)"
echo "=========================================="
isort --check-only --profile black src/ tests/ scripts/ || {
    echo "❌ Import ordering failed. Run: isort src/ tests/ scripts/ --profile black"
    exit 1
}
echo "✓ Import ordering passed"
echo ""

# 3. Linting - Critical Errors
echo "=========================================="
echo "3. Checking for critical errors (flake8)"
echo "=========================================="
flake8 src/ tests/ scripts/ --count --select=E9,F63,F7,F82 --show-source --statistics || {
    echo "❌ Critical flake8 errors found"
    exit 1
}
echo "✓ No critical errors found"
echo ""

# 4. Type Checking (if mypy is available)
echo "=========================================="
echo "4. Checking type hints (mypy)"
echo "=========================================="
if command -v mypy &> /dev/null; then
    mypy src/ --ignore-missing-imports --no-strict-optional || {
        echo "⚠️  Type checking warnings found (non-blocking)"
    }
else
    echo "ℹ️  mypy not installed, skipping type checking"
fi
echo ""

# 5. Run All Tests
echo "=========================================="
echo "5. Running test suite"
echo "=========================================="
pytest tests/ -v --tb=short --maxfail=5 || {
    echo "❌ Tests failed"
    exit 1
}
echo "✓ All tests passed"
echo ""

# 6. Local CI/CD Simulation
echo "=========================================="
echo "6. Simulating CI/CD checks"
echo "=========================================="

# Test on multiple Python versions if available
for python_version in python3.10 python3.11 python3.12 python3; do
    if command -v $python_version &> /dev/null; then
        echo ""
        echo "Testing with $python_version..."
        $python_version --version

        # Create temporary venv for this Python version
        temp_venv=$(mktemp -d)
        $python_version -m venv "$temp_venv"
        source "$temp_venv/bin/activate"

        # Install dependencies
        pip install -q -e ".[dev]" || {
            echo "⚠️  Could not install dependencies for $python_version"
            deactivate
            rm -rf "$temp_venv"
            continue
        }

        # Run tests
        pytest tests/ -q --tb=line --maxfail=1 || {
            echo "❌ Tests failed on $python_version"
            deactivate
            rm -rf "$temp_venv"
            exit 1
        }

        echo "✓ Tests passed on $python_version"

        # Cleanup
        deactivate
        rm -rf "$temp_venv"

        # Re-activate original venv
        if [ -d ".venv" ]; then
            source .venv/bin/activate
        elif [ -d "venv" ]; then
            source venv/bin/activate
        fi

        # Only test one Python version by default for speed
        break
    fi
done
echo ""

# 7. Check for common issues
echo "=========================================="
echo "7. Checking for common issues"
echo "=========================================="

# Check for debug statements
if grep -r "import pdb\|breakpoint()" src/ tests/ 2>/dev/null; then
    echo "⚠️  Warning: Debug statements found (pdb/breakpoint)"
fi

# Check for TODO/FIXME without issue numbers
if grep -r "# TODO\|# FIXME" src/ tests/ 2>/dev/null | grep -v "#[0-9]"; then
    echo "ℹ️  Found TODO/FIXME comments without issue references"
fi

# Check for print statements in source code (excluding tests)
if grep -r "print(" src/ --include="*.py" | grep -v "# debug" 2>/dev/null; then
    echo "⚠️  Warning: print() statements found in source code"
fi

echo ""
echo "=========================================="
echo "✅ All pre-push checks passed!"
echo "=========================================="
echo ""
echo "Safe to push. Recommended command:"
echo "  git push origin \$(git branch --show-current)"
echo ""
