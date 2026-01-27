# Isolated Workspace Setup Guide

This guide explains how to set up the isolated development environment for the HERP Python Client.

## Why Isolated Workspace?

### Problems with Traditional Setup

❌ **Version conflicts** - Different Python versions across projects
❌ **Dependency hell** - Conflicting package versions
❌ **"Works on my machine"** - Environment inconsistencies
❌ **Slow onboarding** - Hours to configure new machines
❌ **System pollution** - Global pip installs clutter system

### Benefits of Isolated Workspace

✅ **Complete isolation** - No conflicts with other projects
✅ **Consistent environment** - Same setup across all machines
✅ **Fast onboarding** - One command to get started
✅ **Clean system** - No global package installations
✅ **Reproducible** - Works the same way every time
✅ **Cross-platform** - macOS, Linux, Windows support

## Workspace Options

We provide **three ways** to work with the HERP client:

### Option 1: VS Code Dev Container (Recommended ⭐)

**Best for:**
- VS Code users
- Teams wanting consistency
- Complex multi-service development

**Pros:**
- Automatic setup
- Pre-configured extensions
- Integrated debugging
- Full IDE features

**Cons:**
- Requires Docker Desktop
- Larger resource usage

[Jump to setup →](#option-1-vs-code-dev-container)

### Option 2: Docker Compose

**Best for:**
- CLI-focused developers
- CI/CD pipelines
- Multi-service testing

**Pros:**
- Flexible configuration
- Can add databases easily
- Good for automation

**Cons:**
- Manual tool setup
- No IDE integration

[Jump to setup →](#option-2-docker-compose)

### Option 3: Local Virtual Environment

**Best for:**
- Quick experimentation
- Lightweight development
- No Docker available

**Pros:**
- Fastest startup
- Minimal resource usage
- Simple troubleshooting

**Cons:**
- Requires Python 3.10+ installed
- Manual dependency management
- Potential version conflicts

[Jump to setup →](#option-3-local-virtual-environment)

---

## Option 1: VS Code Dev Container

### Prerequisites

1. **Install Docker Desktop:**
   - macOS: https://docs.docker.com/desktop/install/mac-install/
   - Windows: https://docs.docker.com/desktop/install/windows-install/
   - Linux: https://docs.docker.com/desktop/install/linux-install/

2. **Install VS Code:**
   - Download from: https://code.visualstudio.com/

3. **Install Remote - Containers Extension:**
   - Open VS Code
   - Press `Cmd+Shift+X` (macOS) or `Ctrl+Shift+X` (Windows/Linux)
   - Search for "Dev Containers"
   - Click "Install"

### Setup Steps

```bash
# 1. Clone repository
git clone https://github.com/lalarsson87/herp-python-client.git
cd herp-python-client

# 2. Open in VS Code
code .

# Or open workspace file
code herp-client.code-workspace
```

**In VS Code:**
1. Press `F1` or `Cmd+Shift+P` (macOS) / `Ctrl+Shift+P` (Windows/Linux)
2. Type: "Dev Containers: Reopen in Container"
3. Press Enter
4. Wait for container to build (~2-3 minutes first time)

**Container will automatically:**
- Build Python 3.12 environment
- Install all dependencies
- Set up pre-commit hooks
- Create .env file
- Run tests to verify setup
- Install VS Code extensions

### Verify Setup

When container is ready, open the integrated terminal (`` Ctrl+` ``):

```bash
# Check Python version
python --version
# Output: Python 3.12.x

# Run tests
make test
# Should show: 132 passed, 11 skipped

# Run pre-push checks
make pre-push
# Should show: ✅ All pre-push checks passed!
```

### Daily Workflow

**Opening Workspace:**
```bash
code herp-client.code-workspace
# Container automatically starts
```

**Running Commands:**
All commands run inside the isolated container:
```bash
# Pre-push checks (REQUIRED before push)
make pre-push

# Run tests
make test
pytest tests/unit/ -v

# Format code
make format

# Interactive Python
ipython
```

**Debugging:**
1. Open test file
2. Click left of line number to set breakpoint
3. Press `F5`
4. Choose "Python: Debug Tests"
5. Debugger stops at breakpoint

**Tasks:**
- `Cmd+Shift+P` → "Tasks: Run Task"
- Choose: Pre-Push Checks, Run Tests, Format Code, etc.

### Configuration

**Environment Variables:**
Edit `.env` in project root:
```bash
HERP_API_TOKEN=your_token_here
HERP_BASE_URL=https://public-api.herp.cloud/hire/public
```

**VS Code Settings:**
Workspace settings in `herp-client.code-workspace`:
- Auto-format on save
- Import sorting
- Linting enabled
- Type checking enabled

**Extensions:**
Automatically installed:
- Python, Pylance
- Black, isort
- flake8, pylint
- GitLens, Git Graph
- Spell checker

### Rebuilding Container

If you modify `.devcontainer/Dockerfile` or `devcontainer.json`:

1. Press `F1`
2. Type: "Dev Containers: Rebuild Container"
3. Press Enter
4. Wait for rebuild

### Troubleshooting

**Container won't start:**
```bash
# Check Docker is running
docker ps

# Check Docker Desktop
# Make sure it's running and has resources allocated
```

**Tests fail:**
```bash
# Check .env configuration
cat .env

# Re-run setup script
bash .devcontainer/post-create.sh
```

**Extensions not working:**
```bash
# Rebuild container
# F1 → "Dev Containers: Rebuild Container"
```

---

## Option 2: Docker Compose

### Prerequisites

1. **Install Docker:**
   - macOS/Windows: Docker Desktop
   - Linux: Docker Engine + Docker Compose

### Setup Steps

```bash
# 1. Clone repository
git clone https://github.com/lalarsson87/herp-python-client.git
cd herp-python-client

# 2. Build and start container
docker-compose -f .devcontainer/docker-compose.yml up -d

# 3. Access container
docker-compose -f .devcontainer/docker-compose.yml exec app bash
```

**Inside container:**
```bash
# Verify setup
make test

# Configure .env
vim .env  # or nano .env
```

### Daily Workflow

**Starting workspace:**
```bash
# Start container
docker-compose -f .devcontainer/docker-compose.yml up -d

# Access shell
docker-compose -f .devcontainer/docker-compose.yml exec app bash
```

**Working in container:**
```bash
# All development commands run inside container
make pre-push
make test
pytest tests/unit/ -v
ipython
```

**Stopping workspace:**
```bash
# Exit container
exit

# Stop container
docker-compose -f .devcontainer/docker-compose.yml down
```

### Adding Services

Edit `.devcontainer/docker-compose.yml` to uncomment PostgreSQL or Redis:

```yaml
postgres:
  image: postgres:15-alpine
  environment:
    POSTGRES_USER: herp
    POSTGRES_PASSWORD: herp_dev_password
    POSTGRES_DB: herp_test
  ports:
    - "5432:5432"
```

Then rebuild:
```bash
docker-compose -f .devcontainer/docker-compose.yml up --build -d
```

---

## Option 3: Local Virtual Environment

### Prerequisites

1. **Python 3.10+** installed:
   ```bash
   python3 --version
   # Should show: Python 3.10.x or higher
   ```

2. **Git** installed

### Setup Steps

```bash
# 1. Clone repository
git clone https://github.com/lalarsson87/herp-python-client.git
cd herp-python-client

# 2. Create virtual environment
python3 -m venv .venv

# 3. Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# 4. Install dependencies
pip install -e ".[dev]"

# 5. Configure environment
cp .env.example .env
vim .env  # Edit with your API keys

# 6. Set up pre-commit hooks
pre-commit install

# 7. Verify setup
make test
```

### Daily Workflow

**Starting work:**
```bash
cd herp-python-client

# Activate virtual environment
source .venv/bin/activate

# Pull latest changes
git pull origin main
```

**Running commands:**
```bash
# Pre-push checks (REQUIRED before push)
make pre-push

# Run tests
make test

# Format code
make format

# Interactive Python
ipython
```

**Ending work:**
```bash
# Deactivate virtual environment
deactivate
```

### Troubleshooting

**Import errors:**
```bash
# Reinstall in dev mode
pip install -e ".[dev]"
```

**Python version issues:**
```bash
# Check Python version
python --version

# If < 3.10, install newer Python
# macOS: brew install python@3.12
# Ubuntu: sudo apt install python3.12
# Windows: Download from python.org
```

**Package conflicts:**
```bash
# Recreate virtual environment
deactivate
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Comparison Matrix

| Feature | Dev Container | Docker Compose | Local venv |
|---------|--------------|----------------|------------|
| **Setup Time** | 2-3 min | 2-3 min | 1 min |
| **Isolation** | ✅ Complete | ✅ Complete | ⚠️ Partial |
| **IDE Integration** | ✅ Full | ❌ None | ✅ Full |
| **Resource Usage** | 🔴 High | 🟡 Medium | 🟢 Low |
| **Debugging** | ✅ Integrated | ⚠️ Manual | ✅ Integrated |
| **Multi-service** | ✅ Easy | ✅ Easy | ❌ Hard |
| **Cross-platform** | ✅ Yes | ✅ Yes | ⚠️ Varies |
| **Onboarding** | ✅ One click | ⚠️ Few commands | ⚠️ Manual setup |

## Recommended Setup by Use Case

### For Daily Development
→ **VS Code Dev Container** - Best developer experience

### For CI/CD Pipelines
→ **Docker Compose** - Consistent automation

### For Quick Testing
→ **Local venv** - Fastest iteration

### For Team Consistency
→ **VS Code Dev Container** - Everyone same environment

### For Complex Multi-Service Apps
→ **Docker Compose** - Easy service management

## Environment Variables

All setups use the same `.env` file:

```bash
# Required
HERP_API_TOKEN=your_token_here
HERP_BASE_URL=https://public-api.herp.cloud/hire/public

# Optional
NOTION_API_TOKEN=your_notion_token_here
LOG_LEVEL=DEBUG
```

Get tokens:
- HERP: https://app.herp.cloud/settings/api
- Notion: https://www.notion.so/my-integrations

## Next Steps

After setup is complete:

1. **Read Documentation:**
   - `docs/DEVELOPMENT_WORKFLOW.md` - Development process
   - `docs/DEVELOPMENT_LOG.md` - Recent changes
   - `README.md` - Project overview

2. **Configure API Keys:**
   - Edit `.env` file
   - Add HERP API token
   - Add Notion token (if using Notion integration)

3. **Run Tests:**
   ```bash
   make test
   ```

4. **Start Developing:**
   ```bash
   # Create feature branch
   git checkout -b feature/my-feature

   # Make changes
   vim src/...

   # Run pre-push checks
   make pre-push

   # Commit and push
   git commit -m "feat: ..."
   git push
   ```

## Getting Help

**Issues with setup?**
1. Check this document
2. Read `.devcontainer/README.md`
3. Review `docs/DEVELOPMENT_WORKFLOW.md`
4. Check Docker logs
5. Try rebuilding from scratch

**Common solutions:**
```bash
# Rebuild Dev Container
# F1 → "Dev Containers: Rebuild Container"

# Rebuild Docker Compose
docker-compose -f .devcontainer/docker-compose.yml down -v
docker-compose -f .devcontainer/docker-compose.yml up --build

# Recreate venv
rm -rf .venv && python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
```

## Resources

- [VS Code Dev Containers Docs](https://code.visualstudio.com/docs/devcontainers/containers)
- [Docker Documentation](https://docs.docker.com/)
- [Python Virtual Environments](https://docs.python.org/3/library/venv.html)
- [Project README](../README.md)
- [Development Workflow](DEVELOPMENT_WORKFLOW.md)

---

**Remember:** The isolated workspace ensures everyone has the same development environment, preventing "works on my machine" issues and making onboarding new team members instant.
