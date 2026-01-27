# HERP Hire MCP Server

A Model Context Protocol (MCP) server for integrating with the HERP Hire API, enabling recruiting and candidate management capabilities in Claude Code.

**Belong Inc Integration**: Currently managing 7,181+ candidates across 33 open positions in 6 divisions (Engineering: 17 positions, Product, Operations, Corporate, Marketing, Customer Success).

## Features

- **Candidate Management**: Create, list, and update candidate applications
- **Workflow Automation**: Move candidates through hiring stages
- **Document Handling**: Upload and manage resumes and documents
- **Timeline Tracking**: Add comments and track candidate interactions
- **Contact Management**: Schedule interviews and evaluations
- **Team Collaboration**: Assign team members to applications
- **Job Requisitions**: Access job position data
- **Rate Limit Awareness**: Automatically tracks API rate limits

## Installation

1. Navigate to the server directory:
```bash
cd mcp-configs/herp-api-server
```

2. Install dependencies:
```bash
npm install
```

3. Build the TypeScript code:
```bash
npm run build
```

## Configuration

### Environment Variables

Set the following environment variables (see `.env.example` in the root directory):

```bash
HERP_API_KEY=your-herp-api-key
HERP_API_BASE_URL=https://public-api.herp.cloud/hire/public
```

### MCP Server Configuration

The server is pre-configured in `mcp-configs/mcp-servers.json`:

```json
{
  "herp-hire": {
    "command": "node",
    "args": ["/path/to/mcp-configs/herp-api-server/dist/index.js"],
    "env": {
      "HERP_API_KEY": "${HERP_API_KEY}",
      "HERP_API_BASE_URL": "https://public-api.herp.cloud/hire/public"
    }
  }
}
```

## Available Tools

### Candidate Management

- `herp_list_candidacies`: List candidate applications with filtering
- `herp_get_candidacy`: Get detailed candidate information
- `herp_create_candidacy`: Create a new candidate application
- `herp_update_candidacy_step`: Move candidate to a new hiring stage
- `herp_terminate_candidacy`: End a candidate application

### Communication & Timeline

- `herp_add_timeline_comment`: Add comments to candidate timeline
- `herp_create_contact`: Schedule interviews or evaluations

### File Management

- `herp_upload_file`: Upload resumes or documents
- `herp_list_files`: List files attached to a candidate

### Master Data

- `herp_list_requisitions`: List job positions
- `herp_list_users`: List team members and recruiters

## Usage Examples

### List Active Candidates

```typescript
// Using the MCP tool
await mcp.callTool("herp_list_candidacies", {
  status: "inProgress",
  step: "interview"
});
```

### Create a New Candidate

```typescript
await mcp.callTool("herp_create_candidacy", {
  channel: "careerPage",
  requisitionId: "550e8400-e29b-41d4-a716-446655440000",
  name: "Jane Doe",
  email: "jane@example.com"
});
```

### Add Timeline Comment

```typescript
await mcp.callTool("herp_add_timeline_comment", {
  candidacyId: "550e8400-e29b-41d4-a716-446655440000",
  comment: "Great interview! Moving to next stage.",
  format: "text/plain"
});
```

## API Reference

The HERP Hire API documentation is available at:
https://public-api.herp.cloud/hire/public/doc

### Rate Limits

- 100 requests per minute per tenant
- Rate limit info is included in all responses
- Headers: `x-remaining-request`, `x-reset-at`

### Authentication

Requires a valid API key from the HERP Hire admin dashboard. API access is only available to paid plan customers.

### Required Scopes

Depending on operations, you may need the following scopes:
- `candidacy:read` - Read candidate data
- `candidacy:write` - Create and update candidates
- `requisition:read` - Read job requisitions
- `user:read` - Read user data

## Development

### Watch Mode

```bash
npm run dev
```

### Rebuild

```bash
npm run build
```

### Testing

Test the server by running it directly:

```bash
HERP_API_KEY=your-key node dist/index.js
```

## Troubleshooting

### Authentication Errors

- Verify your API key is correct
- Ensure your account has the necessary scopes
- Check that you're on a paid HERP plan

### Rate Limit Errors

- The server returns rate limit info in responses
- Wait for the reset time indicated in `x-reset-at` header
- Consider implementing request queuing for high-volume operations

### Connection Errors

- Verify `HERP_API_BASE_URL` is correct
- Check network connectivity
- Ensure firewall allows outbound HTTPS

## Belong-Specific Workflows

### Typical Recruiting Workflow at Belong

Belong's hiring process averages 4 weeks with the following stages:

1. **Document Review**
   ```typescript
   // List candidates in document review stage
   await mcp.callTool("herp_list_candidacies", {
     status: "inProgress",
     step: "documentReview"
   });
   ```

2. **Casual Conversation**
   ```typescript
   // Schedule casual conversation
   await mcp.callTool("herp_create_contact", {
     candidacyId: "candidate-id",
     contactType: "casualConversation",
     scheduledAt: "2026-01-30T10:00:00Z"
   });

   // Add timeline comment
   await mcp.callTool("herp_add_timeline_comment", {
     candidacyId: "candidate-id",
     comment: "Scheduled casual conversation to discuss role and culture fit",
     format: "text/plain"
   });
   ```

3. **Interviews (3-4 rounds)**
   ```typescript
   // Move to interview stage
   await mcp.callTool("herp_update_candidacy_step", {
     candidacyId: "candidate-id",
     step: "interview"
   });

   // Track interview rounds
   await mcp.callTool("herp_add_timeline_comment", {
     candidacyId: "candidate-id",
     comment: "Technical interview round 1/3 completed. Strong performance on Go backend assessment.",
     format: "text/plain"
   });
   ```

4. **Reference Checks**
   ```typescript
   await mcp.callTool("herp_update_candidacy_step", {
     candidacyId: "candidate-id",
     step: "referenceCheck"
   });
   ```

5. **Offer**
   ```typescript
   await mcp.callTool("herp_update_candidacy_step", {
     candidacyId: "candidate-id",
     step: "offer"
   });

   await mcp.callTool("herp_add_timeline_comment", {
     candidacyId: "candidate-id",
     comment: "Offer presented: Backend Engineer, ¥30M insurance, flex-time, remote options, training budget",
     format: "text/plain"
   });
   ```

### Finding Engineering Candidates

```typescript
// List all engineering candidates in progress
await mcp.callTool("herp_list_candidacies", {
  status: "inProgress",
  // Filter by engineering requisitions
  // (17 engineering positions: Backend, SRE, Data Science, GenAI, Frontend, EM)
});
```

### Bulk Operations Considerations

With 7,181+ candidates in the system:
- Be mindful of rate limits (100 requests/minute)
- Use pagination for large result sets
- Implement delays between requests for bulk updates
- Monitor `x-remaining-request` header

## Integration with Notion

This MCP server is designed to work alongside Notion MCP for extended workflows:
- Store detailed interview notes in Notion
- Sync HERP candidacy IDs to Notion database "HERP Candidacy ID" field
- Cross-reference candidate data across systems
- Export analytics to Google Sheets via Notion

## License

MIT
