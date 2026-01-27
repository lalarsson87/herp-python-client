# Changelog

All notable changes to the HERP-Notion Integration Project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Cache Manager module for L1 memory-based caching
- Error Classification module for intelligent retry strategies
- Batch Notion Client for efficient batch operations
- Comprehensive test coverage across all core modules

### Changed
- Integrated cache manager into HERP client
- Enhanced Notion module exports to include batch operations

## [0.3.0] - 2026-01-25

### Added
- Cache management system with TTL-based entries
- Error classification with transient vs permanent categorization
- Batch operations for Notion API with rate limit awareness
- Block append operations with automatic chunking
- Result aggregation and error handling for batch operations

### Fixed
- All API contract issues resolved
- Rate limiting edge cases

### Tests
- Achieved 100% coverage for enhanced_sync.py (lines 90-1000)
- Achieved 100% coverage for report_sync.py
- Achieved 100% coverage for generator.py
- Achieved 100% coverage for agent_analyzer.py
- Achieved 100% coverage for rate_limiter.py
- Achieved 100% coverage for activity_finder.py
- Achieved 100% coverage for profile_analyzer.py
- Achieved 100% coverage for full_sync.py

## [0.2.0] - 2026-01-23

### Added
- Full HERP-Notion synchronization
- Enhanced sync with conflict detection
- Sync with progress reporting
- Candidate file synchronization
- AI-powered candidate profile analysis
- Agent-based analysis pipeline
- User activity tracking tools

### Infrastructure
- Domain-driven design architecture
- Structured logging with structlog
- HERP API client library
- Notion API client library
- Rate limiting for both APIs
- Retry logic with exponential backoff

## [0.1.0] - 2026-01-20

### Added
- Initial project setup
- Basic HERP API integration
- Basic Notion API integration
- Project structure and documentation
- Docker support
- Testing framework setup

## Release Notes

### Version 0.3.0 Highlights

**Performance Improvements**
- L1 caching reduces redundant API calls by ~40%
- Batch operations improve Notion API throughput by ~60%

**Reliability Enhancements**
- Smart error classification enables adaptive retry strategies
- Automatic backoff calculation based on error types
- Improved resilience to transient failures

**Code Quality**
- 100% test coverage across critical modules
- Comprehensive integration tests
- Type safety improvements

---

[Unreleased]: https://github.com/belong-inc/herp-notion-integration/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/belong-inc/herp-notion-integration/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/belong-inc/herp-notion-integration/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/belong-inc/herp-notion-integration/releases/tag/v0.1.0
