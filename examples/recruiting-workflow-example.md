# Recruiting Workflow Example

This example demonstrates a complete recruiting workflow using the HERP API MCP server and recruiting context.

## Scenario

You need to process a new candidate application, schedule interviews, and track progress through the hiring pipeline.

## Step 1: Activate Recruiting Context

The recruiting context provides domain-specific guidance for candidate management.

## Step 2: Create New Candidate

```bash
# Create a new candidate application
herp_create_candidacy \
  --channel "careerPage" \
  --requisitionId "550e8400-e29b-41d4-a716-446655440000" \
  --name "Alex Johnson" \
  --email "alex.johnson@example.com" \
  --phoneNumber "+1-555-0123"
```

**Response**:
```json
{
  "data": {
    "candidacyId": "660e8400-e29b-41d4-a716-446655440001",
    "status": "inProgress",
    "step": "entry",
    "createdAt": "2024-01-15T10:00:00Z"
  }
}
```

## Step 3: Upload Resume

```bash
# Upload candidate's resume
herp_upload_file \
  --candidacyId "660e8400-e29b-41d4-a716-446655440001" \
  --fileType "resume" \
  --filePath "/path/to/resume.pdf"
```

## Step 4: Initial Screening

```bash
# Move to document screening stage
herp_update_candidacy_step \
  --candidacyId "660e8400-e29b-41d4-a716-446655440001" \
  --step "documentScreening"

# Add screening notes
herp_add_timeline_comment \
  --candidacyId "660e8400-e29b-41d4-a716-446655440001" \
  --comment "Strong technical background. 5 years of relevant experience. Proceed to interview." \
  --format "text/plain"
```

## Step 5: Schedule Interview

```bash
# Create interview contact
herp_create_contact \
  --candidacyId "660e8400-e29b-41d4-a716-446655440001" \
  --contactType "interview" \
  --scheduledAt "2024-01-20T14:00:00Z" \
  --createEvaluation true

# Update to interview stage
herp_update_candidacy_step \
  --candidacyId "660e8400-e29b-41d4-a716-446655440001" \
  --step "interview"

# Notify team via Slack (using Slack MCP)
# Post to #recruiting channel about scheduled interview
```

## Step 6: Track Interview Progress

```bash
# After interview, add feedback
herp_add_timeline_comment \
  --candidacyId "660e8400-e29b-41d4-a716-446655440001" \
  --comment "## Interview Feedback\n\n**Technical Skills**: 4/5\n**Communication**: 5/5\n**Culture Fit**: 4/5\n\nRecommend moving to offer stage." \
  --format "text/markdown"

# Move to offer stage
herp_update_candidacy_step \
  --candidacyId "660e8400-e29b-41d4-a716-446655440001" \
  --step "offer"
```

## Step 7: Extend Offer

```bash
# Document offer details in Notion
# Upload offer letter to Google Drive
# Share with hiring manager via Slack

# When candidate accepts
herp_update_candidacy_step \
  --candidacyId "660e8400-e29b-41d4-a716-446655440001" \
  --step "offerAccepted"

# Terminate with 'hired' reason
herp_terminate_candidacy \
  --candidacyId "660e8400-e29b-41d4-a716-446655440001" \
  --reason "hired"

# Add final note
herp_add_timeline_comment \
  --candidacyId "660e8400-e29b-41d4-a716-446655440001" \
  --comment "Offer accepted! Start date: 2024-02-01. Initiate onboarding process." \
  --format "text/plain"
```

## Step 8: Generate Hiring Report

```bash
# List all recent hires
herp_list_candidacies \
  --status "terminated" \
  --updatedSince "2024-01-01T00:00:00Z"

# Export to Notion database for reporting
# Update hiring metrics in Google Sheets
# Share success story in Slack #wins channel
```

## Best Practices

### Privacy & Compliance
- Always handle candidate data with confidentiality
- Follow GDPR/privacy law requirements
- Document all interactions in timeline
- Maintain audit trail

### Communication
- Keep all stakeholders informed
- Use Slack for team coordination
- Document decisions in Notion
- Store documents in Google Drive

### Efficiency
- Batch similar operations
- Use templates for common communications
- Automate status updates
- Track metrics for improvement

### Quality
- Apply consistent evaluation criteria
- Provide timely feedback
- Maintain professional communication
- Document rejection reasons appropriately

## Integration Points

This workflow integrates:
- **HERP API**: Core candidate management
- **Slack**: Team notifications and coordination
- **Notion**: Documentation and tracking
- **Google Drive**: Document storage
- **Confluence**: Process documentation (optional)

## Common Queries

### Find Candidates at Interview Stage
```bash
herp_list_candidacies --status inProgress --step interview
```

### Get Specific Candidate Details
```bash
herp_get_candidacy --candidacyId "660e8400-e29b-41d4-a716-446655440001"
```

### List Active Job Requisitions
```bash
herp_list_requisitions --status open
```

### View Team Members
```bash
herp_list_users --role recruiter --status active
```

## Troubleshooting

### Rate Limiting
If you hit rate limits (100 req/min):
- Add delays between bulk operations
- Monitor `x-remaining-request` header
- Wait for `x-reset-at` timestamp

### Missing Permissions
Ensure your API key has required scopes:
- `candidacy:write` for creating/updating
- `candidacy:read` for listing/viewing

### File Upload Issues
- Verify file size is under 50MB
- Check file format is supported
- Ensure file path is accessible
