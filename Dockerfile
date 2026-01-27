# HERP Development Environment
# Python 3.12 with all dependencies for HERP-Notion integration

FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements files from development/herp directory
COPY development/herp/requirements.txt development/herp/requirements-dev.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r requirements-dev.txt

# Copy project files (HERP development directory only)
COPY development/herp ./development/herp

# Create data directory for temporary files
RUN mkdir -p development/herp/data && chmod 777 development/herp/data

# Set Python path to include src directory from development/herp
ENV PYTHONPATH=/app/development/herp/src:/app/development/herp

# Set working directory to HERP project
WORKDIR /app/development/herp

# Expose port for development server (if needed)
EXPOSE 8000

# Default command: pytest
CMD ["pytest", "tests/", "-v"]
