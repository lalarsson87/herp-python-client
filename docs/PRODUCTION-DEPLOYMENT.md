# Production Deployment Guide
**HERP Project - Domain-Driven Architecture**

**Last Updated**: January 25, 2026
**Version**: 2.0 (Post-Phase 4)

---

## Pre-Deployment Checklist

### Critical Requirements ✅

- [x] **API Contract Fixes Applied**
  - [x] HerpClient uses PUT (not PATCH) for evaluation submission
  - [x] ReviewGenerator validates Notion property existence before writes
  - [x] Contact type mapping includes logging for unknown types

- [x] **All Tests Passing**
  - [x] 464/464 unit tests passing
  - [x] >90% code coverage across all domains
  - [x] Test execution: 13.67 seconds

- [x] **Code Quality**
  - [x] Type hints: 100%
  - [x] Linting: Pass
  - [x] Documentation: High

### Environment Setup

#### Required Environment Variables

```bash
# HERP API Configuration
HERP_API_KEY=herp_xxxxxxxxxxxxxxxxxxxxx
HERP_API_BASE_URL=https://public-api.herp.cloud/hire/public

# Notion API Configuration
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxx
NOTION_CANDIDATES_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_INTERVIEWS_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Optional
NOTION_EVALUATIONS_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Optional

# Rate Limiting (Optional - uses defaults if not set)
HERP_RATE_LIMIT_DELAY=0.6  # seconds between requests (100 req/min)
NOTION_RATE_LIMIT_DELAY=0.34  # seconds between requests (3 req/sec)

# File Storage (Optional)
CANDIDATE_FILES_DIR=/var/herp/candidate-files

# Logging (Optional)
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json  # json or text
```

#### Credential Management

**Production Secrets**:
1. Store API keys in secure vault (AWS Secrets Manager, Google Secret Manager, etc.)
2. Never commit `.env` file to version control
3. Rotate API keys quarterly
4. Use different keys for staging and production

**Validation**:
```bash
# Test HERP API connectivity
python scripts/test-herp-api.py

# Test Notion API connectivity
python -m src.cli.entrypoints.sync_full --dry-run
```

---

## Deployment Steps

### Step 1: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import src; print('✅ Package import successful')"
```

### Step 2: Run Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run integration tests (requires live API access)
pytest tests/integration/ -v --live-api

# Check coverage
pytest tests/ --cov=src --cov-report=html
```

### Step 3: Database Verification

**Verify Notion Database Schema**:

The following Notion properties are used by ReviewGenerator:
- 📊 Overall Score (Number)
- 🎯 Recommendation (Select: Strong Hire, Hire, Weak Hire, No Hire)
- 📈 Velocity Score (Number, 0-1 scale)
- ⚠️ Risk Level (Select: High, Medium, Low)
- ⏱️ Time to Current Stage (Number, days)

**If these properties don't exist, ReviewGenerator will skip them** (graceful degradation).

To add missing properties:
1. Open Notion database
2. Add property with exact name (including emoji)
3. Set correct type (Number or Select)
4. For Select properties, add options: Strong Hire, Hire, Weak Hire, No Hire (for Recommendation) or High, Medium, Low (for Risk Level)

### Step 4: Initial Sync (Dry Run)

```bash
# Test sync without making changes
python -m src.cli.entrypoints.sync_full --dry-run

# Review the output for:
# - Candidates to sync
# - Potential conflicts
# - API rate limiting
```

### Step 5: Production Sync

```bash
# Run full sync
python -m src.cli.entrypoints.sync_full

# Or incremental sync (only changed candidates)
python -m src.cli.entrypoints.sync_full --since 2026-01-24T00:00:00Z
```

---

## Monitoring & Operations

### Health Checks

**API Connectivity**:
```bash
# HERP API health check
curl -H "Authorization: Bearer $HERP_API_KEY" \
  https://public-api.herp.cloud/hire/public/v1/candidacies?pageSize=1

# Notion API health check
curl -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2022-06-28" \
  https://api.notion.com/v1/users/me
```

**Rate Limit Monitoring**:
- HERP: Check `x-remaining-request` header (should be >50)
- Notion: Monitor `Retry-After` headers (indicates rate limiting)

### Logging

**Log Locations**:
- Application logs: stdout (structured JSON or text)
- Sync state: `/tmp/herp-notion-sync-state.json`
- Downloaded files: `/tmp/herp-candidate-files/` (or $CANDIDATE_FILES_DIR)

**Important Log Events**:
- `INFO`: Successful syncs, property updates, file downloads
- `WARNING`: Missing Notion properties, unknown contact types, skipped candidates
- `ERROR`: API failures, network errors, data validation failures
- `CRITICAL`: Unrecoverable errors, authentication failures

### Alerting Thresholds

Set up alerts for:
- **Error Rate** >5% over 1 hour window
- **API Rate Limit** <10 remaining requests
- **Sync Duration** >2x baseline (indicates performance degradation)
- **Failed Syncs** 3 consecutive failures

---

## Troubleshooting

### Common Issues

#### 1. Rate Limit Errors

**Symptom**: `429 Too Many Requests` from HERP or Notion

**Solution**:
```bash
# Increase rate limit delay
export HERP_RATE_LIMIT_DELAY=1.0  # Slower (60 req/min)
export NOTION_RATE_LIMIT_DELAY=0.5  # Slower (2 req/sec)

# Re-run sync
python -m src.cli.entrypoints.sync_full
```

#### 2. Missing Notion Properties

**Symptom**: Logs show `Skipping missing properties: ['📊 Overall Score', ...]`

**Solution**: Add missing properties to Notion database (see Step 3 above)

**Workaround**: Properties are optional - sync will continue without them

#### 3. Unknown Contact Types

**Symptom**: Logs show `Unknown HERP contact type encountered: 'new_type'`

**Solution**:
1. Verify against HERP API documentation
2. If valid, add to `src/domains/sync/mappers/herp_notion_mapper.py`:
   ```python
   mapping = {
       # ... existing mappings ...
       "new_type": "New Type Label"
   }
   ```
3. Submit PR to update codebase

#### 4. Authentication Failures

**Symptom**: `401 Unauthorized` from HERP or Notion

**Solution**:
1. Verify API keys are correct and not expired
2. Check API key permissions/scopes
3. Regenerate keys if necessary
4. Update environment variables

---

## Performance Optimization

### Sync Strategies

**Full Sync** (Initial or Monthly):
```bash
# Sync all candidates (slow, comprehensive)
python -m src.cli.entrypoints.sync_full
```

**Incremental Sync** (Daily/Hourly):
```bash
# Only sync candidates updated in last 24 hours
python -m src.cli.entrypoints.sync_full --since $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)
```

**Single Candidate** (Ad-hoc):
```bash
# Sync specific candidate
python -m src.cli.entrypoints.sync_full --candidate-id 550e8400-e29b-41d4-a716-446655440000
```

### Expected Performance

| Operation | Candidates | Duration | Notes |
|-----------|-----------|----------|-------|
| Full Sync (Cold Start) | 1,000 | ~45 min | First sync with file downloads |
| Incremental Sync | 100 | ~5 min | Daily updates only |
| Single Candidate | 1 | ~3 sec | Ad-hoc sync |

**Bottlenecks**:
- HERP API: 100 req/min limit
- Notion API: 3 req/sec limit
- File downloads: Network bandwidth

---

## Rollback Procedures

### If Deployment Fails

**1. Revert to Previous Version**:
```bash
git checkout <previous-commit>
pip install -r requirements.txt
```

**2. Restore Sync State**:
```bash
# Restore previous sync state file
cp /backup/herp-notion-sync-state.json /tmp/herp-notion-sync-state.json
```

**3. Verify Rollback**:
```bash
pytest tests/unit/ -v
python -m src.cli.entrypoints.sync_full --dry-run
```

### Data Recovery

**Notion Pages**:
- Notion has built-in version history (90 days)
- Restore from Notion UI: Page menu → Page history

**HERP Data**:
- HERP is source of truth (read-only from our side)
- Re-sync from HERP to Notion if needed

---

## Security Considerations

### API Key Protection

**DO**:
- Store keys in environment variables or secret managers
- Rotate keys quarterly
- Use different keys for staging/production
- Audit key usage regularly

**DON'T**:
- Commit keys to git
- Log full API keys
- Share keys via email/Slack
- Use production keys in development

### Data Privacy

**PII Handling**:
- Candidate data contains personal information
- Comply with GDPR and Japanese privacy laws
- Redact PII from logs and error messages
- Implement data retention policies

**Access Control**:
- Limit API key access to necessary personnel
- Use principle of least privilege
- Audit API calls for unauthorized access

---

## Maintenance Schedule

### Daily
- Monitor sync success rate
- Review error logs
- Check rate limit usage

### Weekly
- Review sync performance metrics
- Analyze unknown contact types log
- Update documentation if needed

### Monthly
- Run full sync for data consistency
- Review and update API contract tests
- Check for HERP/Notion API updates

### Quarterly
- Rotate API keys
- Performance optimization review
- Dependency updates (pip, Python version)
- Security audit

---

## Support & Escalation

### Internal Support

**First Line**:
1. Check logs for specific error
2. Review troubleshooting section above
3. Consult API documentation (HERP, Notion)

**Second Line**:
1. Review recent code changes (git log)
2. Check for API schema changes
3. Run integration tests against live APIs

**Escalation**:
- HERP API issues → HERP support team
- Notion API issues → Notion support
- Code bugs → Development team

### External Documentation

- **HERP API Docs**: https://public-api.herp.cloud/hire/public/docs
- **Notion API Docs**: https://developers.notion.com
- **Project Docs**: `docs/migration-progress.md`, `PROJECT-SUMMARY.md`

---

## Changelog

### Version 2.0 (2026-01-25)

**API Contract Fixes**:
- ✅ Fixed HerpClient to use PUT (not PATCH) for evaluation submission
- ✅ Added Notion property validation in ReviewGenerator
- ✅ Enhanced contact type mapping with logging for unknown types

**Phase 4 Completion**:
- ✅ Migrated 16/17 scripts (94.1% completion)
- ✅ 464/464 tests passing
- ✅ Created shared CandidateDataFetcher utility

### Version 1.0 (2026-01-24)

**Initial Release**:
- Domain-driven architecture migration
- Phases 1-3 complete (14/17 scripts)
- 373 tests passing

---

**Document Owner**: Engineering Team
**Review Cycle**: Quarterly
**Next Review**: April 2026

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
