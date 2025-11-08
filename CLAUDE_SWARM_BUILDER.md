# CLAUDE SWARM BUILDER: SBDK Platform Development

**Version**: 1.0
**Date**: January 2025
**Purpose**: Multi-agent swarm orchestration for SBDK platform development

---

## Executive Summary

This document defines how to use Claude Flow swarm orchestration to accelerate SBDK platform development according to the [SBDK Platform Vision](./SBDK_PLATFORM_VISION.md). By leveraging concurrent multi-agent swarms, we can implement complex features faster while maintaining quality, security, and alignment with our local-first principles.

### Key Benefits

- 🚀 **Parallel Development**: 5+ agents working concurrently on different components
- ✅ **Built-in Quality**: TDD, code review, optimization in every swarm
- 🔒 **Secure**: Local execution with API key obfuscation via Rust proxy
- 📦 **Production-Ready**: Automated testing, documentation, and package preparation
- 🎯 **Vision-Aligned**: Each swarm task maps to SBDK platform roadmap

---

## Table of Contents

1. [Swarm Infrastructure Setup](#1-swarm-infrastructure-setup)
2. [SBDK Swarm Patterns](#2-sbdk-swarm-patterns)
3. [Phase-Based Implementation](#3-phase-based-implementation)
4. [Security & Best Practices](#4-security--best-practices)
5. [Swarm Workflows](#5-swarm-workflows)
6. [Monitoring & Quality](#6-monitoring--quality)

---

## 1. Swarm Infrastructure Setup

### 1.1 Initial Setup

#### Prerequisites
- Node.js 18+ installed
- Claude Code Web access (browser or mobile)
- API keys (optional but recommended for extended usage)

#### Environment Configuration

**Option 1: With API Keys (Recommended)**
```bash
# In Claude Code Web environment panel, set:
OPENROUTER_API_KEY=sk-or-v1-xxxxx
GEMINI_API_KEY=xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Optional: Set rate limits for safety
OPENROUTER_RATE_LIMIT=100
GEMINI_RATE_LIMIT=50
```

**Option 2: No API Keys**
```bash
# Works with Claude Code built-in capabilities only
# Limited to Claude's native agents, no external LLM calls
```

### 1.2 Swarm Infrastructure Launch

```bash
# Launch all swarm infrastructure components
npx agentic-flow &
npx claude-flow@alpha &
npx agentdb &

# Wait for initialization (typically 5-10 seconds)
sleep 10

# Verify services are running
curl http://localhost:3000/health    # agentic-flow
curl http://localhost:3001/health    # claude-flow
curl http://localhost:3002/health    # agentdb
```

### 1.3 Swarm Architecture

```
┌─────────────────────────────────────────────────────┐
│              Claude Code Web                        │
│         (Browser/Mobile Interface)                  │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│            Swarm Orchestration Layer                │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ Claude Flow  │  │ Agentic Flow │  │ AgentDB  │ │
│  │   (Alpha)    │  │              │  │          │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│         Rust Proxy (API Key Obfuscation)           │
│              localhost:3003                         │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│          External LLM Services                      │
│   OpenRouter │ Gemini │ Anthropic │ Others         │
└─────────────────────────────────────────────────────┘
```

---

## 2. SBDK Swarm Patterns

### 2.1 Standard 5-Agent Swarm Pattern

**Agent Roles**:
1. **Architect Agent**: Design patterns, structure, API design
2. **Implementation Agent**: Core feature development
3. **Testing Agent**: TDD, unit tests, integration tests
4. **Review Agent**: Code review, quality checks, refactoring
5. **Documentation Agent**: Docs, examples, package preparation

### 2.2 Swarm Command Template

```bash
/swarm "Using the configured API keys, launch npx agentic-flow, npx claude-flow@alpha, and npx agentdb, then spawn a 5-agent swarm to:

TASK: [Specific SBDK feature or component]

REQUIREMENTS:
- Follow SBDK Platform Vision (SBDK_PLATFORM_VISION.md)
- Implement with TDD (tests first)
- Maintain 100% test coverage
- Include comprehensive documentation
- Ensure backward compatibility
- Follow Python best practices (uv, typer, rich)
- Align with local-first principles

DELIVERABLES:
1. Feature implementation with tests
2. Code review and optimization
3. Documentation and examples
4. Package preparation (if applicable)
5. Integration with existing SBDK CLI

CONSTRAINTS:
- Local-first execution
- Zero external dependencies for core features
- Production-ready code quality
- Performance: <30s iteration cycle target
"
```

### 2.3 Specialized Swarm Patterns

#### **Pattern A: Feature Development Swarm**
```bash
/swarm "Implement [FEATURE_NAME] for SBDK:

AGENTS:
1. Design: API design, architecture, integration points
2. Core: Implement main functionality with error handling
3. Testing: Unit tests, integration tests, edge cases
4. CLI: Add CLI commands with typer + rich
5. Docs: User guide, API docs, examples

Follow SBDK_PLATFORM_VISION.md section [X.Y]
Include performance benchmarks and quality metrics
Prepare for merge to branch: claude/[feature-name]-[session-id]
"
```

#### **Pattern B: Quality & Testing Swarm**
```bash
/swarm "Quality audit and enhancement for [COMPONENT]:

AGENTS:
1. Analyzer: Code quality analysis, tech debt identification
2. Tester: Expand test coverage, add edge cases
3. Performance: Profile and optimize bottlenecks
4. Security: Security audit, vulnerability scanning
5. Documenter: Improve docs, add missing examples

Target: 100% coverage, <10s test suite, security hardened
"
```

#### **Pattern C: Integration Swarm**
```bash
/swarm "Build [INTEGRATION_NAME] integration for SBDK:

AGENTS:
1. Research: Study external API/tool, design integration
2. Adapter: Implement adapter layer and connectors
3. Testing: Integration tests, mocking, error scenarios
4. Examples: Working examples and use cases
5. Documentation: Integration guide, troubleshooting

Follow SBDK integration patterns (Section 6, Platform Vision)
Ensure clean API boundaries and optional dependencies
"
```

---

## 3. Phase-Based Implementation

### 3.1 Phase 1: Enhanced Foundation (Q1 2026)

#### Milestone 1.1: Environment Management

```bash
/swarm "Implement SBDK Environment Management System:

REFERENCE: SBDK_PLATFORM_VISION.md Section 7.2 (Phase 1.1)

TASKS:
1. Environment configuration system (dev/staging/prod)
2. Profile management (credentials, settings)
3. Template system for common patterns
4. Environment switching and isolation
5. CLI commands: env create/switch/list/status

ACCEPTANCE CRITERIA:
✅ Create environments with templates
✅ Switch between environments in <2 seconds
✅ Isolated configurations per environment
✅ Validation and error handling
✅ 100% test coverage
✅ Documentation with examples

DELIVERABLES:
- src/sbdk/environment/ module
- CLI commands in src/sbdk/cli/env.py
- Tests in tests/test_environment.py
- Documentation in docs/environment-management.md
- Template examples in templates/
"
```

#### Milestone 1.2: Enhanced Data Sources

```bash
/swarm "Implement SBDK Data Source Connectors:

REFERENCE: SBDK_PLATFORM_VISION.md Section 7.2 (Phase 1.2)

COMPONENTS:
1. Database connectors (Postgres, MySQL, Snowflake)
2. File format support (CSV, JSON, Parquet)
3. API connectors with authentication
4. Smart sampling for local development
5. Schema detection and validation

ARCHITECTURE:
- Plugin-based connector system
- Unified connector interface
- Sample strategy engine (10%, 1000 rows, etc.)
- Incremental sync capabilities
- Connection pooling and caching

DELIVERABLES:
- src/sbdk/sources/ connector framework
- Individual connectors in src/sbdk/sources/connectors/
- CLI: source add/sync/status commands
- Tests with mocking for external services
- Documentation and connector development guide
"
```

#### Milestone 1.3: Advanced Pipeline Features

```bash
/swarm "Implement SBDK Advanced Pipeline Engine:

REFERENCE: SBDK_PLATFORM_VISION.md Section 7.2 (Phase 1.3)

FEATURES:
1. Incremental processing engine
2. Change detection for smart rebuilds
3. Comprehensive testing framework
4. Performance profiling and optimization
5. Deployment configuration export

TECHNICAL REQUIREMENTS:
- Dependency graph analysis
- Incremental state management
- Performance instrumentation
- Multi-format export (dbt-cloud, airflow, terraform)
- Parallel execution support

DELIVERABLES:
- src/sbdk/pipeline/ enhanced engine
- CLI: pipeline run --incremental --changed-only
- CLI: pipeline test --coverage --parallel
- CLI: pipeline profile --performance
- CLI: deploy plan/export commands
- Performance benchmarks and optimization report
"
```

### 3.2 Phase 2: Quality & Reliability (Q2 2026)

#### Milestone 2.1: Data Quality Engine

```bash
/swarm "Implement SBDK Data Quality Framework:

REFERENCE: SBDK_PLATFORM_VISION.md Section 7.3 (Phase 2.1)

COMPONENTS:
1. Statistical profiling engine
2. Custom quality rules engine
3. Anomaly detection algorithms
4. Historical quality tracking
5. Quality reporting and alerting

CAPABILITIES:
- Profile: distributions, nulls, cardinality, uniqueness
- Rules: Custom YAML-based quality rules
- Anomaly: Statistical anomaly detection
- History: Track quality metrics over time
- Reports: HTML/JSON/Prometheus formats

DELIVERABLES:
- src/sbdk/quality/ framework
- CLI: quality profile/check/report/monitor
- Rules engine with YAML schema
- Historical tracking with DuckDB storage
- Documentation and rule examples
"
```

#### Milestone 2.2: Testing Framework

```bash
/swarm "Implement SBDK Comprehensive Testing Framework:

REFERENCE: SBDK_PLATFORM_VISION.md Section 7.3 (Phase 2.2)

TEST LEVELS:
1. Unit tests for individual models
2. Integration tests for full pipelines
3. Regression testing against baselines
4. Performance and scale testing
5. Memory profiling and optimization

FRAMEWORK FEATURES:
- Test discovery and execution
- Fixture management and data generation
- Baseline comparison engine
- Performance benchmarking
- Coverage reporting

DELIVERABLES:
- src/sbdk/testing/ framework
- CLI: test unit/integration/regression/performance
- Test utilities and fixtures
- Performance baseline system
- CI/CD integration templates
"
```

#### Milestone 2.3: Developer Tools

```bash
/swarm "Implement SBDK Enhanced Developer Tools:

REFERENCE: SBDK_PLATFORM_VISION.md Section 7.3 (Phase 2.3)

TOOLS:
1. Hot-reload development server
2. Live documentation generation
3. Interactive SQL debugger
4. Query plan analysis and optimization
5. Data exploration tools

FEATURES:
- Watch mode with file change detection
- Live docs with auto-refresh
- SQL REPL with autocomplete
- EXPLAIN plan visualization
- Interactive data profiling

DELIVERABLES:
- src/sbdk/dev/ developer tools
- CLI: dev serve/docs/debug/explore
- Web UI for interactive features
- Real-time feedback system
- Developer workflow documentation
"
```

### 3.3 Phase 3: Integration & Ecosystem (Q3 2026)

#### Milestone 3.1: MCP Server Suite

```bash
/swarm "Implement SBDK MCP Server for AI Integration:

REFERENCE: SBDK_PLATFORM_VISION.md Section 7.4 (Phase 3.1)

MCP TOOLS:
1. execute_query(sql, env) - Run SQL queries
2. run_pipeline(models, env) - Execute dbt models
3. get_schema(table) - Schema introspection
4. profile_data(table, columns) - Data profiling
5. export_data(table, format, path) - Data export
6. create_environment(name, template) - Env management
7. run_tests(models) - Test execution
8. quality_check(table, rules) - Quality validation

SERVER FEATURES:
- Authentication and authorization
- Rate limiting and resource management
- Error handling and recovery
- Request/response logging
- Tool documentation generation

DELIVERABLES:
- src/sbdk/mcp/ MCP server implementation
- CLI: mcp serve --tools all --port 3000
- Integration examples (knowDB, Cursor, Claude)
- MCP protocol documentation
- Security and deployment guide
"
```

#### Milestone 3.2: CI/CD Integration

```bash
/swarm "Build SBDK CI/CD Integration Suite:

REFERENCE: SBDK_PLATFORM_VISION.md Section 7.4 (Phase 3.2)

INTEGRATIONS:
1. GitHub Actions workflow templates
2. GitLab CI pipeline examples
3. Jenkins pipeline scripts
4. Terraform modules for cloud deployment
5. Docker/Kubernetes deployment patterns

TEMPLATES:
- Data pipeline testing workflow
- Quality gate enforcement
- Automated deployment to staging/prod
- Performance regression testing
- Security scanning integration

DELIVERABLES:
- .github/workflows/ action templates
- ci-cd/ integration examples
- Docker images and Kubernetes manifests
- Terraform modules in terraform/
- CI/CD best practices documentation
"
```

#### Milestone 3.3: VS Code Extension

```bash
/swarm "Build SBDK VS Code Extension:

REFERENCE: SBDK_PLATFORM_VISION.md Section 7.4 (Phase 3.3)

FEATURES:
1. Run dbt models from editor
2. Inline query results preview
3. Schema autocomplete
4. Real-time error checking
5. Integrated terminal with SBDK commands
6. Lineage graph visualization
7. Test execution and results

EXTENSION CAPABILITIES:
- Syntax highlighting for SBDK configs
- Command palette integration
- Status bar indicators
- WebView panels for results
- Language server protocol support

DELIVERABLES:
- vscode-extension/ TypeScript implementation
- Extension manifest and configuration
- VS Code Marketplace publishing
- User guide and screenshots
- Extension API documentation
"
```

### 3.4 Phase 4: Team Collaboration (Q4 2026)

#### Milestone 4.1: Shared Templates & Patterns

```bash
/swarm "Implement SBDK Template Management System:

REFERENCE: SBDK_PLATFORM_VISION.md Section 7.5 (Phase 4.1)

FEATURES:
1. Template creation and publishing
2. Template registry (local and remote)
3. Configuration synchronization
4. Team standards enforcement
5. Pattern libraries

TEMPLATE TYPES:
- Project templates (analytics, ML, basic)
- Configuration templates
- dbt model templates
- Quality rule templates
- Integration templates

DELIVERABLES:
- src/sbdk/templates/ framework
- CLI: template create/publish/install
- Template registry server (optional)
- Configuration sync with git
- Template development guide
"
```

#### Milestone 4.2: Project Orchestration

```bash
/swarm "Implement SBDK Multi-Project Orchestration:

REFERENCE: SBDK_PLATFORM_VISION.md Section 7.5 (Phase 4.2)

FEATURES:
1. Workspace management (multiple projects)
2. Cross-project dependency tracking
3. Parallel execution with DAG resolution
4. Shared data artifacts
5. Unified testing and deployment

ARCHITECTURE:
- Workspace configuration
- Dependency graph engine
- Parallel task executor
- Artifact sharing mechanism
- Unified CLI for multi-project ops

DELIVERABLES:
- src/sbdk/workspace/ orchestration
- CLI: workspace create/add/run/test
- Dependency resolution engine
- Cross-project integration tests
- Multi-project workflow guide
"
```

#### Milestone 4.3: Documentation & Knowledge Sharing

```bash
/swarm "Build SBDK Knowledge Management System:

REFERENCE: SBDK_PLATFORM_VISION.md Section 7.5 (Phase 4.3)

COMPONENTS:
1. Interactive documentation with lineage
2. Cross-project documentation search
3. Knowledge base with semantic search
4. Automated documentation updates
5. Team collaboration features

FEATURES:
- Data lineage visualization
- Semantic search across projects
- Documentation versioning
- Team annotations and comments
- Integration with external docs platforms

DELIVERABLES:
- src/sbdk/docs/ documentation engine
- CLI: docs build/publish/search
- Knowledge base with embeddings
- Search interface (web UI)
- Documentation best practices guide
"
```

---

## 4. Security & Best Practices

### 4.1 API Key Management

#### Secure Configuration
```bash
# Create environment-specific .env files
cat > .env.swarm <<EOF
# OpenRouter API (for extended swarm operations)
OPENROUTER_API_KEY=sk-or-v1-xxxxx

# Gemini API (for specific models)
GEMINI_API_KEY=xxxxx

# Anthropic API (for Claude models)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Rate Limits (requests per minute)
OPENROUTER_RATE_LIMIT=100
GEMINI_RATE_LIMIT=50
ANTHROPIC_RATE_LIMIT=50

# Cost Limits (dollars per day)
DAILY_COST_LIMIT=10.00

# Session Timeout (minutes)
SESSION_TIMEOUT=60
EOF

# Load only when needed
source .env.swarm
```

#### Key Rotation & Limits
```bash
# Use short-lived keys for swarm development
# Create keys with strict limits:
- Time limit: 24 hours
- Rate limit: 100 requests/minute
- Cost limit: $10/day
- Scope: Read-only where possible

# Rotate keys weekly
# Revoke immediately after development session
```

### 4.2 Swarm Security Patterns

#### Principle 1: Least Privilege
```bash
# Only grant necessary permissions
OPENROUTER_SCOPE="chat:read,chat:write"  # No admin
GEMINI_SCOPE="generativelanguage.googleapis.com/models:generateContent"
```

#### Principle 2: Isolated Execution
```bash
# Run swarms in isolated environments
docker run --rm -it \
  -v $(pwd):/workspace \
  -e OPENROUTER_API_KEY \
  sbdk-swarm-env:latest \
  /swarm "..."
```

#### Principle 3: Audit Logging
```bash
# Enable comprehensive logging
export SWARM_AUDIT_LOG=true
export SWARM_LOG_LEVEL=INFO

# Monitor all API calls
tail -f ~/.sbdk/swarm-audit.log
```

### 4.3 Code Quality Enforcement

Every swarm must include:

```bash
✅ Type hints (Python 3.11+)
✅ Docstrings (Google style)
✅ Unit tests (100% coverage target)
✅ Integration tests
✅ Security scanning (bandit, safety)
✅ Code formatting (black, isort)
✅ Linting (ruff, mypy)
✅ Documentation (mkdocs)
```

### 4.4 Review Checklist

Before merging swarm output:

```markdown
## Code Review Checklist

### Functionality
- [ ] Feature works as specified
- [ ] Edge cases handled
- [ ] Error handling comprehensive
- [ ] Performance acceptable (<30s iteration target)

### Quality
- [ ] Test coverage ≥ 95%
- [ ] All tests passing
- [ ] Type hints complete
- [ ] Documentation complete

### Security
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] SQL injection prevention
- [ ] Path traversal prevention

### Integration
- [ ] Backward compatible
- [ ] CLI integration smooth
- [ ] Follows SBDK patterns
- [ ] No breaking changes

### Documentation
- [ ] User guide updated
- [ ] API docs complete
- [ ] Examples working
- [ ] Changelog updated
```

---

## 5. Swarm Workflows

### 5.1 Daily Development Workflow

```bash
# Morning: Start swarm infrastructure
./scripts/start-swarm-infra.sh

# Select task from roadmap
TASK="Implement environment switching (Phase 1.1)"

# Launch development swarm
/swarm "Implement environment switching for SBDK:

REFERENCE: Phase 1.1, SBDK_PLATFORM_VISION.md

DELIVERABLES:
- src/sbdk/environment/switcher.py
- CLI command: sbdk env switch <name>
- Tests with 100% coverage
- Documentation and examples

REQUIREMENTS:
- Switch in <2 seconds
- Validate environment exists
- Update active environment marker
- Preserve previous environment state
"

# Monitor progress
watch -n 5 'cat ~/.sbdk/swarm-status.json | jq'

# Review and merge
git diff
pytest tests/
git commit -m "feat: environment switching"
git push origin claude/env-switching-[session-id]
```

### 5.2 Feature Development Workflow

```bash
# 1. Plan feature with architecture swarm
/swarm "Design architecture for [FEATURE]:

AGENTS:
1. Architect: Design system architecture
2. API Designer: Design public APIs
3. Integration: Design integration points
4. Performance: Identify performance requirements
5. Documenter: Create architecture docs

DELIVERABLES: Architecture doc, API spec, integration plan
"

# 2. Implement with development swarm
/swarm "Implement [FEATURE] using architecture from previous swarm:

AGENTS:
1. Core: Implement main functionality
2. Testing: TDD with comprehensive tests
3. CLI: Add CLI interface
4. Integration: Connect to existing systems
5. Documentation: User guide and examples

DELIVERABLES: Working feature, tests, docs
"

# 3. Quality assurance with QA swarm
/swarm "Quality assurance for [FEATURE]:

AGENTS:
1. Tester: Expand test coverage, edge cases
2. Security: Security audit
3. Performance: Profile and optimize
4. Reviewer: Code review and refactoring
5. Documenter: Improve documentation

DELIVERABLES: Optimized code, security report, performance metrics
"

# 4. Prepare for release
/swarm "Prepare [FEATURE] for release:

AGENTS:
1. Packager: Update setup.py, dependencies
2. Documenter: Update changelog, migration guide
3. Tester: Full integration test suite
4. Reviewer: Final code review
5. Release: Prepare release notes and tags

DELIVERABLES: Release-ready code, documentation, release notes
"
```

### 5.3 Bug Fix Workflow

```bash
# 1. Reproduce and diagnose
/swarm "Diagnose and fix bug [BUG_ID]:

DESCRIPTION: [Bug description]

AGENTS:
1. Reproducer: Create minimal reproduction case
2. Debugger: Root cause analysis
3. Fixer: Implement fix with tests
4. Regression: Add regression tests
5. Documenter: Update docs if needed

DELIVERABLES:
- Reproduction test case
- Root cause analysis report
- Fix with tests
- Regression test suite
"

# 2. Verify fix doesn't break anything
pytest tests/ -v
sbdk pipeline run --test

# 3. Fast-track merge for critical bugs
git commit -m "fix: [BUG_DESCRIPTION]"
git push origin claude/hotfix-[bug-id]-[session-id]
```

### 5.4 Refactoring Workflow

```bash
/swarm "Refactor [COMPONENT] for better performance/maintainability:

CURRENT STATE: [Description]
TARGET STATE: [Desired improvements]

AGENTS:
1. Analyzer: Identify refactoring opportunities
2. Refactorer: Implement refactoring
3. Tester: Ensure tests still pass, add new ones
4. Performance: Benchmark before/after
5. Documenter: Update documentation

CONSTRAINTS:
- Must maintain backward compatibility
- All existing tests must pass
- Performance must improve or stay same
- No new dependencies

DELIVERABLES:
- Refactored code
- Performance comparison
- Updated tests and docs
"
```

---

## 6. Monitoring & Quality

### 6.1 Swarm Performance Metrics

Track swarm effectiveness:

```bash
# Metrics to monitor
{
  "swarm_session": "abc123",
  "start_time": "2025-01-08T10:00:00Z",
  "end_time": "2025-01-08T10:45:00Z",
  "duration_minutes": 45,
  "agents_spawned": 5,
  "tasks_completed": 12,
  "tests_written": 47,
  "test_coverage": 98.5,
  "code_quality_score": 9.2,
  "api_calls": {
    "openrouter": 234,
    "gemini": 89,
    "anthropic": 156
  },
  "cost_usd": 2.34,
  "deliverables": [
    "src/sbdk/environment/switcher.py",
    "tests/test_environment_switcher.py",
    "docs/environment-management.md"
  ],
  "quality_gates_passed": true
}
```

### 6.2 Quality Gates

Every swarm output must pass:

```bash
# 1. Tests
pytest tests/ --cov=sbdk --cov-report=term-missing --cov-fail-under=95

# 2. Type checking
mypy src/sbdk --strict

# 3. Linting
ruff check src/sbdk tests/
black --check src/sbdk tests/

# 4. Security
bandit -r src/sbdk -ll
safety check

# 5. Documentation
mkdocs build --strict

# 6. Performance
pytest tests/test_performance.py --benchmark-only

# 7. Integration
sbdk pipeline run --test --env ci
```

### 6.3 Continuous Improvement

After each swarm session:

```bash
# 1. Review metrics
cat ~/.sbdk/swarm-metrics.json | jq '.[-1]'

# 2. Identify improvements
- What went well?
- What could be better?
- Any blockers or issues?

# 3. Update swarm patterns
# Update CLAUDE_SWARM_BUILDER.md with learnings

# 4. Share knowledge
# Document in team wiki or discussions
```

---

## 7. Swarm Templates

### 7.1 Quick Start Commands

```bash
# Environment Management
/swarm "Implement environment switching (Phase 1.1) - See SBDK_PLATFORM_VISION.md Section 7.2"

# Data Sources
/swarm "Implement PostgreSQL connector (Phase 1.2) - See SBDK_PLATFORM_VISION.md Section 7.2"

# Pipeline Engine
/swarm "Implement incremental processing (Phase 1.3) - See SBDK_PLATFORM_VISION.md Section 7.2"

# Quality Framework
/swarm "Implement data profiling (Phase 2.1) - See SBDK_PLATFORM_VISION.md Section 7.3"

# Testing
/swarm "Implement regression testing (Phase 2.2) - See SBDK_PLATFORM_VISION.md Section 7.3"

# Developer Tools
/swarm "Implement hot-reload server (Phase 2.3) - See SBDK_PLATFORM_VISION.md Section 7.3"

# MCP Server
/swarm "Implement MCP server (Phase 3.1) - See SBDK_PLATFORM_VISION.md Section 7.4"

# CI/CD
/swarm "Create GitHub Actions templates (Phase 3.2) - See SBDK_PLATFORM_VISION.md Section 7.4"

# VS Code Extension
/swarm "Build VS Code extension (Phase 3.3) - See SBDK_PLATFORM_VISION.md Section 7.4"
```

### 7.2 Advanced Swarm Compositions

#### Multi-Phase Swarm
```bash
/swarm "Multi-phase implementation of Environment Management:

PHASE 1 - Architecture (1 hour)
- Design environment configuration schema
- Design switching mechanism
- Design template system
- Design validation rules
- Produce: Architecture doc

PHASE 2 - Core Implementation (2 hours)
- Implement Environment class
- Implement ProfileManager
- Implement TemplateEngine
- Implement validation
- Include: Comprehensive tests
- Produce: Working core system

PHASE 3 - CLI Integration (1 hour)
- Implement CLI commands
- Add rich output formatting
- Add error handling
- Include: CLI tests
- Produce: User-facing commands

PHASE 4 - Quality & Docs (1 hour)
- Expand test coverage to 100%
- Performance optimization
- Security review
- Documentation and examples
- Produce: Production-ready feature

TOTAL TIME: 5 hours
AGENTS: Rotate 5 agents through phases
QUALITY GATES: All must pass between phases
"
```

#### Parallel Feature Swarms
```bash
# Launch multiple swarms in parallel
/swarm-parallel "
  Swarm 1: Implement PostgreSQL connector (Phase 1.2)
  Swarm 2: Implement CSV file connector (Phase 1.2)
  Swarm 3: Implement API connector (Phase 1.2)

  Each swarm has 5 agents
  All follow same connector interface
  All produce same deliverables structure
  Coordinate via AgentDB for interface consistency
"
```

---

## 8. Success Metrics

### 8.1 Development Velocity

Target metrics for swarm-assisted development:

- **Feature completion**: 3-5x faster than solo development
- **Code quality**: Maintained at 95%+ test coverage
- **Bug density**: <1 bug per 1000 lines of code
- **Documentation**: 100% of public APIs documented
- **Time to production**: 50% reduction

### 8.2 Platform Alignment

Every swarm output must align with:

- ✅ **Local-first principle**: No cloud dependencies for core features
- ✅ **30-second iteration**: Fast feedback loops maintained
- ✅ **Production parity**: Local dev mirrors production
- ✅ **Developer experience**: Intuitive, well-documented APIs
- ✅ **Foundation focus**: Build core, integrate with specialists

### 8.3 Quality Standards

- **Test Coverage**: ≥95% for all new code
- **Performance**: <30s for typical development iterations
- **Documentation**: All features documented with examples
- **Security**: Zero critical vulnerabilities
- **Compatibility**: Backward compatible releases

---

## 9. Getting Started

### 9.1 First Swarm Session

```bash
# 1. Set up environment
export OPENROUTER_API_KEY="sk-or-v1-xxxxx"  # Optional
cd /path/to/sbdk-dev

# 2. Start swarm infrastructure
npx agentic-flow &
npx claude-flow@alpha &
npx agentdb &

# 3. Verify services
sleep 10
curl http://localhost:3000/health

# 4. Launch first swarm (simple task)
/swarm "Create a simple utility function for SBDK:

TASK: Implement get_project_root() function
LOCATION: src/sbdk/utils/project.py
REQUIREMENTS:
- Find .sbdk directory or pyproject.toml
- Return Path object
- Handle errors gracefully
- Include tests and docs

This is a test swarm to verify infrastructure.
"

# 5. Review results
ls -la src/sbdk/utils/project.py
pytest tests/test_utils.py -v

# 6. If successful, proceed with roadmap tasks
```

### 9.2 Recommended Learning Path

1. **Week 1**: Small utility functions and bug fixes
2. **Week 2**: Single-component features (e.g., one connector)
3. **Week 3**: Multi-component features (e.g., full environment system)
4. **Week 4**: Complex integrations (e.g., MCP server)

### 9.3 Support & Resources

- **Platform Vision**: [SBDK_PLATFORM_VISION.md](./SBDK_PLATFORM_VISION.md)
- **Current Codebase**: [src/sbdk/](./src/sbdk/)
- **Tests**: [tests/](./tests/)
- **Documentation**: [docs/](./docs/)
- **Issues**: [GitHub Issues](https://github.com/sbdk-dev/sbdk-dev/issues)

---

## 10. Conclusion

The Claude Swarm Builder enables rapid, high-quality development of the SBDK platform according to our vision. By leveraging concurrent multi-agent swarms with built-in quality assurance, we can:

- **Accelerate development**: 3-5x faster feature delivery
- **Maintain quality**: 100% test coverage, comprehensive docs
- **Stay aligned**: Every feature maps to platform vision
- **Scale efficiently**: Parallel development across roadmap phases

**Next Steps**:
1. Set up swarm infrastructure
2. Start with Phase 1 milestones
3. Monitor metrics and iterate
4. Scale to parallel swarms for Phase 2+

---

*Document Version: 1.0*
*Last Updated: January 2025*
*Next Review: After first major swarm implementation*
