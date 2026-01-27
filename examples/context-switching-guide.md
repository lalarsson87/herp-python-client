# Context Switching Guide

Learn how to effectively switch between different contexts to optimize Claude Code for various types of work.

## What Are Contexts?

Contexts are domain-specific system prompts that configure Claude Code with specialized knowledge, workflows, and best practices for different types of tasks.

## Available Contexts

1. **recruiting.md** - Recruiting and candidate management
2. **hr.md** - Human resources and employee management
3. **engineering-pr.md** - Engineering and pull request workflows
4. **newsflashes.md** - Quick communications and announcements
5. **reports-proposals.md** - Formal reports and business proposals

## When to Use Each Context

### Recruiting Context

**Use when**:
- Managing candidate applications
- Scheduling interviews
- Reviewing resumes
- Tracking hiring pipeline
- Coordinating with hiring managers

**Enabled MCP Servers**:
- `herp-hire` (primary)
- `slack` (notifications)
- `notion` (documentation)
- `google-drive` (resume storage)

**Example Tasks**:
```
- "Create a new candidate for the Senior Engineer position"
- "List all candidates currently in the interview stage"
- "Schedule an interview with candidate ID xyz"
- "Update the candidate to offer stage"
```

### HR Context

**Use when**:
- Onboarding new employees
- Managing performance reviews
- Updating policies
- Creating employee documentation
- Handling benefits administration

**Enabled MCP Servers**:
- `notion` (employee databases)
- `google-drive` (policies, documents)
- `slack` (employee communications)
- `confluence` (policy wiki)

**Example Tasks**:
```
- "Create an onboarding checklist for new hires"
- "Update the employee handbook with new PTO policy"
- "Generate a performance review template"
- "Create a benefits enrollment guide"
```

### Engineering PR Context

**Use when**:
- Creating pull requests
- Reviewing code
- Generating release notes
- Managing deployments
- Writing technical documentation

**Enabled MCP Servers**:
- `slack` (engineering channels)
- `confluence` (technical docs)
- `notion` (project tracking)

**Example Tasks**:
```
- "Create a PR description for these changes"
- "Review this pull request for security issues"
- "Generate release notes from merged PRs"
- "Create deployment checklist"
```

### Newsflashes Context

**Use when**:
- Writing company announcements
- Creating team newsletters
- Drafting incident reports
- Sending quick updates
- Announcing events

**Enabled MCP Servers**:
- `slack` (primary distribution)
- `notion` (archive)
- `confluence` (published announcements)

**Example Tasks**:
```
- "Draft a company-wide announcement about the holiday schedule"
- "Create an incident report for the outage"
- "Write a weekly engineering newsletter"
- "Announce the product launch"
```

### Reports & Proposals Context

**Use when**:
- Creating business proposals
- Writing performance reports
- Developing strategic plans
- Preparing budgets
- Generating executive summaries

**Enabled MCP Servers**:
- `notion` (drafting)
- `google-drive` (storage)
- `confluence` (publishing)

**Example Tasks**:
```
- "Create a proposal for the new marketing initiative"
- "Generate Q4 performance report"
- "Write an executive summary of our metrics"
- "Develop a budget proposal for next year"
```

## How to Switch Contexts

### Method 1: Explicit Reference

Simply mention the context in your request:

```
"Using the recruiting context, create a new candidate application"
"Switch to engineering-pr context and review this code"
"In the HR context, create an onboarding guide"
```

### Method 2: Implicit from Task

Claude Code can infer context from your task:

```
"Schedule an interview with the candidate" → Recruiting context
"Update the employee handbook" → HR context
"Review this pull request" → Engineering PR context
"Draft a company announcement" → Newsflashes context
"Create a Q4 report" → Reports & Proposals context
```

### Method 3: MCP Server Configuration

Disable/enable relevant MCP servers in `mcp-configs/mcp-servers.json`:

```json
{
  "mcpServers": {
    "herp-hire": { "disabled": false },  // Enable for recruiting
    "slack": { "disabled": false },      // Enable for all
    "notion": { "disabled": false },     // Enable for all
    "google-drive": { "disabled": true }, // Disable when not needed
    "confluence": { "disabled": true }   // Disable when not needed
  }
}
```

## Context Switching Best Practices

### 1. Focus on One Domain at a Time

**Good**:
```
Morning: Recruiting work (recruiting context)
Afternoon: Engineering PRs (engineering-pr context)
Evening: Reports (reports-proposals context)
```

**Avoid**:
```
Switching contexts every 5 minutes
```

### 2. Enable Only Necessary MCP Servers

**Why**: Each enabled MCP server consumes context window space.

**Strategy**:
- Enable 3-5 servers for current work
- Disable servers you won't use today
- Re-enable as needed

### 3. Use Context-Specific Workflows

Each context provides optimized workflows. Follow them:

**Recruiting**: Candidate → Screening → Interview → Offer → Hired
**HR**: Draft → Review → Approve → Publish → Archive
**Engineering**: Code → PR → Review → Merge → Deploy
**Newsflashes**: Draft → Review → Send → Archive
**Reports**: Research → Draft → Review → Finalize → Distribute

### 4. Maintain Consistency Within Sessions

Once you start working in a context, complete related tasks before switching:

```
✓ Good:
  - Create 3 candidate applications (recruiting context)
  - Schedule all interviews
  - Update all candidate stages
  - Then switch to HR context

✗ Avoid:
  - Create 1 candidate (recruiting)
  - Update policy (HR)
  - Review PR (engineering)
  - Create candidate (recruiting again)
```

## Context-Specific Command Examples

### Recruiting Commands
```bash
herp_list_candidacies --status inProgress
herp_create_candidacy --name "Jane Doe" --requisitionId "..."
herp_update_candidacy_step --candidacyId "..." --step "interview"
```

### HR Commands
```bash
# Notion database queries for employees
# Google Drive file operations for policies
# Slack messages to HR channels
```

### Engineering Commands
```bash
# GitHub PR operations
# Confluence documentation updates
# Slack engineering channel posts
```

## Performance Optimization

### Context Window Usage

Different contexts consume different amounts of context window:

- **Light** (30-40k tokens): newsflashes, simple reports
- **Medium** (50-70k tokens): hr, engineering-pr
- **Heavy** (80-100k tokens): recruiting (with HERP API), complex reports

### Recommendations

1. **For Heavy Contexts**: Disable all non-essential MCP servers
2. **For Light Contexts**: Can enable more MCP servers
3. **Monitor**: If responses slow down, disable some servers

## Troubleshooting

### "Context window full" errors

**Solution**:
1. Disable unused MCP servers
2. Start a new conversation
3. Use more focused queries

### Wrong context activated

**Solution**:
1. Explicitly state desired context
2. Check which MCP servers are enabled
3. Restart conversation if needed

### Mixed context confusion

**Solution**:
1. Focus on one type of work at a time
2. Clearly indicate context switches
3. Complete workflows before switching

## Advanced: Custom Contexts

You can create your own contexts:

1. Create new `.md` file in `contexts/` directory
2. Define domain focus, data sources, workflows
3. Specify which MCP servers to use
4. Document common tasks and patterns

Example structure:
```markdown
# My Custom Context

## Domain Focus
[What this context is for]

## Data Sources
[Which MCP servers to use]

## Key Principles
[Guidelines for this domain]

## Common Tasks
[Typical workflows]

## Integration Points
[How systems connect]
```

## Summary

- Use contexts to optimize for specific types of work
- Switch contexts explicitly or let Claude Code infer
- Enable only necessary MCP servers
- Follow context-specific workflows
- Complete related work before switching
- Create custom contexts as needed
