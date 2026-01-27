# HERP API Client Development Container
# Isolated Python development environment with all dependencies

FROM python:3.12-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials
    build-essential \
    # Git for version control
    git \
    # Curl for API testing
    curl \
    # Shell utilities
    bash \
    zsh \
    vim \
    nano \
    # Process management
    procps \
    # Network utilities
    net-tools \
    iputils-ping \
    # SSL certificates
    ca-certificates \
    # For better terminal experience
    locales \
    && rm -rf /var/lib/apt/lists/*

# Set locale
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

# Set working directory
WORKDIR /workspace

# Copy requirements first for better layer caching
COPY pyproject.toml setup.py setup.cfg README.md ./
COPY src/core/__init__.py src/core/

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e ".[dev]"

# Install additional development tools
RUN pip install \
    ipython \
    ipdb \
    ptpython \
    rich \
    httpie \
    pre-commit

# Create bash history file
RUN mkdir -p /root && touch /root/.bash_history

# Set up git config
RUN git config --global --add safe.directory /workspace

# Default command
CMD ["/bin/bash"]
