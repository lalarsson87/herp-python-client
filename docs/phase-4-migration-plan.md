# Phase 4 Migration Plan
**Remaining Scripts: 3/17 (17.6%)**

---

## Script Analysis

### 1. deduplicate-candidates.py → CandidateDeduplicator

**Current**: 227 lines monolithic script
**Domain**: Candidates (Data Quality)
**Complexity**: Medium

**Key Features**:
- Query all candidates from Notion database
- Find duplicates by HERP Candidacy ID
- Archive older entries, keep most recent
- Dry run mode for safety

**Migration Strategy**:
- **Service**: `src/domains/candidates/data_quality/deduplicator.py`
- **CLI**: `src/cli/entrypoints/deduplicate_candidates.py`
- **Tests**: `tests/unit/domains/candidates/test_deduplicator.py`

**Estimated**:
- Service: ~400 lines
- CLI: ~150 lines
- Tests: ~500 lines (20 tests)
- Coverage target: >90%

---

### 2. evaluate-candidate.py → CandidateEvaluator

**Current**: 333 lines monolithic script
**Domain**: Candidates (Evaluation)
**Complexity**: Medium-High

**Key Features**:
- Fetch comprehensive candidate data (candidacy, files, contacts, timeline)
- Auto-detect evaluation track (IC/EM/Hybrid)
- Generate evaluation template with scorecard
- Post evaluation to HERP timeline (optional)
- Markdown-formatted output

**Migration Strategy**:
- **Service**: `src/domains/candidates/evaluation/evaluator.py`
- **CLI**: `src/cli/entrypoints/evaluate_candidate.py`
- **Tests**: `tests/unit/domains/candidates/test_evaluator.py`

**Estimated**:
- Service: ~500 lines
- CLI: ~200 lines
- Tests: ~600 lines (25 tests)
- Coverage target: >90%

**Note**: This overlaps with ProfileAnalyzer functionality. Consider integration or refactoring to share code.

---

### 3. test-herp-api.py

**Current**: 56 lines test utility
**Domain**: Core (Testing)
**Complexity**: Low

**Assessment**: **DO NOT MIGRATE**

**Rationale**:
- Simple connectivity test script (56 lines)
- Already uses refactored `src/core/utils/logging_config`
- Already uses refactored `src.core` imports (line 9)
- Not a business logic script - just a diagnostic tool
- No test suite needed for a test script
- Minimal value from migration

**Recommendation**: Keep as-is in `scripts/` directory as a diagnostic utility

---

## Phase 4 Migration Decision

### Scripts to Migrate: 2/3

1. ✅ **deduplicate-candidates.py** → CandidateDeduplicator
2. ✅ **evaluate-candidate.py** → CandidateEvaluator
3. ❌ **test-herp-api.py** → Keep as-is (diagnostic utility)

### Adjusted Completion Target

**Final Completion**: 16/17 scripts (94.1%)
- 14 migrated (Phases 1-3)
- 2 migrated (Phase 4)
- 1 kept as diagnostic utility (test-herp-api.py)

---

## Phase 4 Execution Plan

### Approach: Sequential Migration

Given medium complexity and potential overlap, migrate sequentially:

**Day 1: CandidateDeduplicator**
1. Create domain service with dependency injection
2. Extract configuration to DeduplicationConfig dataclass
3. Create CLI wrapper
4. Write comprehensive unit tests (20 tests)
5. Verify in Docker

**Day 2: CandidateEvaluator**
1. Create domain service
2. Identify overlap with ProfileAnalyzer (potential refactoring)
3. Create CLI wrapper
4. Write comprehensive unit tests (25 tests)
5. Verify in Docker

**Estimated Duration**: 1-2 days total

---

## Expected Outcomes

### Phase 4 Statistics

| Metric | Estimate |
|--------|----------|
| Services Created | 2 |
| CLI Wrappers | 2 |
| Tests Added | 45 |
| Total Tests | 418 |
| Coverage | >90% |
| Code Lines Added | ~2,350 |

### Final Project Statistics

| Metric | Current | After Phase 4 | Change |
|--------|---------|---------------|--------|
| Scripts Migrated | 14/17 (82.4%) | 16/17 (94.1%) | +11.7% |
| Total Tests | 373 | 418 | +45 tests |
| Service Lines | ~7,000 | ~7,900 | +900 |
| Test Lines | ~10,500 | ~11,600 | +1,100 |
| Total Coverage | >90% | >90% | Maintained |

---

## Integration Considerations

### CandidateEvaluator ↔ ProfileAnalyzer Overlap

**Shared Functionality**:
- Both fetch candidate data from HERP
- Both analyze candidate suitability
- Both generate reports

**Differences**:
- **ProfileAnalyzer**: AI-powered Four Pillars scoring, Notion updates
- **CandidateEvaluator**: Template-based evaluation, manual completion, HERP timeline posting

**Recommendation**:
1. Extract shared data fetching to a common service: `CandidateDataFetcher`
2. Keep evaluation logic separate (different frameworks)
3. Consider future unification under a comprehensive evaluation system

**Potential Shared Service**:
```python
# src/domains/candidates/data/fetcher.py
class CandidateDataFetcher:
    def fetch_comprehensive_data(self, candidacy_id: str) -> CandidateData:
        """Fetch all candidate data (candidacy, files, contacts, timeline)"""
        # Shared implementation used by both ProfileAnalyzer and CandidateEvaluator
```

---

## Architecture Impact

### After Phase 4

```
src/domains/candidates/
├── analysis/          # ProfileAnalyzer, AgentAnalyzer, Orchestrator
├── reviews/           # ReviewGenerator
├── evaluation/        # CandidateEvaluator ✨ NEW
├── data_quality/      # CandidateDeduplicator ✨ NEW
└── data/              # CandidateDataFetcher ✨ NEW (refactoring)
```

### Refactoring Opportunity

**Current State**: ProfileAnalyzer and CandidateEvaluator both fetch HERP data independently

**Improved State**: Both use shared `CandidateDataFetcher`

**Benefits**:
- DRY principle (Don't Repeat Yourself)
- Consistent data fetching logic
- Easier to add caching/optimization
- Single source of truth for HERP data access

**Implementation**: Can be done during Phase 4 CandidateEvaluator migration

---

## Risk Assessment

### Low Risk

- **CandidateDeduplicator**: Straightforward logic, minimal dependencies
- **CandidateEvaluator**: Template-based, no complex algorithms

### Medium Risk

- **Overlap with ProfileAnalyzer**: Need to identify shared code carefully
- **Data fetching duplication**: Should refactor during migration

### Mitigation

1. **Review ProfileAnalyzer** before starting CandidateEvaluator migration
2. **Extract shared utilities** during migration (not as separate step)
3. **Comprehensive testing** to ensure no regression
4. **Dry run modes** to prevent accidental HERP/Notion writes

---

## Success Criteria

### Phase 4 Complete When:

- [ ] CandidateDeduplicator service created
  - [ ] 20+ tests passing (>90% coverage)
  - [ ] CLI wrapper functional
  - [ ] Dry run mode working
  - [ ] Notion API mocked in tests

- [ ] CandidateEvaluator service created
  - [ ] 25+ tests passing (>90% coverage)
  - [ ] CLI wrapper functional
  - [ ] Template generation working
  - [ ] HERP timeline posting optional
  - [ ] Shared CandidateDataFetcher extracted (if feasible)

- [ ] All tests passing (418 total)
- [ ] Documentation updated
- [ ] PROJECT-SUMMARY.md updated to 94.1% completion

---

## Timeline

**Start Date**: TBD (after Phase 4 approval)
**Estimated Duration**: 1-2 days
**Target Completion**: Within 1 week

---

## Appendix: test-herp-api.py Justification

**Why NOT migrate**:

1. **Already refactored**: Uses `src.core.utils.logging_config` (line 9)
2. **Diagnostic tool**: Not business logic
3. **Minimal complexity**: 56 lines, no complex logic
4. **No test value**: Testing a test script doesn't add value
5. **Low ROI**: Migration would create more code than original script

**Status**: Keep as diagnostic utility in `scripts/` directory

**Future**: Could evolve into integration test suite using pytest fixtures, but not priority for domain-driven migration

---

**Created**: January 25, 2026
**Status**: Draft - Awaiting approval for Phase 4 execution
**Next Step**: Review plan and approve/modify approach

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
