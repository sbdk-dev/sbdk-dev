# 🚀 SBDK Swarm Commands - Ready to Execute

**Quick Start**: Copy any command below and execute it in Claude Code to launch a swarm!

---

## 🎯 Phase 1: Environment Management (START HERE)

### 🔥 FULL PHASE 1.1 - Environment Management System

```
/swarm "Launch swarm infrastructure and implement SBDK Environment Management System:

INFRASTRUCTURE SETUP:
1. Start: npx agentic-flow (background)
2. Start: npx claude-flow@alpha (background)
3. Start: npx agentdb (background)
4. Wait 10 seconds for services to initialize
5. Verify all services are running on localhost

PROJECT CONTEXT:
- Repository: sbdk-dev/sbdk-dev
- Branch: claude/setup-swarm-agents-011CUvjMRBQTmdVf7sckau6U
- Reference: SBDK_PLATFORM_VISION.md Section 7.2 (Phase 1.1)
- Guide: CLAUDE.md for code patterns and standards

MISSION - ENVIRONMENT MANAGEMENT SYSTEM:
Build a complete environment management system that enables developers to create,
switch, and manage multiple SBDK environments (dev/staging/prod) with templates.

AGENTS (5 concurrent):

1. ARCHITECT AGENT - System Design
   - Design Environment class architecture
   - Design EnvironmentManager API
   - Design template system (analytics, ml, basic)
   - Design configuration schema (Pydantic models)
   - Design environment storage (.sbdk/environments/)
   - Output: Architecture document with class diagrams

2. IMPLEMENTATION AGENT - Core Code
   - Implement src/sbdk/environment/manager.py
   - Implement src/sbdk/environment/config.py (Pydantic models)
   - Implement src/sbdk/environment/template.py
   - Implement src/sbdk/environment/switcher.py
   - Include type hints, docstrings (Google style)
   - Output: Working core implementation

3. TESTING AGENT - TDD Excellence
   - Write tests/environment/test_manager.py
   - Write tests/environment/test_config.py
   - Write tests/environment/test_template.py
   - Write tests/environment/test_switcher.py
   - Target: 95%+ coverage
   - Include edge cases, error scenarios
   - Output: Comprehensive test suite

4. CLI AGENT - User Interface
   - Implement src/sbdk/cli/env.py
   - Commands: create, switch, list, status, delete
   - Use Typer + Rich for beautiful output
   - Add --verbose, --quiet, --format options
   - Include shell completion
   - Output: User-friendly CLI commands

5. DOCUMENTATION AGENT - User Guide
   - Write docs/environment-management.md
   - Create user guide with examples
   - Document all CLI commands
   - Add troubleshooting section
   - Create quick-start tutorial
   - Output: Complete documentation

TECHNICAL REQUIREMENTS:

Environment Creation:
- sbdk env create <name> --template <analytics|ml|basic>
- sbdk env create <name> --copy-from <existing>
- Create .sbdk/environments/<name>/ directory
- Generate config.json with Pydantic validation
- Support custom targets (duckdb, postgres, bigquery)

Environment Switching:
- sbdk env switch <name>
- Update .sbdk/active-environment marker
- Validate environment exists
- Must complete in <2 seconds (performance requirement)
- Preserve state of previous environment

Environment Management:
- sbdk env list (show all environments with status)
- sbdk env status (show current environment details)
- sbdk env delete <name> (with confirmation prompt)

Templates:
- analytics: Full-featured with dbt, DLT, DuckDB
- ml: Machine learning focused setup
- basic: Minimal configuration

CODE QUALITY STANDARDS (from CLAUDE.md):
- Python 3.11+ with strict type hints
- Google-style docstrings for all public APIs
- Pydantic models for all configuration
- Comprehensive error handling with SBDKError
- Rich console output with colors and formatting
- 95%+ test coverage
- Black formatting, Ruff linting

DELIVERABLES:

Code Files:
✅ src/sbdk/environment/__init__.py
✅ src/sbdk/environment/manager.py (EnvironmentManager class)
✅ src/sbdk/environment/config.py (Pydantic models)
✅ src/sbdk/environment/template.py (Template engine)
✅ src/sbdk/environment/switcher.py (Environment switcher)
✅ src/sbdk/cli/env.py (CLI commands)

Test Files:
✅ tests/environment/__init__.py
✅ tests/environment/test_manager.py
✅ tests/environment/test_config.py
✅ tests/environment/test_template.py
✅ tests/environment/test_switcher.py
✅ tests/environment/test_cli.py

Documentation:
✅ docs/environment-management.md (User guide)
✅ templates/analytics/ (Template files)
✅ templates/ml/ (Template files)
✅ templates/basic/ (Template files)

Configuration:
✅ Update pyproject.toml if needed
✅ Update CHANGELOG.md

QUALITY GATES (ALL MUST PASS):

1. Tests:
   pytest tests/environment/ -v --cov=sbdk.environment --cov-fail-under=95

2. Type Checking:
   mypy src/sbdk/environment --strict

3. Linting:
   ruff check src/sbdk/environment tests/environment/

4. Formatting:
   black --check src/sbdk/environment tests/environment/

5. Integration Test:
   sbdk env create dev --template analytics
   sbdk env create staging --copy-from dev
   sbdk env switch dev
   sbdk env list
   sbdk env status
   sbdk env delete staging

6. Performance:
   Environment switching must complete in <2 seconds

ALIGNMENT WITH SBDK PRINCIPLES:

✅ Local-First: No cloud dependencies, pure local state management
✅ Rapid Iteration: Fast environment switching enables quick experimentation
✅ Production Parity: dev/staging/prod environments mirror deployment pattern
✅ Developer Experience: Intuitive CLI with helpful error messages
✅ Foundation Focus: Core capability that other features build upon

SUCCESS CRITERIA:

1. ✅ Can create environments with 3 templates (analytics, ml, basic)
2. ✅ Can switch between environments in <2 seconds
3. ✅ All environments are isolated (no cross-contamination)
4. ✅ 95%+ test coverage achieved
5. ✅ All quality gates pass
6. ✅ Documentation complete with examples
7. ✅ CLI is intuitive and helpful
8. ✅ Code follows all SBDK standards from CLAUDE.md

COMMIT STRATEGY:

After completion, create commits:
1. feat(environment): add environment management system core
2. feat(environment): add CLI commands for env management
3. test(environment): add comprehensive test suite
4. docs(environment): add environment management guide

Push to: claude/setup-swarm-agents-011CUvjMRBQTmdVf7sckau6U

ESTIMATED TIME: 2-3 hours for complete implementation with 5 agents working in parallel

NOTES:
- This is the foundation for Phase 1 - get this right!
- Follow CLAUDE.md patterns religiously
- Use existing CLI patterns from src/sbdk/cli/ as reference
- Make error messages helpful with suggestions
- Test on clean environment to ensure setup works
"
```

---

## 🔄 Phase 1.2 - Data Source Connectors

### PostgreSQL Connector

```
/swarm "Implement PostgreSQL data source connector for SBDK:

REFERENCE: SBDK_PLATFORM_VISION.md Section 7.2 (Phase 1.2)
CONTEXT: CLAUDE.md for patterns

AGENTS:
1. Design connector interface and architecture
2. Implement PostgreSQL connector with DLT
3. Add sampling strategies (10%, 1000 rows, etc.)
4. Create comprehensive tests with mocking
5. Write connector documentation and examples

DELIVERABLES:
- src/sbdk/sources/connectors/postgres.py
- tests/sources/test_postgres.py
- docs/connectors/postgresql.md
- CLI: sbdk source add postgres --host <host> --db <name>

QUALITY: 95%+ coverage, full type hints, error handling
"
```

---

## 📦 Quick Test - Simple Feature

### Test Swarm with Simple Utility Function

```
/swarm "Test swarm infrastructure with a simple utility function:

TASK: Create a robust project path utility for SBDK

AGENTS:
1. Design: API design for get_project_root(), validate_project()
2. Implementation: Implement src/sbdk/utils/paths.py
3. Testing: Write comprehensive tests
4. Documentation: Add docstrings and examples
5. Review: Code review and optimization

REQUIREMENTS:
- Find .sbdk directory or pyproject.toml
- Return Path object
- Handle errors gracefully with helpful messages
- Type hints required
- 100% test coverage

DELIVERABLES:
- src/sbdk/utils/paths.py
- tests/utils/test_paths.py
- Full type checking and linting passes

This is a test to verify swarm infrastructure works correctly.
"
```

---

## 🎨 Full Stack Feature - MCP Server

### Phase 3.1 - MCP Server Implementation

```
/swarm "Implement SBDK MCP Server for AI tool integration:

REFERENCE: SBDK_PLATFORM_VISION.md Section 7.4 (Phase 3.1)

AGENTS:
1. MCP Protocol Architect: Design server architecture
2. Core Implementation: Build MCP server with tools
3. Integration Testing: Test with Claude, Cursor
4. Security & Auth: Implement authentication, rate limiting
5. Documentation: API docs, integration guides

MCP TOOLS TO IMPLEMENT:
- execute_query(sql, env): Run SQL queries
- run_pipeline(models, env): Execute dbt models
- get_schema(table): Table introspection
- profile_data(table): Data profiling
- create_environment(name, template): Env creation

DELIVERABLES:
- src/sbdk/mcp/server.py
- src/sbdk/mcp/tools.py
- CLI: sbdk mcp serve --port 3000
- Integration examples for knowDB, Cursor
- Security documentation

QUALITY: Production-ready, secure, well-documented
"
```

---

## 🚀 How to Use These Commands

### Step 1: Choose Your Starting Point

**Recommended Order**:
1. ✅ **Start Here**: Phase 1.1 (Environment Management) - Foundation
2. Phase 1.2 (Data Connectors) - Build on foundation
3. Phase 2.x (Quality & Testing) - Enhance reliability
4. Phase 3.x (Integration) - Ecosystem growth

### Step 2: Set Up Environment (Optional)

```bash
# If using API keys for extended swarm operations
export OPENROUTER_API_KEY="sk-or-v1-xxxxx"  # Optional
export GEMINI_API_KEY="xxxxx"               # Optional

# Set rate limits for safety
export OPENROUTER_RATE_LIMIT=100
export DAILY_COST_LIMIT=10.00
```

### Step 3: Execute Swarm Command

Simply copy the full command block and paste it into Claude Code:

```
/swarm "Launch swarm infrastructure and implement SBDK Environment Management System:
...
[full command from above]
"
```

### Step 4: Monitor Progress

Watch for swarm output showing:
- ✅ Infrastructure services starting
- ✅ Agents spawning and beginning work
- ✅ Code generation progress
- ✅ Tests running
- ✅ Quality gates passing

### Step 5: Verify Results

After swarm completes:

```bash
# Check generated files
ls -la src/sbdk/environment/
ls -la tests/environment/

# Run tests
pytest tests/environment/ -v

# Try the feature
sbdk env create dev --template analytics
sbdk env list
```

---

## 💡 Pro Tips

### Parallel Swarms

Launch multiple swarms for independent features:

```
/swarm-parallel "
  Swarm 1: Implement PostgreSQL connector (Phase 1.2)
  Swarm 2: Implement CSV connector (Phase 1.2)
  Swarm 3: Implement API connector (Phase 1.2)
"
```

### Iterative Development

Start small, then expand:

1. **First**: Test swarm with simple utility
2. **Second**: Single-component feature
3. **Third**: Multi-component system
4. **Fourth**: Full phase implementation

### Quality First

Every swarm includes:
- ✅ TDD with tests first
- ✅ Type hints everywhere
- ✅ Comprehensive error handling
- ✅ Rich CLI output
- ✅ Complete documentation

---

## 🎯 Success Metrics

After Phase 1.1 completion:

```bash
# Should all work:
sbdk env create dev --template analytics    # Creates environment
sbdk env create staging --copy-from dev    # Copies environment
sbdk env switch dev                        # Switches in <2s
sbdk env list                              # Shows all environments
sbdk env status                            # Shows current env details

# Quality metrics:
pytest tests/environment/ --cov --cov-fail-under=95  # ✅ Passes
mypy src/sbdk/environment --strict                   # ✅ Passes
ruff check src/sbdk/environment                      # ✅ Passes
```

---

## 📞 Troubleshooting

### Swarm Infrastructure Not Starting

```bash
# Check if ports are available
lsof -i :3000  # agentic-flow
lsof -i :3001  # claude-flow
lsof -i :3002  # agentdb

# Kill existing processes if needed
killall node

# Restart infrastructure
npx agentic-flow &
npx claude-flow@alpha &
npx agentdb &
```

### Swarm Fails Quality Gates

```bash
# Run quality checks manually
pytest tests/ -v
mypy src/sbdk --strict
ruff check src/sbdk
black src/sbdk

# Fix issues and re-run swarm focusing on fixes
```

### Need to Resume Swarm

```bash
# If swarm was interrupted, you can resume
/swarm "Continue previous environment management implementation:
- Review completed work in src/sbdk/environment/
- Complete any missing deliverables
- Ensure all quality gates pass
"
```

---

**🚀 Ready to Launch!** Pick a command above and paste it into Claude Code to start your SBDK development journey!
