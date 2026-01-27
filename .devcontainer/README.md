# HERP API Client Development Container

This directory contains the isolated development environment configuration for the HERP Python Client.

## Quick Start

### Option 1: VS Code Dev Container (Recommended)

1. **Prerequisites:**
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
   - [VS Code](https://code.visualstudio.com/) installed
   - [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension

2. **Open in Dev Container:**
   ```bash
   # Open VS Code in the project directory
   code .

   # Or open the workspace file
   code herp-client.code-workspace
   ```

3. **Start Dev Container:**
   - Press `F1` or `Cmd+Shift+P` (macOS) / `Ctrl+Shift+P` (Windows/Linux)
   - Type: "Dev Containers: Reopen in Container"
   - Wait for container to build and start (~2-3 minutes first time)

4. **Verify Setup:**
   ```bash
   # Inside the container terminal
   make test
   ```

### Option 2: Docker Compose

```bash
# Build and start the container
docker-compose -f .devcontainer/docker-compose.yml up -d

# Access the container
docker-compose -f .devcontainer/docker-compose.yml exec app bash

# Inside container
make test
```

### Option 3: Standalone Docker

```bash
# Build the image
docker build -f .devcontainer/Dockerfile -t herp-client-dev .

# Run the container
docker run -it --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  herp-client-dev bash

# Inside container
make test
```

## What's Included

### Development Tools

- **Python 3.12** - Latest stable Python
- **pip, setuptools, wheel** - Package management
- **pytest** - Testing framework
- **black** - Code formatter
- **isort** - Import sorter
- **flake8** - Linter
- **pylint** - Advanced linter
- **mypy** - Type checker
- **ipython** - Enhanced Python REPL
- **ipdb** - Interactive debugger
- **pre-commit** - Git hooks
- **httpie** - CLI HTTP client for API testing

### System Utilities

- **git** - Version control
- **curl** - HTTP client
- **vim/nano** - Text editors
- **zsh** - Enhanced shell
- **GitHub CLI** - GitHub integration

### VS Code Extensions

Automatically installed when using Dev Container:
- Python extension pack
- Pylance (IntelliSense)
- Black formatter
- isort
- flake8/pylint
- Ruff
- GitLens
- Git Graph
- Copilot (if you have access)
- Spell checker

## Configuration Files

### `.devcontainer/devcontainer.json`
Main Dev Container configuration:
- Container settings
- VS Code extensions
- Port forwarding
- Environment variables
- Post-create commands

### `.devcontainer/Dockerfile`
Docker image definition:
- Python 3.12 slim base
- System dependencies
- Python packages
- Development tools

### `.devcontainer/docker-compose.yml`
Multi-container setup:
- Main app container
- Optional PostgreSQL (commented out)
- Optional Redis (commented out)
- Volume management

### `.devcontainer/post-create.sh`
Runs after container creation:
- Installs package in dev mode
- Sets up pre-commit hooks
- Creates .env file
- Runs initial tests
- Displays setup info

### `herp-client.code-workspace`
VS Code workspace configuration:
- Folder structure
- Python settings
- Linting configuration
- Testing setup
- Debug configurations
- Tasks (pre-push, test, format, lint)

## Features

### Isolated Environment

✅ **Complete isolation** from host system
✅ **No Python version conflicts** - Uses Python 3.12
✅ **Consistent across team** - Same environment for everyone
✅ **Clean dependencies** - Fresh environment every time
✅ **No host pollution** - No system-wide package installs

### Pre-configured Tools

✅ **Auto-format on save** - Black + isort
✅ **Live linting** - Flake8 + Pylint
✅ **Type checking** - Mypy integration
✅ **Test discovery** - Automatic test detection
✅ **Debug support** - Breakpoint debugging
✅ **Git integration** - Full Git support inside container

### Persistent Data

✅ **Bash history** - Preserved across sessions
✅ **Git config** - Maintains your Git settings
✅ **Workspace files** - All changes saved to host
✅ **Pip cache** - Faster rebuilds

## Common Tasks

### Inside Dev Container

```bash
# Run pre-push checks (REQUIRED before push)
make pre-push

# Run tests
make test
pytest tests/ -v

# Run specific test
pytest tests/unit/core/herp/test_client.py -v

# Format code
make format

# Run linters
make lint

# Interactive Python shell
ipython

# Interactive debugger
ipdb script.py

# API testing
http GET https://public-api.herp.cloud/hire/public/v1/requisitions \
  Authorization:"Bearer $HERP_API_TOKEN"
```

### VS Code Tasks (Cmd+Shift+P / Ctrl+Shift+P)

- **"Tasks: Run Task"** → "Run Pre-Push Checks"
- **"Tasks: Run Test Task"** → Runs default test task
- **"Python: Run Python File in Terminal"**
- **"Python: Debug Python File"**

### Debugging

**Debug Current Test:**
1. Open test file
2. Set breakpoint (click left of line number)
3. Press `F5` or select "Python: Debug Tests"
4. Debugger stops at breakpoint

**Debug Specific Test:**
1. Select test function name
2. Press `F5`
3. Choose "Python: Debug Specific Test"

## Environment Variables

Create `.env` file in project root:

```bash
# HERP API Configuration
HERP_API_TOKEN=your_token_here
HERP_BASE_URL=https://public-api.herp.cloud/hire/public

# Notion API Configuration (optional)
NOTION_API_TOKEN=your_notion_token_here

# Development Settings
LOG_LEVEL=DEBUG
PYTHONPATH=/workspace/src
```

The `.env` file is automatically created from `.env.example` on first container start.

## Rebuilding the Container

If you modify `Dockerfile` or `devcontainer.json`:

**VS Code:**
- `F1` → "Dev Containers: Rebuild Container"

**Docker Compose:**
```bash
docker-compose -f .devcontainer/docker-compose.yml down
docker-compose -f .devcontainer/docker-compose.yml up --build -d
```

## Troubleshooting

### Container won't start

```bash
# Check Docker is running
docker ps

# Check logs
docker-compose -f .devcontainer/docker-compose.yml logs

# Rebuild from scratch
docker-compose -f .devcontainer/docker-compose.yml down -v
docker-compose -f .devcontainer/docker-compose.yml up --build
```

### Python packages not found

```bash
# Reinstall in dev mode
pip install -e ".[dev]"

# Or rebuild container
# VS Code: F1 → "Dev Containers: Rebuild Container"
```

### Tests fail

```bash
# Check .env configuration
cat .env

# Verify API token is set
echo $HERP_API_TOKEN

# Run tests with verbose output
pytest tests/ -v --tb=short
```

### Git issues

```bash
# Add workspace as safe directory
git config --global --add safe.directory /workspace

# Check Git status
git status
```

## Advanced Usage

### Adding Database Support

Uncomment PostgreSQL section in `docker-compose.yml`:

```yaml
postgres:
  image: postgres:15-alpine
  environment:
    POSTGRES_USER: herp
    POSTGRES_PASSWORD: herp_dev_password
    POSTGRES_DB: herp_test
  volumes:
    - postgres-data:/var/lib/postgresql/data
  networks:
    - herp-dev
  ports:
    - "5432:5432"
```

Then rebuild:
```bash
docker-compose -f .devcontainer/docker-compose.yml up --build -d
```

### Adding Redis Support

Uncomment Redis section in `docker-compose.yml` and rebuild.

### Custom Python Packages

Add to `pyproject.toml` or install in container:

```bash
# Temporary (lost on rebuild)
pip install package-name

# Permanent
# Add to pyproject.toml [project.optional-dependencies]
# Then rebuild container
```

## Benefits

### For Individual Developers

- 🚀 **Fast setup** - One command to get started
- 🔒 **Isolated** - No conflicts with other projects
- 🧹 **Clean** - No clutter on host system
- 🔄 **Reproducible** - Same environment every time
- 💻 **Cross-platform** - Works on macOS, Linux, Windows

### For Teams

- 👥 **Consistency** - Everyone uses same environment
- 📦 **Self-contained** - All dependencies included
- 📝 **Documented** - Configuration as code
- 🔧 **Maintainable** - Easy to update for everyone
- 🎯 **Onboarding** - New developers productive in minutes

## Resources

- [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Python in Containers](https://code.visualstudio.com/docs/containers/quickstart-python)

## Support

For issues:
1. Check this README
2. Check `docs/DEVELOPMENT_WORKFLOW.md`
3. Check `docs/DEVELOPMENT_LOG.md`
4. Review Docker logs
5. Rebuild container from scratch
