# Lean UX & Data-Driven Feedback: HERP-Notion Integration

**Report Date:** 2026-01-24
**Prepared By:** Engineering HR Product Manager (Lean UX / Data-Driven Focus)
**Sprint:** Sprint 1 Post-Analysis
**Context:** Belong Inc - Japanese Engineering Recruiting Pipeline

---

## Executive Summary

This report re-analyzes the HERP-Notion Integration project through a **Lean UX**, **Lean Startup**, and **data-driven decision making** lens. While Sprint 1 delivered outstanding technical quality (240% velocity), several critical **assumptions remain unvalidated**, **key metrics are missing**, and the project shows early signs of **unsustainable team dynamics**.

**Critical Findings:**
- **Riskiest Assumption Unvalidated**: We assume engineers want this integration, but have no usage data
- **Missing Leading Indicators**: No metrics to predict recruiting success or developer productivity
- **Burnout Red Flags**: 240% overdelivery celebrated as success (red flag for Japanese work culture)
- **Build Trap**: Building features without validating user problems
- **Data Blindness**: Cannot answer "Is this working?" with quantitative evidence

**Immediate Actions Required:**
1. Validate core assumptions with actual users (recruiters, hiring managers) THIS WEEK
2. Instrument code to collect usage metrics BEFORE Sprint 2
3. Address team sustainability (Japanese 残業 culture intervention)
4. Define success metrics tied to business outcomes (not output)

---

## Section 1: Lean Experiments (Top 5)

### Experiment 1: Recruiter Productivity Hypothesis

**Hypothesis:**
"If we provide recruiters with real-time HERP-Notion sync, then time spent on manual data entry will decrease by 30% within 2 weeks of deployment."

**Riskiest Assumption:**
Recruiters actually spend significant time on manual data entry (not validated - we assumed this problem exists)

**MVP (Minimum Viable Experiment):**
1. **Week 1 (Before)**: Shadow 3 recruiters for 1 day each, time-study their workflow
   - Use gemba walk (現場 observation) approach from Kaizen
   - Track: time per candidate update, # of context switches, frustration points
   - Tools: Stopwatch + observation notes
   - Acceptance: If <20% of time is data entry, pivot hypothesis

2. **Week 2 (Baseline)**: Deploy sync to 1 recruiter (pilot user)
   - Daily check-in meetings (10 min standup)
   - Collect qualitative feedback
   - Track sync errors manually

3. **Week 3 (Measure)**: Repeat time-study with pilot user
   - Same methodology as Week 1
   - Calculate time savings
   - Interview for qualitative insights

**Success Metrics (Leading Indicators):**
- **Primary**: Time spent on data entry per candidate (target: -30%)
- **Secondary**: Candidate data freshness (HERP update → Notion visible, target: <5 min)
- **Lagging**: Recruiter NPS score (measure after 1 month)

**Failure Metrics (When to Pivot):**
- Time savings <10%: Pivot to different value proposition
- >5 errors/day reported: Fix quality before scaling
- Recruiter refuses to use after Week 1: Fundamental product-market fit issue

**Decision Criteria:**
- **Persevere** (scale to all recruiters): Time savings >30%, <1 error/day, positive qualitative feedback
- **Pivot** (change approach): Time savings 10-30%, recruiter feedback "nice to have"
- **Kill** (stop project): Time savings <10%, recruiter feedback "doesn't help", or technical quality too poor

**Duration:** 3 weeks
**Resources:** 1 recruiter (pilot), 1 PM for observation, engineering support for fixes

---

### Experiment 2: Engineering Hiring Velocity Hypothesis

**Hypothesis:**
"If we implement candidate analysis automation (Claude AI profiling), then time-to-hire for engineering positions will decrease by 15% within 1 quarter."

**Riskiest Assumption:**
Candidate evaluation is a bottleneck in hiring (vs. sourcing, interview scheduling, or offer negotiation)

**MVP (Minimum Viable Experiment):**
1. **Baseline (Week 1-2)**: Analyze last 3 months of hiring data from HERP
   - Extract: application date → offer date for 20 recent engineering hires
   - Calculate: median time-to-hire, variance, stage durations
   - Identify: which stage takes longest (書類選考? 1次面接? 最終面接?)
   - Tools: SQL query on HERP export OR manual HERP analysis

2. **Intervention (Week 3-6)**: Deploy AI analysis for NEW applicants only
   - Generate Claude profiling reports for all new engineering candidates
   - Track: hiring manager time reading resumes vs reading AI reports
   - Measure: days from application → 書類選考 decision

3. **Compare (Week 7)**: A/B comparison
   - Control group: 10 candidates hired during baseline (no AI)
   - Treatment group: 10 candidates processed with AI
   - Statistical test: t-test on time-to-hire

**Success Metrics (Leading Indicators):**
- **Primary**: Days from application → resume screening decision (target: -20%)
- **Secondary**: Hiring manager time per candidate review (target: -40%)
- **Quality Check**: Offer acceptance rate (must not decrease, target: >70%)

**Failure Metrics (When to Pivot):**
- No change in screening decision time: AI reports not being read
- Offer acceptance rate drops >10%: AI is filtering wrong candidates
- Hiring managers complain AI reports are inaccurate: Quality issue

**Decision Criteria:**
- **Persevere**: Screening time -20%, hiring managers report "helpful", no quality degradation
- **Pivot**: Screening time -5-15%, mixed feedback, try different AI approach or focus on different stage
- **Kill**: No improvement or negative impact on offer acceptance rate

**Duration:** 7 weeks (includes baseline)
**Resources:** Access to HERP analytics, Claude API budget, 2 hiring managers for feedback

---

### Experiment 3: Code Quality vs Velocity Tradeoff

**Hypothesis:**
"If we enforce strict code quality gates (linting, 80% coverage, type hints), then initial velocity will drop 20% but bug rate will decrease 50% within 4 weeks."

**Riskiest Assumption:**
Current code has significant technical debt that will cause production incidents (we have no production usage yet to validate this)

**MVP (Minimum Viable Experiment):**
1. **Week 1 (Baseline)**: Sprint 1 data
   - Velocity: 36 story points (with 5 unplanned tasks)
   - Bug count: 0 (no production usage)
   - Technical debt: qualitatively assessed as "medium" (30% duplication)

2. **Week 2-3 (Sprint 2 with gates)**: Implement minimal quality gates
   - Add: pytest runs in CI, black formatter (auto-fix)
   - Skip: 80% coverage requirement, strict type checking (too costly for MVP)
   - Measure: story points completed, time spent on "quality tax"

3. **Week 4 (Measure)**: Compare Sprint 1 vs Sprint 2
   - Velocity change
   - Developer sentiment survey (5-point Likert scale)
   - Code churn (lines changed per story point)

**Success Metrics (Leading Indicators):**
- **Primary**: Developer productivity (story points / day, accounting for quality time)
- **Secondary**: PR review time (faster with cleaner code)
- **Tertiary**: Developer happiness score (must be >3.5/5)

**Failure Metrics (When to Pivot):**
- Velocity drops >40%: Quality gates too strict
- Developer happiness <3.0/5: Team morale damage
- No bugs to prevent yet: Over-engineering for non-existent problem

**Decision Criteria:**
- **Persevere**: Velocity drop <20%, developer happiness >3.5/5, qualitative feedback positive
- **Pivot**: Velocity drop 20-40%, try lighter gates (just formatting, skip coverage)
- **Kill**: Velocity drop >40% or team morale crash, rollback all gates

**Duration:** 4 weeks
**Resources:** CI setup time (4 hours), ongoing enforcement

---

### Experiment 4: Japanese Market Recruiting Efficiency

**Hypothesis:**
"If we optimize for Japanese recruiting workflows (カジュアル面談 tracking, 社員紹介 source tracking), then recruiter satisfaction will increase by 30% and referral hire rate will increase by 15%."

**Riskiest Assumption:**
Current HERP-Notion integration doesn't adequately support Japanese recruiting practices (not validated with actual recruiters)

**MVP (Minimum Viable Experiment):**
1. **Week 1 (Discovery)**: Interview 3 Belong recruiters
   - Questions:
     - What's different about Japanese recruiting vs US/global?
     - What Notion fields do you wish existed?
     - Which HERP data points are most important to you?
     - Do you use カジュアル面談 differently than formal interviews?
   - Deliverable: List of Japan-specific requirements

2. **Week 2 (Prototype)**: Implement top 2 requested features
   - Example: Dedicated カジュアル面談 tracking, 社員紹介 source visualization
   - Deploy to 2 pilot recruiters

3. **Week 3-4 (Validate)**: Measure usage and impact
   - Track: # of times Japan-specific fields are updated
   - Interview: Are these features actually used? Any surprises?
   - Measure: Referral pipeline health (応募手法 = "社員紹介")

**Success Metrics (Leading Indicators):**
- **Primary**: Japan-specific feature usage rate (target: >50% of candidates have data)
- **Secondary**: Recruiter satisfaction survey (target: +30% on specific questions)
- **Tertiary**: Referral hire rate (応募手法 = "社員紹介" → 承諾, target: +15%)

**Failure Metrics (When to Pivot):**
- Feature usage <20%: Built wrong features, go back to discovery
- Recruiter feedback "doesn't help": Misunderstood problem
- Referral rate unchanged after 3 months: Not a real blocker

**Decision Criteria:**
- **Persevere**: Usage >50%, positive qualitative feedback, referral rate trending up
- **Pivot**: Usage 20-50%, mixed feedback, try different Japan-specific features
- **Kill**: Usage <20%, negative feedback, focus on global recruiting instead

**Duration:** 4 weeks
**Resources:** 3 recruiter interviews (3 hours total), 1 week dev time, Belong Slack for feedback

---

### Experiment 5: Team Sustainability (Burnout Prevention)

**Hypothesis:**
"If we cap sprint velocity at 15 story points and enforce 'no weekend work' policy, then team burnout risk will decrease (measured by eNPS) and sprint completion rate will increase to 100% (vs 90% plan adherence with scope creep)."

**Riskiest Assumption:**
240% overdelivery is unsustainable and indicates burnout risk (Japanese work culture context: 残業 normalization)

**MVP (Minimum Viable Experiment):**
1. **Week 1 (Baseline Survey)**: Anonymous team health survey
   - Questions (5-point Likert):
     - "I feel energized by my work" (burnout indicator)
     - "I have time for life outside work" (work-life balance)
     - "Sprint commitments feel achievable" (scope realism)
     - "I would recommend this team to a colleague" (eNPS proxy)
   - Current hypothesis: Scores will be 4/5 (high) due to Sprint 1 excitement, but not sustainable

2. **Week 2-5 (Sprint 2-3 with caps)**: Enforce sustainable pace
   - Rule 1: Max 15 story points per sprint (no exceptions)
   - Rule 2: No work on weekends (Slack monitoring)
   - Rule 3: Mid-sprint checkpoint to catch scope creep early
   - Rule 4: "Done is better than perfect" (counter Japanese perfectionism)

3. **Week 6 (Resurvey)**: Repeat team health survey
   - Compare: Sprint 1 baseline vs Sprint 2-3 sustainable pace
   - Hypothesis: Scores will remain 4/5 or improve to 4.5/5, indicating sustainability

**Success Metrics (Leading Indicators):**
- **Primary**: Team eNPS score (target: maintain >4.0/5 for 3 sprints)
- **Secondary**: Sprint plan adherence (target: 100%, zero scope creep)
- **Tertiary**: Weekend Slack activity (target: zero work messages)

**Failure Metrics (When to Pivot):**
- eNPS drops below 3.5/5: Team morale damaged, intervention needed
- Sprint completion rate <80%: Cap too restrictive, calibrate upward
- Stakeholder complaints about "slow delivery": Educate on sustainability value

**Decision Criteria:**
- **Persevere**: eNPS stable/improving, 100% plan adherence, team reports less stress
- **Pivot**: eNPS stable but stakeholders unhappy, negotiate 18-20 point cap
- **Kill** (emergency): eNPS crashes or team attrition, immediate intervention with HR

**Duration:** 6 weeks (2 sprints + surveys)
**Resources:** Survey tool (Google Forms), PM time for enforcement, HR support if needed

---

## Section 2: Data Gaps & Instrumentation

### 2.1 Critical Missing Metrics

**Engineering Productivity (DORA Metrics)**

| Metric | Current State | Target State | How to Measure | Why It Matters |
|--------|---------------|--------------|----------------|----------------|
| **Deployment Frequency** | Unknown (no CI/CD) | Daily | GitHub Actions workflow runs | Proxy for developer velocity |
| **Lead Time for Changes** | Unknown | <1 day (commit → deploy) | Git commit timestamp → production timestamp | Speed of value delivery |
| **Change Failure Rate** | Unknown (no production) | <5% | Rollback count / deployment count | Quality of releases |
| **Time to Restore Service** | Unknown | <1 hour | Incident start → resolution | Resilience/operational maturity |

**Current Gap:** ZERO DORA metrics instrumented. Cannot answer "Are we getting faster/better?"

**Action Item:**
- Sprint 2: Set up basic CI/CD with deployment tracking (Issue P1-001)
- Sprint 3: Implement error tracking (Sentry or equivalent)
- Sprint 4: Build DORA dashboard (Grafana or Notion page)

---

**Recruiting Metrics (Pipeline Health)**

| Metric | Current State | Target State | Data Source | Why It Matters |
|--------|---------------|--------------|-------------|----------------|
| **Time-to-Hire** | Unknown (HERP has data, not analyzed) | <30 days for engineering | HERP API: `appliedAt` → `hired` status | Recruiting efficiency |
| **Funnel Conversion Rate** | Unknown | 書類選考→1次: 40%, 1次→オファー: 30% | HERP step transitions | Identify bottleneck stages |
| **Candidate Experience Score** | Unknown (no surveys) | >4.0/5 | Post-interview survey | Employer brand impact |
| **Source Effectiveness** | Unknown | Referral: 15% of hires, LinkedIn: 10% | HERP `channel` field analysis | Optimize recruiting budget |
| **Offer Acceptance Rate** | Unknown | >70% | HERP: offers / acceptances | Competitiveness of offers |
| **Time in Stage** | Unknown | 書類選考: <5 days, 1次面接: <7 days | HERP step transition timestamps | Stage-specific optimization |
| **Recruiter Workload** | Unknown | <30 active candidates/recruiter | HERP assignments count | Capacity planning |
| **Engineering Specific**: Days to First Interview | Unknown | <10 days | `appliedAt` → first `contactType=interview` | Engineering talent competition |

**Current Gap:** 7,181 candidates in HERP, ZERO analytics on recruiting funnel

**Action Item:**
- Sprint 2: Export HERP data to BigQuery/CSV for analysis (1-day spike)
- Sprint 3: Build recruiting dashboard in Notion (2 days)
- Sprint 4: Automated weekly recruiting metrics email (1 day)

**SQL Query Example (for BigQuery):**
```sql
-- Time-to-hire for engineering positions
SELECT
  AVG(DATE_DIFF(hired_date, applied_date, DAY)) as avg_time_to_hire,
  PERCENTILE_CONT(DATE_DIFF(hired_date, applied_date, DAY), 0.5) as median_time_to_hire,
  COUNT(*) as total_hires
FROM herp_candidacies
WHERE status = 'hired'
  AND requisition_title LIKE '%Engineer%'
  AND applied_date >= '2025-01-01'
```

---

**Team Health Metrics (Japanese Work Culture Context)**

| Metric | Current State | Target State | How to Measure | Cultural Context |
|--------|---------------|--------------|----------------|------------------|
| **残業時間 (Overtime Hours)** | Unknown | <10 hours/month average | Git commit timestamps outside 9-18 JST | Japanese overtime culture risk |
| **離職率 (Attrition Rate)** | 0% (team just formed) | <10% annually | Team member departures | Retention health |
| **eNPS (Employee Net Promoter Score)** | Unknown (no baseline) | >40 (excellent) | Monthly pulse survey: "Recommend team? 0-10" | Team morale/satisfaction |
| **Sprint Burnout Score** | Unknown | <3/10 | Weekly question: "How burned out? 1-10" | Early warning system |
| **社内勉強会 Frequency** | Unknown | 2x/month | Calendar event tracking | Learning culture health |
| **Psychological Safety Score** | Unknown | >4.0/5 | Google's 5-question survey | Can team say "no" to scope creep? |
| **Work-Life Balance Score** | Unknown (assumed: compromised by 240% velocity) | >4.0/5 | Survey: "I have time for personal life" | Sustainability indicator |

**Current Gap:** Team delivered 240% of planned work, but we have ZERO data on whether this is sustainable or a burnout red flag

**Action Item:**
- **IMMEDIATE (This Week)**: Anonymous team health survey (Google Form, 5 min)
- Sprint 2: Weekly burnout check-in (1 question in Slack standup)
- Sprint 3: Implement overtime tracking (Git commits outside work hours)
- Monthly: Full team health survey (Amy Edmondson psychological safety framework)

**Cultural Context (Japan-Specific):**
- In Japanese work culture, 残業 (overtime) is often normalized/expected
- Team members may not report burnout until severe (がまん culture)
- 240% overdelivery could indicate inability to say "no" (not empowerment)
- Need to proactively monitor for unsustainable pace, not wait for team to ask for help

---

### 2.2 Data Sources & Collection Strategy

**HERP API Data (Already Available)**
- **What:** 7,181+ candidate records, contacts, evaluations, timeline
- **Access:** MCP server + Python scripts
- **Gap:** Data exists but not analyzed for insights
- **Action:**
  - Sprint 2: One-time export to BigQuery (4 hours)
  - Sprint 3: Automated daily sync HERP → BigQuery (2 days)
  - Sprint 4: Looker/Data Studio dashboards (1 week)

**Git Commit Data (Developer Activity)**
- **What:** Commit timestamps, author, files changed, commit message
- **Access:** `git log --all --format=json`
- **Gap:** Not tracked for productivity or work-life balance metrics
- **Action:**
  - Sprint 2: Git analytics script (1 day)
  - Track: commits outside 9-18 JST, weekend commits, commit frequency
  - Alert: If any team member has >10 commits/week outside work hours

**Notion Activity Logs (Usage Data)**
- **What:** Page views, edits, user activity
- **Access:** Notion API audit log (limited)
- **Gap:** Cannot tell if recruiters are actually using synced data
- **Action:**
  - Sprint 3: Implement custom tracking (append-only log in Notion DB)
  - Track: Last accessed timestamp for each candidate page
  - Metric: % of candidate pages viewed within 24h of HERP update

**Team Surveys (Qualitative + Quantitative)**
- **What:** eNPS, burnout, satisfaction, feature requests
- **Access:** Google Forms + Slack polls
- **Gap:** No baseline data, no regular pulse
- **Action:**
  - **THIS WEEK**: Sprint 1 retrospective survey (one-time)
  - **Ongoing**: Weekly 1-question pulse ("How was this week? 1-5")
  - **Monthly**: Full team health survey (10 questions, 5 min)

---

### 2.3 Dashboards & Visibility Needed

**Dashboard 1: Recruiting Funnel (Notion Database View)**
- **Audience:** Recruiters, hiring managers, CTO
- **Refresh:** Daily (automated sync)
- **Metrics:**
  - Total candidates by stage (書類選考, 1次, 2次, 最終, オファー)
  - Conversion rate by stage
  - Average days in each stage
  - Bottleneck identification (which stage has longest wait?)
  - Source effectiveness (社員紹介 vs エージェント vs 自社サイト)
- **Tools:** Notion database with calculated fields + formulas
- **Effort:** 2 days Sprint 3

**Dashboard 2: DORA Metrics (Grafana or Notion)**
- **Audience:** Engineering team, PM
- **Refresh:** Real-time (on every deployment)
- **Metrics:**
  - Deployment frequency (deployments/day)
  - Lead time (commit → deploy duration)
  - Change failure rate (% of deployments with rollback)
  - MTTR (incident → resolution time)
- **Tools:** GitHub Actions → Prometheus → Grafana OR simple Notion page
- **Effort:** 1 week Sprint 4 (after CI/CD is set up)

**Dashboard 3: Team Health (Notion or Google Sheets)**
- **Audience:** PM, team (anonymized aggregate only)
- **Refresh:** Weekly after survey
- **Metrics:**
  - eNPS trend (line chart over time)
  - Burnout score (line chart)
  - Overtime hours (bar chart by week)
  - Psychological safety score (current vs target)
  - Sprint velocity (actual vs planned, not as success metric but as sustainability check)
- **Tools:** Google Forms → Google Sheets → Notion embed
- **Effort:** 4 hours Sprint 2

---

### 2.4 Alerting & Thresholds

**When to Alert (SLOs)**

| Alert Condition | Severity | Action | Owner |
|----------------|----------|--------|-------|
| eNPS drops below 3.0/5 | **P0 Critical** | Emergency team meeting, HR escalation | PM + CTO |
| 3+ team members report burnout >7/10 | **P0 Critical** | Immediate workload reduction, 1:1s | PM |
| Recruiting time-to-hire >45 days for engineering | **P1 High** | Process review with recruiting team | PM + HR |
| CI/CD failure rate >20% | **P1 High** | Stop new features, fix quality | Architect + Backend |
| Zero HERP sync in 24 hours | **P2 Medium** | Check sync script, investigate | Backend Engineer |
| Weekend git commits from same person 3 weeks in row | **P2 Medium** | 1:1 check-in re: work-life balance | PM |
| Candidate page in Notion not viewed for 7 days after update | **P3 Low** | Recruiter training on new system | PM |

**Alert Channels:**
- **P0**: Slack @channel + email to CTO
- **P1**: Slack #engineering-alerts + PM email
- **P2**: Daily digest email
- **P3**: Weekly summary report

---

## Section 3: Recruiting Process ROI Analysis

### 3.1 Current State (Estimated from HERP Data)

**Assumptions (To Be Validated):**
- 7,181 total candidates in HERP (confirmed)
- ~200-300 active candidates at any time (estimate)
- ~30-40 hires/year across all departments (based on "33 open positions")
- Engineering: ~15-20 hires/year (estimate)

**Time-to-Hire Funnel (Engineering, Estimated)**

| Stage | Median Days | Drop-off Rate | Candidates Remaining (per 100 applicants) |
|-------|-------------|---------------|-------------------------------------------|
| 応募 → 書類選考 | 3 days | 60% | 100 → 40 |
| 書類選考 → カジュアル面談 | 5 days | 30% | 40 → 28 |
| カジュアル面談 → 1次選考 | 7 days | 25% | 28 → 21 |
| 1次選考 → 2次選考 | 7 days | 40% | 21 → 12 |
| 2次選考 → 最終面接 | 10 days | 30% | 12 → 8 |
| 最終面接 → オファー | 5 days | 20% | 8 → 6 |
| オファー → 承諾 | 7 days | 30% | 6 → 4 |
| **Total** | **44 days** | **96% drop-off** | **4 hires per 100 applicants** |

**Current Pain Points (Hypotheses to Validate):**
1. **Manual Data Entry**: Recruiters spend 20-30% time copying data between HERP and Notion
2. **Context Switching**: Average 10+ context switches per candidate update
3. **Stale Data**: Notion candidate data lags HERP by 1-3 days
4. **Missing Insights**: No visibility into bottleneck stages
5. **Inconsistent Updates**: Some candidates fall through cracks

**Effort per Candidate (Recruiter Time, Estimated):**
- Resume screening: 15 min
- Schedule 1st interview: 20 min (email back-and-forth)
- Interview coordination (2-3 rounds): 40 min
- Data entry/updates: 15 min (THIS IS WHAT SYNC SOLVES)
- Reference checks: 30 min
- Offer preparation: 20 min
- **Total**: ~2.5 hours per candidate through full pipeline

**Cost per Hire (Japan Market, 2026):**
- Recruiter time: ~20 hours @ ¥5,000/hour = ¥100,000
- Interview time (engineers): ~5 hours @ ¥8,000/hour = ¥40,000
- Agency fees (if used): 30-35% of annual salary = ¥1,500,000 - ¥2,000,000
- **Total**: ¥1,640,000 - ¥2,140,000 per engineering hire

---

### 3.2 ROI of HERP-Notion Sync (Projected)

**Value Proposition Hypotheses:**

**Hypothesis 1: Reduce Data Entry Time**
- Current: 15 min/candidate × 300 active candidates = 75 hours/month
- With Sync: 2 min/candidate (just verification) × 300 = 10 hours/month
- **Savings**: 65 hours/month recruiter time
- **Value**: 65h × ¥5,000/h = ¥325,000/month = ¥3,900,000/year
- **Confidence**: Medium (depends on actual recruiter workflow validation)

**Hypothesis 2: Reduce Time-to-Hire**
- Current: 44 days median
- With Sync: 40 days (10% improvement from faster data visibility)
- **Impact**: 4 days × 20 engineering hires/year = 80 candidate-days saved
- **Value**: Faster hires = less revenue loss from unfilled positions
  - Unfilled engineering role costs ~¥500,000/month in lost productivity
  - 4 days saved = 0.13 months × ¥500,000 = ¥65,000 per hire
  - 20 hires/year × ¥65,000 = ¥1,300,000/year
- **Confidence**: Low (time-to-hire improvement not directly caused by sync)

**Hypothesis 3: Increase Offer Acceptance Rate**
- Current: ~70% (estimate)
- With Better Candidate Experience: 75% (+5 percentage points)
- **Impact**: 5% more offers accepted = 1 extra hire per 20 offers
- **Value**: Avoid re-recruiting cost = ¥2,000,000 (agency fee for 1 hire)
- **Confidence**: Very Low (sync unlikely to improve candidate experience directly)

**Total ROI (Conservative Estimate):**
- **Annual Value**: ¥3,900,000 (time savings only, ignoring questionable indirect benefits)
- **Development Cost**:
  - Sprint 1-2: 36 + 15 = 51 story points × 4 hours/point × 4 people × ¥6,000/hour = ¥4,896,000
  - Ongoing maintenance: ¥500,000/year
- **ROI**: (¥3,900,000 - ¥500,000) / ¥4,896,000 = **69% first-year ROI**
- **Payback Period**: 14 months

**CRITICAL CAVEAT:**
This ROI assumes recruiters actually spend 15 min/candidate on manual data entry. **This is unvalidated**. If actual time is <5 min/candidate, ROI becomes negative.

**ACTION REQUIRED**: Validate time savings assumption via time-study (Experiment 1) before continuing development.

---

### 3.3 Quick Wins (Automation Opportunities)

**1. Auto-email on Stage Change (Candidate Experience)**
- **What**: When HERP status changes (書類選考 → 1次選考), auto-send email to candidate
- **Value**: Reduce recruiter manual email time, improve candidate experience
- **Effort**: 1 day (HERP webhook → email template → SendGrid)
- **ROI**: 10 min/candidate × 300 candidates/year = 50 hours saved = ¥250,000/year
- **Priority**: High (quick win, high impact)

**2. Slack Notification for Interview Scheduling**
- **What**: When interview scheduled in HERP, notify interviewer in Slack
- **Value**: Reduce calendar conflicts, improve interviewer preparation
- **Effort**: 4 hours (HERP contact created → Slack webhook)
- **ROI**: Qualitative (better interviewer experience), prevents double-booking
- **Priority**: Medium (nice-to-have, low effort)

**3. Automated Weekly Recruiting Report**
- **What**: Every Monday, email recruiting team with funnel metrics from HERP
- **Value**: Visibility into pipeline health, proactive bottleneck identification
- **Effort**: 1 day (SQL query + email template + cron job)
- **ROI**: Improve recruiter decision-making (hard to quantify)
- **Priority**: High (data-driven culture building)

**4. Duplicate Candidate Detection**
- **What**: Flag when same email applies to multiple positions
- **Value**: Prevent awkward duplicate outreach, save recruiter time
- **Effort**: 2 hours (Notion database query + visual indicator)
- **ROI**: Prevent 5-10 embarrassing emails/year (qualitative)
- **Priority**: Low (rare edge case)

---

### 3.4 Strategic Improvements (Longer-term)

**1. AI-Powered Candidate Matching**
- **What**: Claude analyzes job description + candidate resume, suggests fit score
- **Value**: Reduce resume screening time from 15 min → 5 min per candidate
- **Effort**: 2 weeks (already partially built in `analyze-candidate-profile.py`)
- **ROI**: 10 min × 300 candidates/year = 50 hours = ¥250,000/year
- **Risk**: AI bias risk (must validate against human screening decisions)
- **Priority**: Medium (after validating recruiter workflow)

**2. Interview Scheduling Automation (Calendly-like)**
- **What**: Candidate self-schedules interviews based on interviewer availability
- **Value**: Reduce scheduling coordination time from 20 min → 2 min
- **Effort**: 3 weeks (complex, requires calendar API integration)
- **ROI**: 18 min × 300 candidates × ¥5,000/hour = ¥450,000/year
- **Priority**: High (major pain point in Japanese recruiting)

**3. Reference Check Automation**
- **What**: Auto-send reference check forms, collect responses, summarize for hiring manager
- **Value**: Reduce reference check time from 30 min → 10 min
- **Effort**: 1 week (form builder + email automation)
- **ROI**: 20 min × 100 reference checks/year = ¥166,000/year
- **Priority**: Low (fewer reference checks needed in Japan vs US)

---

## Section 4: Kaizen Action Items

### 4.1 This Sprint (Week 1) - 継続的改善

**Gemba Walk (現場 Observation) - Go See for Yourself**

Japanese proverb: "現場に行け" (Go to the gemba - the actual place)

**Action**: Shadow 1 recruiter for 1 full day THIS WEEK
- **Who**: PM (this report's author)
- **What**: Observe actual workflow: HERP → decisions → Notion → communication
- **Questions to Answer**:
  1. How much time is REALLY spent on manual data entry? (vs our assumption)
  2. What causes the most frustration? (may not be what we think)
  3. Where do candidates "fall through cracks"? (gaps in process)
  4. What's the actual context-switching cost? (number + cognitive load)
- **Deliverable**: 1-page observation report with time-study data
- **Date**: By end of Sprint 1 (January 31, 2026)

**5 Whys - Root Cause Analysis of Sprint 1 Scope Creep**

**Problem**: Delivered 36 story points vs 15 planned (240% overdelivery)

**Why 1**: Why did we deliver 240%?
→ Test Engineer and Technical Writer completed assigned work quickly and started unplanned tasks

**Why 2**: Why did they start unplanned tasks without approval?
→ No clear protocol for "what to do when you finish early"

**Why 3**: Why was there no protocol?
→ First sprint, process not fully defined, PM assumed team would ask for next task

**Why 4**: Why did team not ask for next task?
→ Japanese work culture: initiative is valued, asking "what next?" feels like lacking autonomy

**Why 5**: Why is this a problem?
→ **ROOT CAUSE**: Unsustainable pace + unpredictability makes planning impossible + burnout risk

**Countermeasure**:
1. **Process Fix**: "Done with assigned work? Slack PM before starting new work" (added to DoD)
2. **Cultural Alignment**: Explain in retrospective: "Asking is not weakness, it's professional collaboration"
3. **Mid-sprint Checkpoint**: Day 3-4 standup specifically checks for scope drift
4. **Capacity Buffer**: Plan for 12 story points in Sprint 2, reserve 3 points for "surprises"

---

**PDCA Cycle - Sprint 1 Learnings**

**Plan (Sprint 1):**
- Goal: Architecture & Foundation
- Capacity: 15 story points
- Team: 4 agents (Architect, Backend, Test, Writer)

**Do (Sprint 1 Execution):**
- Delivered: 36 story points (240%)
- Quality: Excellent (77 E2E tests, comprehensive docs)
- Process: Scope creep detected (5 unplanned tasks)

**Check (Sprint 1 Analysis):**
- ✅ Architecture solid (domain classification, testing infrastructure)
- ⚠️ Core utilities incomplete (US-4 still in progress)
- ❌ Unsustainable velocity (burnout risk)
- ❌ Planning accuracy poor (15 vs 36)

**Act (Sprint 2 Adjustments):**
1. **Adjust Capacity**: 15 story points (realistic), do NOT plan 36
2. **Complete Blockers**: US-4 is P0 priority
3. **Enforce Process**: Mid-sprint checkpoint, no unapproved work
4. **Measure Burnout**: Weekly pulse survey starting Sprint 2

**Next PDCA Cycle**: Sprint 2 (repeat process, refine based on data)

---

**Hansei (反省) - Reflection Without Blame**

In Japanese business culture, hansei (反省) is reflection focused on learning, not punishment.

**Sprint 1 Reflection Questions for Team:**

1. **What went well?**
   - Test infrastructure exceeded expectations
   - Documentation is comprehensive
   - Team collaboration excellent

2. **What could be improved?**
   - Scope control (5 unplanned tasks)
   - Communication about capacity (should have flagged early completion)
   - Core utilities completion (US-4 delay)

3. **What did we learn?**
   - Initial estimates were too conservative (we can do more than 15 points)
   - Quality is achievable without sacrificing speed (good news!)
   - Need mid-sprint check-ins to catch drift
   - Team is highly motivated (both strength and risk)

4. **What will we change?**
   - Realistic capacity: 15-18 points (not 36)
   - Mandatory mid-sprint checkpoint
   - "Ask before new work" protocol
   - Weekly burnout pulse check

**Format**: 30-minute retrospective meeting, anonymous input via Google Form, then discussion

**Japanese Cultural Note**: Emphasize "learning" not "blame" (failure is learning opportunity, very Kaizen)

---

### 4.2 Next Sprint (Sprint 2) - 2 Weeks

**Process Experiments (2-week PDCA cycle)**

**Experiment 1: Mid-Sprint Checkpoint (Day 3-4)**
- **What**: 15-minute standup on Wednesday, ask each team member:
  - "Will you finish assigned work by Friday?"
  - "Are you blocked?"
  - "Are you working on anything not in the sprint backlog?"
- **Why**: Catch scope creep early, adjust before it's too late
- **Success Criteria**: Zero scope creep in Sprint 2
- **If Fails**: Try daily written check-ins instead of Wednesday meeting

**Experiment 2: Definition of Ready Enforcement**
- **What**: No user story enters sprint unless it meets DoR (see IMPROVE-PROC-005 from feedback report)
- **DoR Checklist**:
  - [ ] Acceptance criteria clearly defined
  - [ ] Dependencies identified and resolved
  - [ ] Story points estimated with planning poker
  - [ ] Technical approach discussed
  - [ ] Test scenarios outlined
  - [ ] No blockers
  - [ ] Product Owner approval
- **Why**: Reduce mid-sprint clarifications, improve completion rate
- **Success Criteria**: Zero stories "waiting for clarification" during sprint
- **If Fails**: Identify which DoR criteria are too strict, refine

---

### 4.3 This Quarter (3 Months) - Strategic Initiative

**Strategic Initiative: Recruiting Process Kaizen**

**Goal**: Reduce engineering time-to-hire from 44 days → 35 days (20% improvement) by Q2 2026

**Approach**: Identify and eliminate waste (Muda - 無駄) in recruiting process

**7 Wastes (Muda) in Recruiting:**
1. **Transport**: Handoffs between recruiters, hiring managers, HR
2. **Inventory**: Candidates stuck in "書類選考" for weeks
3. **Motion**: Context switching between HERP, Notion, Email, Slack
4. **Waiting**: Delays in interview scheduling
5. **Overprocessing**: Duplicate data entry (HERP + Notion)
6. **Overproduction**: Too many interview rounds (overkill?)
7. **Defects**: Mis-hires, candidates declining offers

**Kaizen Activities:**
- **Month 1**: Value stream mapping (apply Lean manufacturing to recruiting)
  - Map every step: 応募 → 承諾
  - Identify non-value-added activities
  - Measure time in each stage
- **Month 2**: Eliminate top 3 wastes
  - Example: Automate interview scheduling (eliminate "Waiting")
  - Example: HERP-Notion sync (eliminate "Overprocessing")
  - Example: Reduce interview rounds from 4 → 3 if data supports (eliminate "Overproduction")
- **Month 3**: Measure improvement
  - Compare: Q1 2026 time-to-hire vs Q2 2026
  - Statistical significance test
  - Celebrate wins, identify next waste to eliminate

**Success Criteria**:
- Engineering time-to-hire <35 days (median)
- Offer acceptance rate >75%
- Recruiter satisfaction +20%

---

### 4.4 Reflection (Hansei) - What Did We Learn from 240% Overdelivery?

**Positive Learnings:**
1. Team is **highly capable** (can deliver 2.4x planned work)
2. **Quality doesn't suffer at high velocity** (77 tests, all passing)
3. **Motivation is high** (team excited about project)
4. **Collaboration works** (no blockers, smooth coordination)

**Concerns (Potential Red Flags):**
1. **Unsustainable pace**: Can team maintain this for 6 months? Unlikely.
2. **Planning inaccuracy**: If estimates are off by 140%, we can't predict delivery dates
3. **Scope creep normalization**: Sets precedent for "it's okay to work on unapproved tasks"
4. **Burnout risk**: In Japanese work culture, overwork is often normalized until crisis

**Japanese Cultural Context (重要):**
- In Japan, 残業 (overtime) and がんばる (working hard) are often praised
- Team may not report stress until burnout is severe
- "No" is difficult to say (especially to authority)
- **PM responsibility**: Protect team from themselves, enforce sustainable pace

**What to Watch For (Early Warning Signs):**
- [ ] Weekend git commits
- [ ] Late-night Slack messages (after 22:00 JST)
- [ ] Team members skipping lunch
- [ ] Declining code review quality
- [ ] Short/terse communication (vs usual politeness)
- [ ] Physical signs: tired eyes, slouching posture (if co-located)

**Countermeasure**:
- Weekly anonymous burnout check: "How tired are you? 1-10"
- If average >6/10: Mandatory day off + scope reduction
- PM models work-life balance: No Slack after 18:00, no weekend work

---

## Section 5: Team Health & Sustainability

### 5.1 Burnout Risk Assessment

**Current Status: 🟡 YELLOW (Moderate Risk)**

**Evidence of Risk:**
1. ✅ 240% velocity (much higher than planned)
2. ✅ 5 unplanned tasks completed (scope creep)
3. ✅ No explicit "stop working" signals from PM
4. ❓ Unknown: Actual hours worked (no time tracking)
5. ❓ Unknown: Team sentiment (no burnout survey yet)

**Japanese Work Culture Context:**

In Japan, there's a concept called "karoshi" (過労死 - death from overwork). While extreme, it illustrates how overwork is normalized:
- 残業 (overtime) is often expected, even unpaid
- がんばる (trying hard/perseverance) is praised over work-life balance
- Saying "I can't" or "I need rest" is seen as weak
- Team harmony (和) means not complaining even when struggling

**Risk**: Team delivered 240% not because it was easy, but because they felt they **should** (cultural pressure)

**Validation Needed:**
- Were team members working weekends? (Check git commits)
- Were team members working late nights? (Check Slack activity, git commits)
- Did team feel empowered to say "this is too much"? (Check psychological safety)

---

### 5.2 Are We Celebrating or Should We Be Concerned?

**The Paradox**: 240% velocity is both impressive AND concerning

**When Overdelivery is GOOD:**
- Team found ways to work smarter (automation, templates)
- Initial estimates were overly conservative (learning curve)
- Team is genuinely excited and energized (not forced)
- Quality remains high (tests pass, documentation complete)

**When Overdelivery is BAD:**
- Team worked unsustainable hours (burnout ahead)
- Team felt pressure to "prove themselves" (first sprint)
- Scope creep means we can't plan reliably
- Sets unrealistic expectations for future sprints

**Current Assessment: Likely BOTH**
- Good: Team is capable, quality is high
- Bad: Sustainability unknown, planning broken, cultural pressure risks

**Action Required:**
1. **IMMEDIATE**: Survey team on Sprint 1 experience
   - "Did you work overtime? How many hours?"
   - "Did you feel pressured to work beyond sprint commitment?"
   - "Do you feel energized or exhausted after Sprint 1?"
   - "Is this pace sustainable for 6 months?"
2. **Sprint 2**: Enforce 15-point cap, monitor for weekend/evening work
3. **Retrospective**: Celebrate quality, discuss sustainability openly

---

### 5.3 Sustainable Pace (Recommended)

**Target Velocity: 15-18 Story Points**
- Based on Sprint 1 data, team CAN do 36 points
- But SHOULD do 15-18 for sustainability
- Reserve 20% capacity for unknowns (learning, blockers, life events)

**Work Hours Guidelines:**
- **Core Hours**: 10:00-16:00 JST (6 hours focused work)
- **Flexible**: 9:00-10:00 and 16:00-18:00 (meetings, async work)
- **Off-Limits**: Weekends, after 20:00 JST
- **Exception**: Production incidents only (should be rare with good process)

**Slack Activity Policy:**
- No expectation of response after 18:00 JST
- No expectation of response on weekends
- PM models this behavior (do not send Slack after hours)
- Use Slack "schedule send" for messages drafted after hours

**Git Commit Monitoring:**
```bash
# Check for commits outside work hours (9-18 JST)
git log --all --format="%h %ai %an" | awk '{
  hour = substr($3, 1, 2);
  if (hour < 9 || hour >= 18) print $0;
}'
```
- Run weekly, report to PM
- If >10% of commits outside work hours: Intervention needed

---

### 5.4 Psychological Safety (Can Team Say "No"?)

**Google's Psychological Safety Framework (5 Questions):**

Survey team monthly (5-point Likert scale: Strongly Disagree → Strongly Agree):

1. "If you make a mistake on this team, it is not held against you."
   - **Target**: >4.0/5 (safe to fail, iterate, learn)

2. "Members of this team are able to bring up problems and tough issues."
   - **Target**: >4.0/5 (can say "this sprint is too much")

3. "People on this team sometimes reject others for being different."
   - **Target**: <2.0/5 (diversity welcome)

4. "It is safe to take a risk on this team."
   - **Target**: >4.0/5 (can try new approaches)

5. "It is difficult to ask other members of this team for help."
   - **Target**: <2.0/5 (help-seeking encouraged)

**Japanese Culture Adjustment:**
- In Japan, asking for help can be seen as "burdening others" (迷惑)
- "No" is indirect ("It might be difficult" = "No")
- Team may agree to unrealistic scope to maintain harmony (和)

**PM Actions to Build Psychological Safety:**
1. **Model Vulnerability**: PM shares own mistakes/failures
2. **Reward Honesty**: Praise team member who flags overcommitment early
3. **No Blame Postmortems**: When issues occur, focus on system/process, not individuals
4. **Explicitly Invite "No"**: "It's okay to say this is too much"
5. **Track Metrics**: Monitor psychological safety score, intervene if drops below 3.5/5

---

### 5.5 Work-Life Balance Score (Japanese Context)

**Survey Question** (monthly):
"I have adequate time for my personal life outside of work." (1-5 scale)

**Target**: >4.0/5 average across team

**Japanese Context Challenges:**
- Long commutes (1-2 hours each way common in Tokyo)
- Expectation to attend 飲み会 (after-work drinking, unofficial mandatory)
- Limited vacation usage (even when entitled)
- Pressure to arrive early, leave late

**Work-Life Balance Red Flags:**
- Survey score <3.5/5
- Team member consistently first to arrive, last to leave
- Vacation days unused (Belong offers 16-20 PTO days)
- Sick days never used (may indicate 出勤主義 - presenteeism)

**Belong-Specific Strengths** (from CLAUDE.md):
- ✅ Flex-time system
- ✅ Remote work options
- ✅ Hybrid work model
- ✅ Average age ~31 (younger, more open to work-life balance)

**Actions to Support Work-Life Balance:**
1. **Encourage PTO Usage**: PM tracks team PTO, reminds if 0 days used by Q2
2. **No-Meeting Fridays**: Reserve Fridays for focused work, no meetings after 15:00
3. **Mandatory Breaks**: Encourage lunch breaks away from desk
4. **Celebrate Life Events**: Team member got married? Send congratulations, give gift
5. **Model Behavior**: PM takes PTO, shares weekend activities, leaves on time

---

### 5.6 Monthly Team Health Check Template

**Team Health Survey (5 minutes, anonymous Google Form)**

**Section 1: Sprint Health (1-5 scale)**
1. Sprint commitments felt achievable
2. I had time to do quality work (not rushed)
3. I felt supported by team members
4. I understood what was expected of me

**Section 2: Burnout & Workload (1-10 scale)**
5. How energized do you feel? (1=exhausted, 10=energized)
6. How much overtime did you work this sprint? (0-10+ hours)
7. Did you work on weekends? (Yes/No + hours)

**Section 3: Psychological Safety (1-5 scale)**
8. I feel safe raising concerns with the team
9. It's okay to make mistakes on this team
10. I can ask for help when I need it

**Section 4: Work-Life Balance (1-5 scale)**
11. I have time for personal life outside work
12. I take adequate breaks during the day
13. I feel refreshed at the start of each sprint

**Section 5: Open Feedback**
14. What's one thing we should START doing?
15. What's one thing we should STOP doing?
16. What's one thing we should CONTINUE doing?

**Results Dashboard** (aggregated, anonymized):
- Share with team as Notion page
- Track trends over time (line charts)
- Discuss in retrospectives
- Alert if any metric drops >20% month-over-month

---

## Section 6: Critical Questions to Answer

### Q1: What's the #1 Riskiest Assumption About Our Development Process?

**Answer**: "Recruiters want this integration and will use it actively."

**Why This is Risky:**
- We've built 36 story points worth of work without validating actual user need
- No user interviews, no time studies, no prototype validation
- All assumptions about "pain points" are from engineering perspective, not user research
- If recruiters don't use it, entire project is waste

**How to Validate:**
1. **THIS WEEK**: Interview 3 recruiters (30 min each)
   - "Walk me through your current workflow"
   - "What's the most frustrating part of your job?"
   - "If I gave you perfect HERP-Notion sync, what would change?"
2. **Sprint 2**: Deploy to 1 pilot recruiter, observe usage for 1 week
3. **Sprint 3**: Measure: % of candidate pages accessed within 24h of HERP update

**De-Risk Strategies:**
- **If recruiters don't care**: Pivot to different users (hiring managers? candidates?)
- **If workflow doesn't match our assumptions**: Rebuild with correct mental model
- **If Notion is wrong tool**: Consider different reporting layer (dashboard, Slack bot, email)

---

### Q2: What Metric Would Best Predict Recruiting Success?

**Answer**: "Days from application to first interview" (応募 → 1次選考)

**Why This is a Leading Indicator:**
- **Candidate Experience**: Fast response = better candidate experience = higher offer acceptance
- **Competitive Advantage**: Tech talent is competed for, faster = more likely to win
- **Bottleneck Indicator**: If this is slow, likely indicates resume screening bottleneck
- **Actionable**: Recruiter can directly control this (vs later stages with interviewer dependencies)

**Target**: <10 days (currently ~15 days estimated)

**How to Measure:**
```sql
SELECT
  candidacy_id,
  applied_at,
  MIN(contact.scheduled_at) as first_interview,
  DATE_DIFF(MIN(contact.scheduled_at), applied_at, DAY) as days_to_first_interview
FROM herp_candidacies
JOIN herp_contacts ON candidacy_id = contacts.candidacy_id
WHERE contact_type IN ('casual_interview', 'technical_interview', 'first_interview')
  AND applied_at >= '2025-01-01'
GROUP BY candidacy_id
```

**Dashboard**: Notion page with:
- Median days to first interview (overall)
- By job posting (which positions are slow?)
- By recruiter (who needs support?)
- By source (社員紹介 faster than エージェント?)
- Trend over time (are we improving?)

**Why NOT "Time-to-Hire"?**
- Time-to-hire (応募 → 承諾) is lagging indicator, too many confounding factors
- Days to first interview is more directly actionable
- Correlates with offer acceptance rate (faster = better candidate experience)

---

### Q3: How Do We Know if Engineers Are Happy/Productive?

**Answer**: We don't. We need multiple metrics, not just velocity.

**Proposed Metrics (Multi-Dimensional):**

**Dimension 1: Output (What We Build)**
- Story points per sprint (current: 36, target: 15-18)
- PR merge rate (PRs merged / PRs opened)
- Code churn (lines changed / lines added, <30% is good)

**Dimension 2: Quality (How Well We Build)**
- Bug escape rate (bugs in production / features shipped)
- Test coverage (target: >80%)
- Code review cycle time (PR opened → merged, target: <24h)

**Dimension 3: Learning (How Much We Grow)**
- 社内勉強会 participation (target: 2x/month)
- Tech conference attendance
- New skills learned (self-reported quarterly)

**Dimension 4: Happiness (How We Feel)**
- eNPS score (target: >40)
- Burnout score (target: <3/10)
- Psychological safety score (target: >4/5)

**Dimension 5: Impact (Value We Deliver)**
- User adoption (% of recruiters using sync)
- Time savings (recruiter hours saved/month)
- Recruiting metrics improvement (time-to-hire reduction)

**Dashboard**: Notion page "Engineering Health" with:
- Overall health score (average of 5 dimensions)
- Trend over time (improving or degrading?)
- Red flags (any dimension <threshold?)

**Action Thresholds:**
- Overall health <3.5/5: Emergency team intervention
- Any dimension <2.5/5: Focused improvement plan
- All dimensions >4.0/5: Celebrate success, maintain

---

### Q4: What Experiment Could We Run THIS WEEK?

**Answer**: Validate recruiter workflow assumptions (Gemba walk)

**Experiment: Recruiter Workflow Time Study**

**Hypothesis**: "Recruiters spend >20% of time on manual HERP → Notion data entry"

**Method** (1 day, this week):
1. **Preparation** (1 hour):
   - Recruit 1 volunteer recruiter from Belong
   - Explain: "I'll shadow you for 1 day to understand your workflow, not to judge performance"
   - Prepare observation template (time-study spreadsheet)

2. **Observation** (8 hours):
   - Sit with recruiter (co-located or Zoom screenshare)
   - Time-study every activity in 15-minute increments:
     - Resume screening
     - HERP data entry
     - Notion updates
     - Email to candidates
     - Interview scheduling
     - Meetings
     - Slack communication
     - Breaks
   - Note: Frustration moments, context switches, "ugh" moments

3. **Analysis** (2 hours):
   - Calculate % time on each activity
   - Identify top 3 time sinks
   - Identify top 3 frustration points
   - Map to current HERP-Notion sync value proposition

4. **Decision** (1 hour):
   - If data entry >20% of time: Validate hypothesis, continue development
   - If data entry <10% of time: Pivot, focus on different pain point
   - If different bottleneck identified: Adjust product roadmap

**Cost**: 12 hours (1 PM day + 1 recruiter day)
**Value**: Prevent wasted development on wrong problem
**Risk Mitigation**: If assumptions are wrong, catch early (Sprint 1 vs Sprint 10)

---

### Q5: Are We Building the Right Thing or Just Building Things Right?

**Current State**: We're building things RIGHT (high quality), but we don't know if they're the RIGHT things

**Evidence**:
- ✅ Excellent code quality (77 tests, comprehensive docs)
- ✅ Solid architecture (DDD, clean boundaries)
- ❌ No user validation (zero recruiter interviews)
- ❌ No usage metrics (can't tell if anyone uses it)
- ❌ No business metrics tied to features (are we impacting time-to-hire?)

**Build Trap Symptoms** (Escaping the Build Trap by Melissa Perri):
1. Celebrating velocity/output instead of outcomes ✅ (we did this)
2. Long feature lists without user validation ✅ (17 scripts, 31 improvements)
3. No clear success metrics tied to business value ✅ (no ROI calculation)
4. "We'll know it when we ship it" mentality ✅ (no early feedback loops)

**How to Shift from Output → Outcome Focus:**

**Before Sprint 2 (This Week):**
- [ ] Define success metrics for HERP-Notion sync (not "features shipped")
  - Example: "30% reduction in recruiter data entry time"
  - Example: "85% of recruiters actively use sync within 1 month"
- [ ] Interview 3 recruiters to validate assumptions
- [ ] Create "Experiment Board" (hypothesis → test → learn → decide)

**During Sprint 2:**
- [ ] Deploy to 1 pilot recruiter, collect daily feedback
- [ ] Instrument usage tracking (page views, sync runs, errors)
- [ ] Weekly check-in: "Are we solving the right problem?"

**Sprint 2 Definition of Done Update:**
- Add: "Success metrics defined for this user story"
- Add: "User feedback collected (if user-facing feature)"
- Add: "Outcome measured (if possible, qualitative if not quantitative)"

**Mindset Shift:**
- ❌ Old: "We delivered 36 story points!" (output)
- ✅ New: "We saved recruiters 20 hours/week!" (outcome)

---

## Section 7: Recommendations Summary

### Immediate Actions (This Week)

| # | Action | Owner | Effort | Impact | Urgency |
|---|--------|-------|--------|--------|---------|
| 1 | **Gemba Walk**: Shadow 1 recruiter for 1 day | PM | 12h | Validate assumptions | P0 Critical |
| 2 | **Team Health Survey**: Sprint 1 experience + burnout check | PM | 2h | Prevent burnout | P0 Critical |
| 3 | **Interview 3 Recruiters**: Validate HERP-Notion pain points | PM | 3h | Validate product-market fit | P0 Critical |
| 4 | **Define Success Metrics**: What does "success" mean? | PM + Team | 2h | Focus on outcomes | P1 High |
| 5 | **Fix Hardcoded API Key**: Security issue (ISSUE-P1-006) | Backend | 30m | Security | P1 High |

**Total Effort**: ~20 hours (2.5 days)
**Why Critical**: Without these, we risk building wrong thing OR burning out team

---

### Sprint 2 Actions (2 Weeks)

**Process:**
- [ ] Enforce 15-point velocity cap (no overdelivery)
- [ ] Mid-sprint checkpoint (Day 3-4, catch scope creep)
- [ ] Weekly burnout pulse (1-question survey)
- [ ] Complete US-4 (core utilities extraction) as P0

**Instrumentation:**
- [ ] Set up basic CI/CD (GitHub Actions)
- [ ] Add usage tracking to sync scripts (log to Notion DB)
- [ ] Create DORA metrics dashboard (simple version)
- [ ] Git commit time analysis (detect overtime)

**User Validation:**
- [ ] Deploy sync to 1 pilot recruiter
- [ ] Daily check-in meetings (10 min)
- [ ] Collect qualitative feedback
- [ ] Measure: time saved, errors encountered, satisfaction

---

### This Quarter Actions (3 Months)

**Metrics & Data:**
- [ ] Export HERP data to BigQuery for analytics
- [ ] Build recruiting funnel dashboard (Notion or Looker)
- [ ] Implement automated weekly recruiting report
- [ ] Track DORA metrics (deployment frequency, lead time, MTTR, change failure rate)

**Team Health:**
- [ ] Monthly team health survey (eNPS, burnout, psychological safety)
- [ ] Quarterly 1:1s with each team member (not just standups)
- [ ] Track 残業時間 (overtime), intervene if >10h/month
- [ ] Celebrate work-life balance (PTO usage, hobbies, family time)

**Product Validation:**
- [ ] Scale sync to all recruiters (if pilot successful)
- [ ] A/B test AI candidate analysis (with vs without)
- [ ] Measure recruiting outcomes (time-to-hire, offer acceptance rate)
- [ ] Pivot or persevere based on data

---

## Appendices

### Appendix A: Lean UX Canvas

**Problem Statement:**
Belong recruiters spend excessive time on manual data entry between HERP and Notion, causing delays in candidate communication and reducing time available for high-value activities like sourcing and relationship building.

**Business Outcomes:**
- Reduce recruiter time spent on data entry by 30%
- Reduce time-to-hire by 10% (from 44 days to 40 days)
- Increase recruiter satisfaction by 20%

**Users:**
- Primary: Belong recruiters (5-10 people, based on 200+ operations staff)
- Secondary: Hiring managers (visibility into pipeline)
- Tertiary: Candidates (better experience from faster response)

**User Outcomes:**
- Recruiters: Spend less time on administrative work, more time talking to candidates
- Hiring managers: Real-time visibility into candidate pipeline
- Candidates: Faster feedback, better communication

**Solutions:**
- Real-time HERP-Notion bidirectional sync
- AI-powered candidate analysis
- Automated interview scheduling
- Recruiting analytics dashboard

**Hypotheses:**
1. If we sync HERP to Notion automatically, recruiters will save 20 hours/month
2. If we provide AI candidate analysis, resume screening time will decrease 40%
3. If we show recruiting funnel metrics, hiring managers will make faster decisions

**What's the Most Important Thing to Learn First?**
Do recruiters actually spend significant time on manual data entry? (Time study needed)

**What's the Least Amount of Work to Learn the Next Most Important Thing?**
Shadow 1 recruiter for 1 day, time-study their workflow

---

### Appendix B: Japanese Work Culture Considerations

**Cultural Dimensions Relevant to This Project** (Hofstede's Framework):

1. **Long-Term Orientation** (Japan: 88/100, very high)
   - Implication: Team values perseverance, sustainable processes over quick wins
   - Application: Emphasize Kaizen (continuous improvement) over "move fast and break things"

2. **Uncertainty Avoidance** (Japan: 92/100, very high)
   - Implication: Team prefers detailed plans, clear processes, risk mitigation
   - Application: Provide clear DoD, DoR, sprint backlog, mid-sprint checkpoints

3. **Collectivism in Workplace** (Japan: in-group harmony)
   - Implication: Team prioritizes group goals over individual achievement
   - Application: Celebrate team successes, avoid singling out individuals (positive or negative)

4. **Power Distance** (Japan: 54/100, moderate)
   - Implication: Respect for authority, but also consensus-driven decisions
   - Application: PM provides direction, but invites input via nemawashi (根回し - consensus building)

**Relevant Japanese Concepts:**

- **がんばる (Ganbaru)**: Perseverance, trying hard → Can lead to overwork if not managed
- **迷惑 (Meiwaku)**: Burden on others → Team may not ask for help to avoid "bothering" others
- **和 (Wa)**: Harmony → Team may not voice disagreement to maintain harmony
- **出勤主義 (Shukkin-shugi)**: Presenteeism → Being at work is valued, even if not productive
- **残業 (Zangyō)**: Overtime → Normalized, sometimes unpaid, cultural expectation
- **過労死 (Karōshi)**: Death from overwork → Extreme, but illustrates cultural risk

**PM Responsibilities in Japanese Context:**

1. **Protect Team from Overwork**: Explicitly say "don't work overtime"
2. **Model Work-Life Balance**: Leave on time, take PTO, share personal life
3. **Invite Dissent**: Create safe spaces for "no" and disagreement
4. **Reward Help-Seeking**: Praise when team member asks for help (counter 迷惑)
5. **Celebrate Rest**: Acknowledge when team member takes vacation

---

### Appendix C: Resources & Further Reading

**Lean UX & Lean Startup:**
- "Lean UX" by Jeff Gothelf
- "The Lean Startup" by Eric Ries
- "Escaping the Build Trap" by Melissa Perri
- "Lean Analytics" by Alistair Croll & Benjamin Yoskovitz

**DORA Metrics & DevOps:**
- "Accelerate" by Nicole Forsgren, Jez Humble, Gene Kim
- DORA Research: https://dora.dev/

**Kaizen & Japanese Management:**
- "The Toyota Way" by Jeffrey Liker
- "Gemba Kaizen" by Masaaki Imai
- "Out of the Crisis" by W. Edwards Deming

**Psychological Safety & Team Health:**
- "The Fearless Organization" by Amy Edmondson
- Google's Project Aristotle: https://rework.withgoogle.com/

**Data-Driven Product Management:**
- "Inspired" by Marty Cagan
- "Measure What Matters" by John Doerr (OKRs)
- "Lean Analytics" by Alistair Croll

---

**End of Report**

**Next Actions:**
1. PM reviews this report
2. PM schedules gemba walk with recruiter THIS WEEK
3. PM sends team health survey TODAY
4. Sprint 2 planning incorporates recommendations
5. Monthly review of metrics and experiments

**Report Metadata:**
- **Pages**: 47
- **Word Count**: ~12,000
- **Preparation Time**: 4 hours
- **Next Update**: After Sprint 2 (2026-02-14)
