# Agents Directory

Specialized agents for automated workflows and complex multi-step tasks.

## Available Agents

### 1. HERP Candidate Reviewer (`herp-candidate-reviewer.md`)

**Purpose**: Automate comprehensive candidate reviews in the HERP Hire system.

**Key Features**:
- Complete candidate analysis from HERP data
- Structured evaluation with ratings
- Automated timeline updates
- Decision recommendations (Hire/Advance/Hold/Reject)
- Compliance and audit trail maintenance

**Use Cases**:
- "Review candidate ID xyz and provide recommendation"
- "Review all candidates in interview stage and prioritize top 3"
- "Perform detailed analysis with cultural fit assessment"

**Tools Used**: HERP API tools, Read

**Context**: recruiting

---

### 2. Employee Performance Reviewer (`employee-performance-reviewer.md`)

**Purpose**: Conduct comprehensive employee performance and psychological assessments.

**Key Features**:
- Multi-dimensional performance analysis
- Psychological well-being assessment
- Burnout risk detection
- 360-degree feedback synthesis
- Career development planning
- Training and resource recommendations

**Use Cases**:
- "Conduct annual performance review for [Name]"
- "Assess [Name]'s burnout risk and provide recommendations"
- "Evaluate [Name]'s readiness for promotion to Senior Engineer"
- "Review performance and well-being for entire Engineering team"

**Tools Used**: Notion MCP tools, Read, Write

**Context**: hr

---

### 3. HERP-Notion Sync (`herp-notion-sync.md`)

**Purpose**: Maintain bi-directional synchronization between HERP Hire and Notion databases.

**Key Features**:
- Bi-directional sync (HERP ↔ Notion)
- Automatic field mapping and transformation
- Conflict resolution strategies
- Incremental and full sync modes
- Change detection and tracking
- Error handling and retry logic
- Sync state monitoring

**Use Cases**:
- "Perform initial full sync from HERP to Notion"
- "Sync candidates updated in last 24 hours"
- "Sync single candidate ID xyz from HERP to Notion"
- "Check sync status and report discrepancies"

**Tools Used**: HERP API tools, Notion MCP tools

**Context**: recruiting

---

## Agent Architecture

Agents follow this structure:

```yaml
---
name: agent-name
description: Brief description
version: 1.0.0
tools:
  - tool_1
  - tool_2
model: sonnet
contexts:
  - relevant-context
---

# Agent Content
[Detailed documentation, workflows, templates, etc.]
```

## Usage Pattern

### Invoking Agents

Agents can be invoked explicitly or contextually:

**Explicit Invocation**:
```
"Use the HERP candidate reviewer agent to analyze candidate xyz"
```

**Contextual Invocation**:
```
"Review candidate xyz and provide hiring recommendation"
# Claude Code automatically uses herp-candidate-reviewer agent
```

### Agent Workflow

1. **Data Collection**: Gather all required information
2. **Analysis**: Process data according to structured criteria
3. **Output Generation**: Create formatted reports/recommendations
4. **Actions**: Perform automated updates and notifications
5. **Logging**: Maintain audit trail

## Creating Custom Agents

To create a new agent:

1. Create a new `.md` file in `agents/` directory
2. Add YAML frontmatter with metadata
3. Document the agent's purpose and capabilities
4. Define workflows and processes
5. Provide templates and examples
6. Specify tools and contexts
7. Include usage examples

### Example Template

```markdown
---
name: my-custom-agent
description: What this agent does
version: 1.0.0
tools:
  - tool_1
  - tool_2
model: sonnet  # or haiku, opus
contexts:
  - relevant-context
---

# My Custom Agent

## Purpose
[What problem does this solve?]

## Capabilities
1. [Capability 1]
2. [Capability 2]

## Workflow
[Step-by-step process]

## Usage Examples
[How to invoke and use]

## Templates
[Output templates]
```

## Agent Best Practices

### Design Principles

1. **Single Responsibility**: Each agent should have one clear purpose
2. **Structured Output**: Use consistent templates and formats
3. **Error Handling**: Handle edge cases gracefully
4. **Documentation**: Provide clear usage examples
5. **Audit Trail**: Log all actions and decisions

### Performance

1. **Batch Operations**: Process multiple items efficiently
2. **Caching**: Cache frequently accessed data
3. **Rate Limiting**: Respect API rate limits
4. **Parallel Processing**: Use concurrent operations when possible

### Quality

1. **Validation**: Validate inputs and outputs
2. **Testing**: Test with real data scenarios
3. **Monitoring**: Track agent performance metrics
4. **Improvement**: Continuously refine based on outcomes

## Integration with Contexts

Agents are optimized for specific contexts:

- **recruiting**: herp-candidate-reviewer, herp-notion-sync
- **hr**: employee-performance-reviewer
- **engineering-pr**: (future agents)
- **newsflashes**: (future agents)
- **reports-proposals**: (future agents)

When working in a specific context, relevant agents are automatically available.

## Agent Metrics

Track these metrics for agent effectiveness:

- **Execution Success Rate**: % of successful completions
- **Average Execution Time**: Time to complete workflow
- **Output Quality**: Accuracy and usefulness of results
- **Error Rate**: Frequency of failures
- **User Satisfaction**: Feedback on agent outputs

## Future Agents

Planned agents for development:

### Recruiting
- **Interview Scheduler**: Coordinate interview times across calendars
- **Offer Letter Generator**: Create customized offer letters
- **Candidate Sourcing**: Automated candidate search and outreach

### HR
- **Onboarding Coordinator**: Manage new hire onboarding tasks
- **Benefits Enrollment**: Guide through benefits selection
- **Policy Updater**: Maintain and version HR policies

### Engineering
- **PR Review Orchestrator**: Coordinate code reviews
- **Release Notes Generator**: Compile release documentation
- **Tech Debt Tracker**: Identify and prioritize technical debt

### General
- **Meeting Summarizer**: Generate meeting notes and action items
- **Report Compiler**: Aggregate data into reports
- **Notification Router**: Smart routing of alerts and updates

## Troubleshooting

### Agent Not Working

1. Verify required tools are available
2. Check context is activated
3. Ensure API credentials are configured
4. Review error logs for details

### Incomplete Results

1. Check data availability in source systems
2. Verify field mappings are correct
3. Review validation rules
4. Ensure sufficient permissions

### Performance Issues

1. Reduce batch sizes
2. Enable caching
3. Check API rate limits
4. Use incremental operations

## Support

For agent-related questions or issues:

1. Review agent documentation in respective `.md` files
2. Check examples in `examples/` directory
3. Review relevant context files in `contexts/`
4. Consult main [README.md](../README.md)

---

**Last Updated**: 2024-01-22
**Agent Count**: 3
**Maintained By**: Operations Team
