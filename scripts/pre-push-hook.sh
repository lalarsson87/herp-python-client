#!/bin/bash
# Git pre-push hook
# Automatically runs pre-push checks before allowing push
#
# To install:
#   cp scripts/pre-push-hook.sh .git/hooks/pre-push
#   chmod +x .git/hooks/pre-push
#
# To bypass (not recommended):
#   git push --no-verify

echo "Running pre-push checks..."
echo ""

# Run the pre-push check script
bash scripts/pre-push-check.sh

# Capture exit code
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ Pre-push checks passed. Proceeding with push."
    exit 0
else
    echo ""
    echo "❌ Pre-push checks failed. Push aborted."
    echo ""
    echo "Fix the issues above and try again."
    echo "To bypass this check (NOT recommended): git push --no-verify"
    echo ""
    exit 1
fi
