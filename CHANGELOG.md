# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2025-10-21

### Changed

#### Package Metadata Optimization
- Enhanced package description for better discoverability
- Expanded keywords from 9 to 20 for improved PyPI search visibility
  - Added: sql, query, olap, data-warehouse, transformation, database
- Expanded classifiers from 14 to 31 for better categorization
  - Added Framework :: Pydantic and Framework :: Pydantic :: 2
  - Added Intended Audience :: Information Technology and Education
  - Added Programming Language :: Python :: 3.13
  - Added Programming Language :: SQL
  - Added Topic :: Scientific/Engineering :: Information Analysis
  - Added Typing :: Typed
- Optimized for search terms: "sql query", "data pipeline", "local-first", "DuckDB analytics"

**No functional changes** - This release only updates package metadata to improve discoverability on PyPI.

---

## [1.1.0] - 2025-10-21

### Major Enhancements - Phase 1 & 2: CLI Transformation

This release represents a significant architectural improvement, transforming SBDK into a professional-grade CLI tool with patterns inspired by spec-kit and other industry-leading CLIs.

### Added - Phase 1: Core Architecture

#### Exception Hierarchy (`sbdk/exceptions.py`)
- Comprehensive exception hierarchy with structured error handling
- Custom exit codes (0-5) for different error types
- Actionable error messages with suggestions
- Beautiful error formatting with Rich integration
- Exception types: `ConfigurationError`, `PipelineError`, `ValidationError`, `NetworkError`, etc.

#### Context Management (`sbdk/context.py`)
- Centralized context manager for state and configuration
- Integrated logging with file persistence to `.sbdk/logs/`
- Resource lifecycle management with automatic cleanup
- Support for verbose, quiet, and dry-run modes
- Singleton pattern for consistent state across commands

#### Configuration Validation (`sbdk/validators.py`)
- Pydantic-based schemas for type-safe configuration
- Comprehensive validation with clear error messages
- Nested configuration models (FeatureFlags, PerformanceConfig, DBTConfig, etc.)
- Automatic path expansion and validation
- Command input validators for CLI arguments

#### Output Formatters (`sbdk/formatters.py`)
- Multi-format output support: text, JSON, YAML, table, minimal
- Consistent formatting methods across all commands
- Spec-kit-inspired structured output
- Scripting-friendly minimal mode for automation
- Integration with Rich console for beautiful displays

#### Enhanced Configuration (`sbdk/core/config.py`)
- Backward-compatible configuration with Pydantic validation
- Enhanced validation through integrated schemas
- New methods for feature flags and performance configuration
- Utility functions for creating and merging configs

### Added - Phase 2: Professional CLI Features

#### Base Command Architecture (`sbdk/cli/base.py`)
- Abstract `BaseCommand` class for all CLI commands
- `ProjectCommand` for commands requiring SBDK project
- `InitCommand` for initialization commands
- Built-in validation, execution, and error handling lifecycle
- Utility decorators: `@with_context`, `@handle_errors`

#### Enhanced CLI Main (`sbdk/cli/main.py`)
- **Global Options** available to all commands:
  - `--verbose, -v`: Detailed debug output with logging
  - `--quiet, -q`: Suppress non-essential output (errors only)
  - `--dry-run`: Preview mode without executing changes
  - `--format, -f`: Output format (text, json, yaml, table, minimal)
  - `--project-dir, -p`: Specify custom project directory
- Context management integration for all commands
- Improved help documentation with usage examples
- `no_args_is_help` for better UX

#### New Commands
- `sbdk completion`: Generate shell completion scripts (bash, zsh, fish, powershell)
- `sbdk query`: Query DuckDB database with built-in SQL interface
  - Show all tables with row counts
  - Execute SQL queries directly from command line
  - Interactive SQL mode with syntax highlighting
  - Rich formatted output tables
  - Integration with project configuration

#### Project Template Enhancements
- Added `query.py` helper script to all new projects
  - No installation required (uses Python duckdb package)
  - Interactive SQL mode
  - Execute queries from files
  - Comprehensive help and examples
  - Automatic database discovery

#### Enhanced Commands
- `sbdk version`:
  - Multi-format support (text, json, minimal)
  - Verbose mode shows Python version, platform, executable path
  - JSON output for automation and scripting
  - Minimal output (version number only) for shell scripts

### Changed

#### Architecture Improvements
- Migrated from procedural to object-oriented command architecture
- Centralized error handling across all commands
- Unified output formatting system
- Context-aware logging throughout the application

#### Developer Experience
- Better error messages with actionable suggestions
- Consistent CLI patterns across all commands
- Improved help text with examples
- Shell completion support for better discoverability

### Testing

#### Phase 1 Tests (125 tests total)
- `tests/test_phase1_exceptions.py`: 27 tests for exception hierarchy
- `tests/test_phase1_context.py`: 28 tests for context management
- `tests/test_phase1_validators.py`: 35 tests for Pydantic schemas
- `tests/test_phase1_formatters.py`: 35 tests for output formatting

#### Test Coverage
- All 125 Phase 1 tests passing
- End-to-end integration tests passing
- 100% backward compatibility maintained
- Complete pipeline workflow tested (DLT + dbt)

### Documentation

#### New Documentation
- `docs/PHASE1_TRANSFORMATION.md`: Complete Phase 1 architecture guide
- `docs/PHASE2_ENHANCEMENTS.md`: Phase 2 CLI features documentation
- `docs/PHASE1_TEST_RESULTS.md`: Comprehensive test results

#### Updated Documentation
- **README.md**: Added professional CLI architecture diagrams, query documentation, DuckDB CLI installation guide
- **API_REFERENCE.md**: Added `sbdk query` command documentation with examples
- **SETUP.md**: Completely rewritten for current development workflow
- **data/README.md**: New documentation for data directory usage
- Enhanced CLI usage examples throughout
- Added multi-format output examples
- Updated command reference with global options and query commands
- Added visual architecture diagrams (ASCII art)
- Improved troubleshooting guides

### Technical Improvements

#### Dependencies
- Added `pyyaml>=6.0.0` for YAML output support
- Upgraded `deepdiff>=8.6.1` to fix CVE-2025-58367 security vulnerability
- All existing dependencies maintained

#### Backward Compatibility
- **100% backward compatible** with version 1.0.1
- All existing commands continue to work
- No breaking changes to public APIs
- Existing configurations supported

### Performance
- No performance degradation
- Context management adds minimal overhead
- Logging optimized for production use

### Security
- **Fixed CVE-2025-58367**: Upgraded deepdiff from 7.0.1 to 8.6.1
  - Addressed Python Class Pollution vulnerability
  - Security scan now shows 0 vulnerabilities
- Type-safe configuration validation prevents injection
- Structured error handling prevents information leakage
- Path validation and expansion secured
- `.gitignore` updated to exclude sensitive database files (*.duckdb)

---

## [1.0.1] - 2025-08-03

### Fixed
- Fixed 'VisualCLI' object has no attribute 'start' error by adding synchronous entry point
- Resolved dbt DuckDB path resolution issues with proper template placeholder replacement
- Fixed profile name mismatch between dbt_project.yml and profiles.yml
- Corrected template replacement logic to handle {project_name} placeholders
- Fixed license typo: "furnished to do do so" → "furnished to do so"

### Added
- Comprehensive end-to-end integration testing
- Complete ServerStateManager implementation in sbdk.cli.commands.start
- Missing load_config function to sbdk.core.config
- Proper error handling for VisualCLI startup

### Changed
- Updated dbt template system to use proper placeholder replacement
- Improved project initialization workflow
- Enhanced test coverage to 95.3% (150+ tests)

### Removed
- Cleaned up build artifacts and cache directories
- Removed redundant requirements.txt files (using pyproject.toml only)
- Eliminated temporary test files and development debris

---

## [1.0.0] - 2025-08-01

### Added
- Initial release of SBDK.dev Local-First Data Pipeline Toolkit
- Modern CLI interface with Typer and Rich
- DLT (data load tool) integration for data pipelines
- DuckDB embedded database support
- dbt Core integration for data transformations
- FastAPI webhook server capabilities
- Visual interface with async/sync support
- Comprehensive test suite with pytest
- uv package management integration
- Project template system with automatic initialization
- Performance benchmarking and monitoring
- Complete documentation and examples

### Features
- Local-first development with DuckDB
- Fast installation with uv package manager
- Clean CLI interface with optional visual mode
- Scalable data processing capabilities
- Minimal configuration requirements
- Cross-platform support (Windows, macOS, Linux)

### Technical Highlights
- Python 3.9+ compatibility
- Modern packaging with pyproject.toml
- Type hints throughout codebase
- Comprehensive error handling
- Professional logging and monitoring
- Extensive test coverage (95%+)
