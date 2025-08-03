# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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