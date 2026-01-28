# .claude - Claude Code Configuration

This directory contains Claude Code configuration, agents, skills, and prompts specific to the HERP Python Client project.

## Directory Structure

```
.claude/
├── README.md                    # This file
├── CLAUDE.md                    # Main project context and configuration
├── mcp-servers.json            # MCP server configuration
├── agents/                      # Agent task prompts
│   └── herp-candidate-reviewer.md
├── skills/                      # Skill definitions
│   ├── herp-test.md
│   └── herp-sync.md
└── prompts/                     # Reusable prompt templates
```

## Files Overview

### CLAUDE.md

**Main configuration file** containing:
- Project context and overview
- MCP servers setup and usage
- Skills configuration
- Development workflow
- Code patterns and best practices
- Common tasks and troubleshooting

**When to read**: First time working on project, when onboarding, for reference

### mcp-servers.json

**MCP server configuration** specifying:
- Which MCP servers to enable
- Server connection details
- Environment variables required
- Allowed operations
- Performance notes

**When to use**: Setting up Claude Code, troubleshooting MCP issues

### agents/

**Agent task prompts** - Detailed instructions for specialized agents:

- `herp-candidate-reviewer.md` - Automated candidate assessment
  - Use for: Reviewing candidate applications
  - Capabilities: Resume analysis, skill matching, scoring
  - Output: Structured assessment with recommendation

**How to invoke**:
```python
Task(
    subagent_type="general-purpose",
    prompt=open('.claude/agents/herp-candidate-reviewer.md').read() +
           "\n\nReview candidate: cand_123",
    description="Review candidate application"
)
```

### skills/

**Skill definitions** - Workflow automation:

- `herp-test.md` - Test running automation
  - Use for: Running tests after code changes
  - Commands: `/herp-test [unit|integration|all|coverage]`
  - Integration: Pre-commit workflow

- `herp-sync.md` - HERP-Notion synchronization
  - Use for: Syncing candidate data
  - Commands: `/herp-sync [full|incremental|candidate <id>|report]`
  - Integration: Data pipeline automation

**How to use**:
```bash
# In Claude Code
/herp-test unit
/herp-sync incremental
```

### prompts/

**Reusable prompt templates** (to be added):
- Code review prompts
- Documentation generation prompts
- Refactoring prompts

## Quick Reference

### For New Contributors

1. **Read first**: `.claude/CLAUDE.md`
2. **Set up MCP servers**: Configure based on `.claude/mcp-servers.json`
3. **Learn workflow**: Follow development workflow in CLAUDE.md
4. **Try a skill**: Run `/herp-test unit` to verify setup

### For Development

**Before coding**:
- Review relevant sections in CLAUDE.md
- Check if an agent can help with the task

**During coding**:
- Use `/herp-test unit` for quick feedback
- Reference code patterns in CLAUDE.md

**Before committing**:
- Run `make pre-push` (always required)
- Use skills to automate common tasks

### For Testing

```bash
# Quick unit test
/herp-test unit

# All tests with coverage
/herp-test coverage

# Specific module
pytest tests/unit/core/herp/test_client.py -v
```

### For Sync Operations

```bash
# Incremental sync (safe, fast)
/herp-sync incremental

# Full sync (use with caution)
/herp-sync full --dry-run
/herp-sync full

# Single candidate
/herp-sync candidate cand_abc123
```

### For Candidate Review

```python
# Via agent invocation
Task(
    subagent_type="general-purpose",
    prompt="Use herp-candidate-reviewer agent for cand_123",
    description="Review candidate"
)
```

## MCP Servers

### Enabled by Default

**Notion**:
- Purpose: HERP-Notion sync operations
- Commands: `notion-search`, `notion-create-page`, `notion-database-query`
- Required env: `NOTION_API_TOKEN`

**GitHub**:
- Purpose: PR/issue management, CI/CD monitoring
- Commands: `create_pull_request`, `create_issue`, `get_file_contents`
- Required env: `GITHUB_TOKEN`

### Disabled by Default

**Filesystem**:
- Purpose: Advanced file operations
- Enable only when needed (keeps context window efficient)
- Edit `.claude/mcp-servers.json` to enable

## Environment Variables

Required in `.env`:

```bash
# HERP API
HERP_API_TOKEN=your_token_here
HERP_BASE_URL=https://public-api.herp.cloud/hire/public

# Notion API (for sync operations)
NOTION_API_TOKEN=your_notion_token_here
NOTION_DATABASE_ID=your_database_id_here

# GitHub (for PR/issue operations)
GITHUB_TOKEN=your_github_token_here

# Development
LOG_LEVEL=DEBUG
PYTHONPATH=./src
```

Get tokens:
- HERP: https://app.herp.cloud/settings/api
- Notion: https://www.notion.so/my-integrations
- GitHub: https://github.com/settings/tokens

## Common Tasks

### Run Tests

```bash
make test                    # All tests
make pre-push               # Pre-push checks (REQUIRED)
pytest tests/unit/ -v       # Unit tests only
/herp-test coverage         # With coverage report
```

### Sync Data

```bash
/herp-sync incremental      # Recent changes only
/herp-sync full             # All candidates
/herp-sync report           # Sync status
```

### Review Candidates

```bash
# Use candidate reviewer agent
# See agents/herp-candidate-reviewer.md
```

### Create PR

```bash
# 1. Ensure pre-push passes
make pre-push

# 2. Push branch
git push origin feature/branch

# 3. Create PR
gh pr create --title "..." --body "..."
```

## Troubleshooting

### MCP Server Issues

**Notion not working**:
1. Check `NOTION_API_TOKEN` in `.env`
2. Verify token has database access
3. Check `.claude/mcp-servers.json` config
4. Restart Claude Code

**GitHub not working**:
1. Check `GITHUB_TOKEN` in `.env`
2. Verify token has repo access
3. Try `gh auth status` in terminal
4. Re-authenticate if needed

### Skill Not Found

**Skills not recognized**:
- Skills are documentation, not executable commands
- Reference them in prompts or use underlying tools
- Example: "Run unit tests as described in .claude/skills/herp-test.md"

### Agent Not Working

**Agent invocation failing**:
- Use Task tool with agent content
- Provide sufficient context
- Check agent file exists and is readable
- Verify agent has required MCP servers enabled

## Best Practices

### MCP Server Management

✅ **DO**:
- Enable only needed servers (<10 total)
- Use `alwaysAllow` for frequent operations
- Set environment variables in `.env`
- Monitor context window usage

❌ **DON'T**:
- Enable all servers at once
- Hard-code tokens in config files
- Leave unused servers enabled
- Ignore performance warnings

### Agent Usage

✅ **DO**:
- Read agent instructions fully
- Provide clear context
- Review agent output before using
- Update agents based on learnings

❌ **DON'T**:
- Use agents for tasks they're not designed for
- Blindly trust agent output
- Skip human review for critical decisions
- Forget to provide required data

### Skill Development

✅ **DO**:
- Document skill purpose clearly
- Provide usage examples
- Specify success criteria
- Include error handling

❌ **DON'T**:
- Make skills too complex
- Duplicate existing functionality
- Skip testing
- Forget to update documentation

## Updating Configuration

### When to Update CLAUDE.md

- After major feature additions
- When workflow changes
- After discovering issues or patterns
- When adding new integrations
- At project milestones

### How to Update

```bash
# Use the skill
/revise-claude-md

# Or manually
vim .claude/CLAUDE.md
git add .claude/CLAUDE.md
git commit -m "docs: update CLAUDE.md with [change]"
```

### Version Control

- **Always commit** `.claude/` changes
- **Document changes** in commit messages
- **Review before merging** to main
- **Share updates** with team

## Resources

### Documentation

- Main config: `.claude/CLAUDE.md`
- Project README: `../README.md`
- Workspace setup: `../docs/WORKSPACE_SETUP.md`
- Dev workflow: `../docs/DEVELOPMENT_WORKFLOW.md`

### External Resources

- [Claude Code Docs](https://docs.anthropic.com/claude/docs/claude-code)
- [MCP Documentation](https://modelcontextprotocol.io/)
- [HERP API Docs](https://public-api.herp.cloud/hire/public)
- [Notion API Docs](https://developers.notion.com/)

### Getting Help

1. Check `.claude/CLAUDE.md` first
2. Review skill documentation
3. Check project `docs/` folder
4. GitHub issues for bugs
5. Team discussion for questions

---

**Last Updated**: 2026-01-27
**Maintained By**: Development team
**Review Frequency**: After major changes or monthly

**Note**: Keep this directory updated as the project evolves. Use `claude-md-management:revise-claude-md` skill to incorporate learnings.
