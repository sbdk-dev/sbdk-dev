# 🚀 SBDK Swarm Command Examples

> Ready-to-use swarm commands for SBDK development
> Copy, paste, and build!

---

## Core SBDK Features (Priority Order)

### 1. Environment Management System
```bash
/swarm "Using SPARC methodology and TDD principles:

Build SBDK Environment Management System

SPECIFICATION:
- Multi-environment support (dev/staging/prod)
- Fast switching (<2 seconds)
- Template system (analytics, ml, basic)
- Configuration isolation
- Store in .sbdk/environments/

PSEUDOCODE:
1. create_environment(name, template)
2. switch_environment(target)
3. list_environments()
4. delete_environment(name)
5. validate_config(environment)

ARCHITECTURE:
- EnvironmentManager (core orchestrator)
- ConfigValidator (Pydantic schemas)
- TemplateEngine (template management)
- EnvironmentSwitcher (fast switching)
- CLI module (user interface)

REFINEMENT:
- Cache active environment
- Lazy load configurations
- Atomic switching operations
- Rollback on errors

CODE (TDD):
1. Write comprehensive test suite first
2. Test all edge cases and error scenarios
3. Implement minimal code to pass tests
4. Refactor for performance
5. Achieve 100% test coverage

AGENTS:
1. Architect: Design system and APIs
2. Developer: TDD implementation
3. Tester: Comprehensive test coverage
4. Reviewer: Performance optimization
5. Documenter: User guide and API docs

DELIVERABLES:
- src/sbdk/environment/ module
- tests/test_environment.py (100% coverage)
- CLI commands: sbdk env [create|switch|list|delete|status]
- docs/environment-management.md
- Performance: <2 second switching"
```

### 2. PostgreSQL Data Connector
```bash
/swarm "SPARC+TDD: PostgreSQL Data Connector

SPECIFICATION:
- DLT-based PostgreSQL connector
- Smart sampling strategies
- Connection pooling
- Schema auto-detection
- Error recovery

PSEUDOCODE:
connect() → sample_data() → detect_schema() → load_to_duckdb()

ARCHITECTURE:
- BaseConnector (abstract interface)
- PostgreSQLConnector (implementation)
- SampleStrategy (10%, 1000 rows, time-based)
- SchemaDetector (auto-discovery)
- ConnectionPool (resource management)

REFINEMENT:
- Retry logic with exponential backoff
- Connection caching
- Incremental loading support

CODE:
- Mock all database calls in tests
- Test connection failures
- Test sampling strategies
- 100% coverage required

Location: src/sbdk/connectors/postgres.py"
```

### 3. MCP Server Implementation
```bash
/swarm "SPARC+TDD: MCP Server for AI Tools

SPECIFICATION:
Create MCP server exposing SBDK capabilities to AI agents

ARCHITECTURE:
- MCPServer class (main server)
- Tool decorators (@mcp.tool)
- Authentication middleware
- Rate limiting
- Error handling

TOOLS TO IMPLEMENT:
1. execute_query(sql: str, env: str) -> dict
2. run_pipeline(models: List[str]) -> dict
3. get_schema(table: str) -> dict
4. profile_data(table: str) -> dict
5. create_environment(name: str, template: str) -> dict

REFINEMENT:
- Async operations
- Result caching
- Query optimization

TDD APPROACH:
- Mock SBDK operations
- Test each endpoint
- Test authentication
- Test rate limiting
- Test error scenarios

Port: 3000
Security: API key authentication"
```

---

## Quality & Testing Features

### 4. Data Quality Framework
```bash
/swarm "SPARC+TDD: Data Quality Engine

SPECIFICATION:
- Statistical profiling
- Custom quality rules
- Anomaly detection
- Historical tracking

COMPONENTS:
- DataProfiler (statistics)
- RuleEngine (YAML rules)
- AnomalyDetector (ML-based)
- QualityReporter (outputs)

DELIVERABLES:
- Profile: nulls, cardinality, distributions
- Rules: YAML-based definitions
- Storage: DuckDB for history
- Reports: HTML, JSON, Prometheus"
```

### 5. Testing Framework
```bash
/swarm "SPARC+TDD: Comprehensive Testing Framework

TEST LEVELS:
1. Unit tests (individual functions)
2. Integration tests (full pipelines)
3. Regression tests (baseline comparison)
4. Performance tests (benchmarks)
5. E2E tests (complete workflows)

FEATURES:
- Fixture management
- Test data generation
- Coverage reporting
- CI/CD integration

Location: src/sbdk/testing/"
```

---

## Developer Tools

### 6. Hot-Reload Development Server
```bash
/swarm "SPARC+TDD: Hot-Reload Server

SPECIFICATION:
- Watch file changes
- Auto-rebuild on save
- WebSocket notifications
- <3 second rebuild time

ARCHITECTURE:
- FileWatcher (fs events)
- BuildManager (incremental)
- WebSocketServer (live updates)
- WebUI (status dashboard)

Port: 8080
Performance: <3s rebuilds"
```

### 7. CLI Enhancement
```bash
/swarm "SPARC+TDD: Enhanced CLI Experience

FEATURES:
- Rich formatting (colors, tables)
- Progress bars for long operations
- Interactive prompts
- Shell completion
- Global options (--verbose, --format)

Libraries: Typer, Rich, Click
Location: src/sbdk/cli/"
```

---

## Data Processing

### 8. Incremental Processing Engine
```bash
/swarm "SPARC+TDD: Incremental Processing

SPECIFICATION:
Track changes and rebuild only affected models

ARCHITECTURE:
- ChangeDetector (file/table monitoring)
- DependencyGraph (model relationships)
- IncrementalBuilder (smart rebuilds)
- StateManager (build history)

PERFORMANCE:
- Hash-based change detection
- Parallel execution
- <30 second cycles

TDD:
- Test change detection
- Test dependency resolution
- Test incremental vs full builds"
```

### 9. Semantic Layer
```bash
/swarm "SPARC+TDD: Semantic Layer

SPECIFICATION:
Business logic layer for metric definitions

FEATURES:
- YAML metric definitions
- Business term → SQL translation
- Automatic aggregations
- Dimension handling

EXAMPLE:
Query: 'monthly revenue by segment'
Output: SELECT segment, SUM(revenue) ...

Location: src/sbdk/semantic/"
```

---

## Integration Features

### 10. CSV/JSON Connectors
```bash
/swarm "SPARC+TDD: File Connectors

Build CSV and JSON connectors with:
- Schema inference
- Large file handling
- Streaming support
- Multiple encodings
- Error recovery

Test with various file formats and sizes"
```

### 11. VS Code Extension
```bash
/swarm "SPARC+TDD: VS Code Extension

FEATURES:
- Run dbt models from editor
- Inline query results
- Syntax highlighting
- Command palette

TypeScript, VS Code Extension API
Location: vscode-extension/"
```

---

## Bug Fixes & Improvements

### 12. Performance Optimization
```bash
/swarm "TDD: Fix Slow Pipeline

REPRODUCE:
1. Write performance test showing issue
2. Profile to find bottleneck
3. Write test for expected performance
4. Implement optimization
5. Verify 10x improvement"
```

### 13. Error Message Enhancement
```bash
/swarm "SPARC+TDD: Better Error Messages

REQUIREMENTS:
- Clear problem description
- Suggested fixes
- Relevant context
- Rich formatting

Example:
'Column not found' → 'Column user_id not found in table orders. Did you mean customer_id?'"
```

---

## Multi-Agent Patterns

### 14. Parallel Connector Development
```bash
/swarm "Parallel Development: 3 Connectors

Spawn 3 concurrent swarms:
1. PostgreSQL connector
2. MySQL connector
3. SQLite connector

All follow BaseConnector interface
Coordinate through shared tests
100% coverage each"
```

### 15. Full Stack Feature
```bash
/swarm "5-Agent Full Feature

FEATURE: Complete data pipeline

AGENTS:
1. Architect: System design
2. Backend: Core implementation
3. Frontend: CLI/UI
4. Tester: Test suite
5. DevOps: CI/CD setup

Coordinate via AgentDB"
```

---

## Quick Templates

### Simple Utility
```bash
/swarm "TDD: Create [UTILITY_NAME] utility
Requirements: [LIST]
Tests first, 100% coverage
Location: src/sbdk/utils/"
```

### Bug Fix
```bash
/swarm "TDD Bug Fix: [ISSUE]
1. Write failing test
2. Fix to pass test
3. No regressions
4. Document solution"
```

### Documentation
```bash
/swarm "Create comprehensive docs for [FEATURE]
Include: API reference, user guide, examples
Format: Markdown, mkdocs compatible"
```

---

## Tips for Effective Swarms

1. **Always include "SPARC+TDD"** - Enforces methodology
2. **Specify location** - Where code should go
3. **Set targets** - Performance, coverage, quality
4. **List deliverables** - Be explicit about outputs
5. **Include agents** - 5-agent pattern works best

---

**Remember:** Start services first with `./swarm-manager.sh start`!