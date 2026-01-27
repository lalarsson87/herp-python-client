#!/bin/bash
# Post-create script for dev container setup

set -e

echo "=========================================="
echo "Setting up HERP API Client Dev Environment"
echo "=========================================="
echo ""

# Install package in editable mode
echo "📦 Installing HERP client in development mode..."
pip install -e ".[dev]"
echo "✓ Package installed"
echo ""

# Set up pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
if [ -f .pre-commit-config.yaml ]; then
    pre-commit install
    echo "✓ Pre-commit hooks installed"
else
    echo "⚠️  No .pre-commit-config.yaml found, skipping"
fi
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✓ .env created from .env.example"
        echo "⚠️  Remember to configure your API keys in .env"
    else
        echo "⚠️  No .env.example found, creating empty .env"
        cat > .env <<EOF
# HERP API Configuration
HERP_API_TOKEN=your_token_here
HERP_BASE_URL=https://public-api.herp.cloud/hire/public

# Notion API Configuration (optional)
NOTION_API_TOKEN=your_notion_token_here

# Development Settings
LOG_LEVEL=DEBUG
EOF
    fi
else
    echo "✓ .env already exists"
fi
echo ""

# Run tests to verify setup
echo "🧪 Running tests to verify setup..."
if pytest tests/ -v --maxfail=1 -x; then
    echo "✓ All tests passed"
else
    echo "⚠️  Some tests failed - check configuration"
fi
echo ""

# Display helpful information
echo "=========================================="
echo "✅ Development environment ready!"
echo "=========================================="
echo ""
echo "Available commands:"
echo "  make pre-push    - Run pre-push checks"
echo "  make test        - Run test suite"
echo "  make lint        - Run linters"
echo "  make format      - Format code"
echo "  pytest tests/    - Run specific tests"
echo ""
echo "Quick start:"
echo "  1. Configure .env with your API keys"
echo "  2. Run: make test"
echo "  3. Start developing!"
echo ""
echo "Documentation:"
echo "  - README.md"
echo "  - docs/DEVELOPMENT_WORKFLOW.md"
echo "  - docs/DEVELOPMENT_LOG.md"
echo ""
