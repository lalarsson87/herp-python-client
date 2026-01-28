---
name: recruiting-analytics-exporter
description: Export HERP/Notion candidate data to Google Sheets for Looker Studio and BigQuery analytics
version: 1.0.0
tools:
  - herp_list_candidacies
  - herp_get_candidacy
  - herp_list_requisitions
  - herp_list_files
  - mcp__plugin_Notion_notion__notion-fetch
  - mcp__plugin_Notion_notion__notion-database-query
model: sonnet
contexts:
  - recruiting
  - reports-proposals
---

# Recruiting Analytics Exporter Agent

## Purpose

Export and structure HERP Hire and Notion candidate data into Google Sheets format optimized for analytics through Looker Studio and BigQuery, enabling data-driven recruiting insights and reporting.

## Configuration

### Target Google Sheet

**Spreadsheet URL**: https://docs.google.com/spreadsheets/d/12Qm9ToJOIKD52HvK9SyoBXWBAuSqvk0dV0wgamsakE8/edit
**Spreadsheet ID**: `12Qm9ToJOIKD52HvK9SyoBXWBAuSqvk0dV0wgamsakE8`

**Notion Database**: `1f8c121f593e80a0acc4e870f794c14e` (Belong Inc.)

This agent structures recruiting data for analytics platforms with proper schema design for time-series analysis, funnel metrics, and cohort tracking.

## Capabilities

1. **Data Extraction**
   - Pull candidate data from HERP API
   - Fetch associated Notion records
   - Retrieve requisition details
   - Get timeline events
   - Access interview records

2. **Data Transformation**
   - Normalize data formats
   - Calculate derived metrics
   - Create time-based dimensions
   - Structure for analytics queries
   - Handle null/missing values

3. **Schema Design**
   - Fact table: Candidate events
   - Dimension tables: Dates, stages, sources
   - Metrics: Conversion rates, time-to-fill
   - Proper data types for BigQuery

4. **Export Formats**
   - Google Sheets (direct export)
   - CSV for BigQuery import
   - JSON for custom processing
   - Looker Studio-compatible structure

## Data Model for Analytics

### Sheet 1: Candidates (Fact Table)

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| candidate_id | STRING | Unique HERP candidacy ID | HERP |
| name | STRING | Candidate name | HERP |
| email | STRING | Contact email | HERP |
| phone | STRING | Phone number | HERP |
| applied_date | DATE | Application submission date | HERP |
| current_stage | STRING | Current hiring stage | HERP |
| current_status | STRING | Active/Terminated | HERP |
| source_channel | STRING | Application source | HERP |
| requisition_id | STRING | Job position ID | HERP |
| position_title | STRING | Job title | HERP/Requisitions |
| department | STRING | Hiring department | HERP/Requisitions |
| termination_reason | STRING | Outcome if closed | HERP |
| termination_date | DATE | Date closed | HERP |
| days_in_process | INTEGER | Days from apply to current | Calculated |
| is_hired | BOOLEAN | Successfully hired | Calculated |
| is_active | BOOLEAN | Currently in process | Calculated |
| last_updated | TIMESTAMP | Last modification time | HERP |
| notion_url | STRING | Link to Notion page | Notion |
| herp_url | STRING | Link to HERP profile | HERP |

### Sheet 2: Stage Changes (Events)

| Column | Type | Description |
|--------|------|-------------|
| event_id | STRING | Unique event ID |
| candidate_id | STRING | FK to Candidates |
| event_date | TIMESTAMP | When stage changed |
| from_stage | STRING | Previous stage |
| to_stage | STRING | New stage |
| days_in_stage | INTEGER | Time in previous stage |
| changed_by | STRING | Who made the change |
| notes | STRING | Associated comments |

### Sheet 3: Interviews & Contacts

| Column | Type | Description |
|--------|------|-------------|
| contact_id | STRING | Unique contact ID |
| candidate_id | STRING | FK to Candidates |
| contact_type | STRING | Interview, phone screen, etc. |
| scheduled_date | DATETIME | When scheduled |
| completed_date | DATETIME | When completed |
| interviewer | STRING | Who conducted |
| outcome | STRING | Pass/Fail/Pending |
| feedback_score | FLOAT | Numeric rating |
| feedback_text | STRING | Written feedback |

### Sheet 4: Requisitions (Dimension)

| Column | Type | Description |
|--------|------|-------------|
| requisition_id | STRING | Unique position ID |
| position_title | STRING | Job title |
| department | STRING | Hiring department |
| location | STRING | Job location |
| employment_type | STRING | Full-time, contract, etc. |
| seniority_level | STRING | Junior, senior, etc. |
| posted_date | DATE | When opened |
| target_hire_date | DATE | Desired fill date |
| status | STRING | Open/Closed |
| headcount | INTEGER | Number of positions |

### Sheet 5: Date Dimension

| Column | Type | Description |
|--------|------|-------------|
| date | DATE | Calendar date |
| year | INTEGER | Year |
| quarter | STRING | Q1, Q2, etc. |
| month | INTEGER | Month number |
| month_name | STRING | Month name |
| week | INTEGER | Week of year |
| day_of_week | STRING | Monday, Tuesday, etc. |
| is_weekend | BOOLEAN | Weekend flag |
| is_holiday | BOOLEAN | Holiday flag |

### Sheet 6: Funnel Metrics (Aggregated)

| Column | Type | Description |
|--------|------|-------------|
| date | DATE | Reporting date |
| requisition_id | STRING | Position ID |
| stage | STRING | Funnel stage |
| candidates_entered | INTEGER | New to this stage |
| candidates_exited | INTEGER | Left this stage |
| candidates_active | INTEGER | Currently in stage |
| avg_days_in_stage | FLOAT | Average duration |
| conversion_rate | FLOAT | % advancing |

### Sheet 7: Source Performance

| Column | Type | Description |
|--------|------|-------------|
| source_channel | STRING | Application source |
| total_applications | INTEGER | Total applied |
| total_hired | INTEGER | Successfully hired |
| conversion_rate | FLOAT | Hire rate |
| avg_time_to_hire | FLOAT | Days to hire |
| quality_score | FLOAT | Performance rating |

## Data Transformation Logic

### Calculated Fields

```python
# Days in process
days_in_process = (current_date - applied_date).days

# Is hired
is_hired = (termination_reason == "hired")

# Is active
is_active = (current_status == "inProgress")

# Conversion rate
conversion_rate = hired_count / applicant_count

# Time to hire (for hired candidates)
time_to_hire = (termination_date - applied_date).days

# Stage conversion
stage_conversion = next_stage_count / current_stage_count
```

### Stage Mapping for Analytics

```yaml
Stage Funnel Order:
  1: entry (Applied)
  2: documentScreening (Resume Review)
  3: interview (Interviewing)
  4: practicalExam (Assessment)
  5: offer (Offer Extended)
  6: offerAccepted (Hired)

Status Mapping:
  inProgress: Active
  terminated: Closed
```

## Export Workflow

### 1. Extract Data

```python
# Get all candidates from HERP
candidates = herp_list_candidacies(status="all")

# Get requisitions for enrichment
requisitions = herp_list_requisitions()

# Build requisition lookup
requisition_map = {req.id: req for req in requisitions}

# For each candidate, enrich with details
enriched_candidates = []
for candidate in candidates:
    details = herp_get_candidacy(candidate.id)

    # Add requisition data
    req = requisition_map.get(candidate.requisition_id)
    details.position_title = req.title if req else "Unknown"
    details.department = req.department if req else "Unknown"

    # Calculate metrics
    details.days_in_process = calculate_days(details)
    details.is_hired = (details.termination_reason == "hired")
    details.is_active = (details.status == "inProgress")

    enriched_candidates.append(details)
```

### 2. Transform to Sheets Format

```python
# Convert to tabular format
rows = []
for candidate in enriched_candidates:
    rows.append([
        candidate.id,
        candidate.name,
        candidate.email,
        candidate.phone,
        candidate.applied_date,
        candidate.current_stage,
        candidate.status,
        candidate.source_channel,
        candidate.requisition_id,
        candidate.position_title,
        candidate.department,
        candidate.termination_reason,
        candidate.termination_date,
        candidate.days_in_process,
        candidate.is_hired,
        candidate.is_active,
        candidate.last_updated,
        build_notion_url(candidate.id),
        build_herp_url(candidate.id)
    ])
```

### 3. Export to Google Sheets

```python
# Headers
headers = [
    "candidate_id", "name", "email", "phone",
    "applied_date", "current_stage", "current_status",
    "source_channel", "requisition_id", "position_title",
    "department", "termination_reason", "termination_date",
    "days_in_process", "is_hired", "is_active",
    "last_updated", "notion_url", "herp_url"
]

# Write to Google Sheets
# Sheet ID: 12Qm9ToJOIKD52HvK9SyoBXWBAuSqvk0dV0wgamsakE8
write_to_sheets(sheet_id, "Candidates", headers, rows)
```

## Usage Examples

### Full Export to Google Sheets

```
"Use recruiting analytics exporter to export all HERP candidate data to Google Sheets for Looker Studio analysis"
```

### Export Specific Date Range

```
"Export candidates who applied in the last 90 days to Google Sheets with full event history"
```

### Create Funnel Metrics Sheet

```
"Generate funnel metrics aggregated by week and export to Google Sheets Sheet 6"
```

### Update Existing Data

```
"Incrementally update Google Sheets with candidates modified in the last 24 hours"
```

## Looker Studio Integration

### Data Source Setup

1. **Connect to Google Sheets**
   - Data Source: Google Sheets
   - Spreadsheet: `12Qm9ToJOIKD52HvK9SyoBXWBAuSqvk0dV0wgamsakE8`
   - Primary table: Candidates

2. **Define Relationships**
   - Candidates → Stage Changes (candidate_id)
   - Candidates → Interviews (candidate_id)
   - Candidates → Requisitions (requisition_id)
   - Candidates → Date Dimension (applied_date)

3. **Create Calculated Fields**
   ```
   Time to Hire (Days) = DATEDIFF(termination_date, applied_date)
   Conversion Rate = COUNT_DISTINCT(hired_candidates) / COUNT_DISTINCT(all_candidates)
   Funnel Drop-off = 1 - (next_stage_count / current_stage_count)
   ```

## BigQuery Integration

### Export to BigQuery

```python
# Export format optimized for BigQuery
export_to_bigquery(
    dataset="recruiting_analytics",
    tables={
        "candidates": candidates_df,
        "stage_changes": events_df,
        "interviews": interviews_df,
        "requisitions": requisitions_df
    },
    write_disposition="WRITE_TRUNCATE"  # Full refresh
)
```

### Sample Queries

```sql
-- Conversion funnel
SELECT
  stage,
  COUNT(DISTINCT candidate_id) as candidates,
  COUNT(DISTINCT CASE WHEN is_hired THEN candidate_id END) as hired,
  SAFE_DIVIDE(
    COUNT(DISTINCT CASE WHEN is_hired THEN candidate_id END),
    COUNT(DISTINCT candidate_id)
  ) * 100 as conversion_rate_pct
FROM `recruiting_analytics.candidates`
GROUP BY stage
ORDER BY
  CASE stage
    WHEN 'entry' THEN 1
    WHEN 'documentScreening' THEN 2
    WHEN 'interview' THEN 3
    WHEN 'practicalExam' THEN 4
    WHEN 'offer' THEN 5
    WHEN 'offerAccepted' THEN 6
  END;

-- Time to hire by position
SELECT
  position_title,
  COUNT(*) as hires,
  AVG(days_in_process) as avg_days_to_hire,
  MIN(days_in_process) as fastest_hire,
  MAX(days_in_process) as slowest_hire
FROM `recruiting_analytics.candidates`
WHERE is_hired = TRUE
GROUP BY position_title
ORDER BY hires DESC;

-- Source performance
SELECT
  source_channel,
  COUNT(*) as applications,
  COUNT(CASE WHEN is_hired THEN 1 END) as hires,
  SAFE_DIVIDE(
    COUNT(CASE WHEN is_hired THEN 1 END),
    COUNT(*)
  ) * 100 as hire_rate_pct
FROM `recruiting_analytics.candidates`
GROUP BY source_channel
ORDER BY applications DESC;
```

## Key Metrics & KPIs

### Volume Metrics
- Total applications
- Applications by source
- Applications by position
- Applications by date

### Funnel Metrics
- Stage conversion rates
- Stage drop-off rates
- Average time in each stage
- Bottleneck identification

### Outcome Metrics
- Hire rate overall
- Hire rate by source
- Hire rate by position
- Rejection reasons

### Efficiency Metrics
- Time to hire
- Time to first interview
- Time from interview to offer
- Recruiter productivity

### Quality Metrics
- Offer acceptance rate
- Candidate satisfaction
- Hiring manager satisfaction
- 90-day retention rate

## Automation

### Scheduled Exports

```yaml
Schedule:
  - Daily: 2:00 AM - Incremental update (last 24h changes)
  - Weekly: Sunday 3:00 AM - Full refresh
  - Monthly: 1st of month - Historical archive
```

### Real-time Updates (Future)

```yaml
Triggers:
  - New candidate applied → Add to Sheets
  - Stage changed → Update candidate + add event
  - Interview completed → Add interview record
  - Candidate hired → Update status + metrics
```

## Data Quality

### Validation Rules

```python
# Required fields
assert candidate.id is not None
assert candidate.applied_date is not None
assert candidate.requisition_id is not None

# Data consistency
assert candidate.termination_date >= candidate.applied_date
assert candidate.days_in_process >= 0

# Valid values
assert candidate.status in ["inProgress", "terminated"]
assert candidate.current_stage in VALID_STAGES
```

### Error Handling

```python
# Missing data
if not candidate.email:
    candidate.email = "no-email@unknown.com"

# Invalid dates
if candidate.termination_date < candidate.applied_date:
    log_error(f"Invalid dates for candidate {candidate.id}")
    candidate.termination_date = None
```

## Privacy & Compliance

### Data Redaction

```python
# Redact PII for analytics
candidate.name = hash_name(candidate.name)  # Hash for counting
candidate.email = anonymize_email(candidate.email)
candidate.phone = None  # Remove entirely
```

### Access Control

- Limit Google Sheets access to authorized users
- Set BigQuery dataset permissions appropriately
- Log all data access
- Implement data retention policies

### GDPR Compliance

- Remove candidates after retention period
- Support right to deletion
- Maintain audit log
- Document data processing

## Troubleshooting

### Export Fails

**Issue**: Google Sheets API quota exceeded
**Solution**: Implement batching, reduce frequency, or use BigQuery

**Issue**: Data mismatch between HERP and Sheets
**Solution**: Run full refresh, check sync timestamps

### Data Quality Issues

**Issue**: Missing candidates in export
**Solution**: Check HERP API filters, verify permissions

**Issue**: Incorrect metrics
**Solution**: Validate calculation logic, check for null handling

---

## Invocation

```bash
# Full export
"Use recruiting analytics exporter to sync all HERP data to Google Sheets"

# Incremental update
"Export candidates updated in last 24 hours to Google Sheets"

# Specific analysis
"Export interview data for last quarter to prepare Looker Studio dashboard"
```

---

**Version**: 1.0.0
**Last Updated**: 2024-01-22
**Maintained By**: Recruiting Operations & Data Team
