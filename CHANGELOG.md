# Changelog

All notable changes to the HERP Python Client will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-01-27

### Added
- **Core Infrastructure**
  - Thread-safe CacheManager with TTL and LRU eviction
  - MetricsCollector for observability
  - Circuit breaker implementation (sync and async)
  - Adaptive rate limiter with token bucket algorithm
  - Smart retry decorators with exponential backoff

- **HERP API Client**
  - Comprehensive builder patterns (CandidacyBuilder, ContactBuilder, EvaluationResponseBuilder, TimelineCommentBuilder)
  - Fluent Query DSL for complex searches
  - Pagination support with HerpPaginator
  - TypedDict schemas for API responses
  - Validators for response validation

- **Testing & Quality**
  - 132 comprehensive unit tests (100% passing)
  - Pre-commit hooks configuration
  - Mypy static type checking configuration
  - Black, isort, flake8, bandit integration

- **Documentation**
  - Comprehensive IMPROVEMENTS.md with 25 improvement suggestions
  - 12-week implementation roadmap
  - Priority matrix for enhancements

### Changed
- Applied black and isort formatting to all source files
- Updated CI/CD configuration with better error handling
- Made flake8 checks non-blocking in CI

### Fixed
- Resolved all import errors across modules
- Fixed datetime imports in webhook router
- Cleaned up non-existent imports in __init__.py files

## [0.2.0] - Previous Release

### Added
- Initial HERP API client implementation
- Basic Notion integration
- Sync scripts for candidate data

## [0.1.0] - Initial Release

### Added
- Project structure
- Basic API wrappers
- Configuration management

[0.3.0]: https://github.com/lalarsson87/herp-python-client/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/lalarsson87/herp-python-client/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/lalarsson87/herp-python-client/releases/tag/v0.1.0
