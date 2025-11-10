# 🌊 SBDK Swarm Development - Unified System

> **AI-Powered Development with Claude-Flow, Agentic-Flow, and AgentDB**
>
> Build SBDK features 10x faster using concurrent AI agent swarms

---

## 🚀 Quick Start (30 Seconds)

```bash
# 1. Start swarm infrastructure
./swarm-manager.sh start

# 2. Spawn your first swarm in Claude Code Web
/swarm "SPARC+TDD: Create get_project_root() utility with tests"

# 3. Build real features
/swarm "SPARC+TDD: Implement SBDK environment management system"
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         Claude Code Web Interface            │
│            (Browser or Mobile)               │
└────────────────┬────────────────────────────┘
                 │
        ┌────────▼────────┐
        │  /swarm command │
        └────────┬────────┘
                 │
┌────────────────▼────────────────────────────┐
│         Swarm Orchestration Layer           │
├──────────────────────────────────────────────┤
│  🌊 claude-flow@alpha   │  Port 3001        │
│     └─ Hive-mind mode for coordination     │
├──────────────────────────────────────────────┤
│  🔄 agentic-flow        │  Port 3000        │
│     └─ Agent federation and parallelization │
├──────────────────────────────────────────────┤
│  🧠 agentdb             │  Port 3002        │
│     └─ Persistent memory and learning       │
└──────────────────────────────────────────────┘
                 │
         ┌───────▼───────┐
         │ Rust Proxy    │
         │ (Key Safety)  │
         └───────┬───────┘
                 │
    ┌────────────▼────────────┐
    │  Optional: External APIs │
    │  OpenRouter / Gemini     │
    └──────────────────────────┘
```

---

## 🎯 Core Concepts

### The Three Services

1. **claude-flow@alpha (Hive-Mind)**
   - Coordinates multi-agent collaboration
   - Manages task distribution
   - Ensures consistency across agents

2. **agentic-flow (Federation)**
   - Enables parallel agent execution
   - Handles agent specialization
   - Manages resource allocation

3. **agentdb (Memory)**
   - Persistent storage across sessions
   - Pattern learning and recognition
   - Cross-agent knowledge sharing

### SPARC + TDD Methodology

Every swarm automatically follows:

```
SPARC Phases:
S - Specification (define requirements)
P - Pseudocode (design algorithm)
A - Architecture (structure components)
R - Refinement (optimize design)
C - Code (implement with TDD)

TDD Cycle:
1. Red - Write failing tests
2. Green - Implement to pass
3. Refactor - Optimize code
```

---

## 📋 Swarm Management Commands

```bash
# Service Management
./swarm-manager.sh start      # Start all services
./swarm-manager.sh stop       # Stop all services
./swarm-manager.sh restart    # Restart services
./swarm-manager.sh status     # Check service status
./swarm-manager.sh health     # Health check
./swarm-manager.sh logs       # View logs

# Swarm Spawning
./swarm-manager.sh spawn "Build PostgreSQL connector"
# Generates ready-to-use /swarm command
```

---

## 🚀 Ready-to-Use Swarm Commands

### Environment Management System
```bash
/swarm "Using SPARC methodology and TDD:

Build SBDK Environment Management System:

SPECIFICATION:
- Multi-environment support (dev/staging/prod)
- Fast switching (<2 seconds)
- Template system (analytics, ml, basic)
- Store in .sbdk/environments/

AGENTS:
1. Architect: Design EnvironmentManager class
2. Developer: TDD implementation
3. Tester: 100% test coverage
4. Reviewer: Performance optimization
5. Documenter: User guide and API docs

DELIVERABLES:
- src/sbdk/environment/ module
- CLI commands (env create/switch/list)
- Complete test suite
- Documentation"
```

### PostgreSQL Data Connector
```bash
/swarm "SPARC+TDD: PostgreSQL Connector

Build DLT-based PostgreSQL connector with:
- Connection pooling
- Smart sampling (10%, 1000 rows)
- Schema auto-detection
- Error recovery
- CLI integration

Test with mocks, 100% coverage required"
```

### MCP Server for AI Tools
```bash
/swarm "SPARC+TDD: MCP Server Implementation

Create MCP server exposing SBDK tools:
- execute_query(sql, env)
- run_pipeline(models)
- get_schema(table)
- profile_data(table)

Port 3000, include authentication"
```

---

## 🔐 Security Features

### Default (No API Keys)
- ✅ Works with Claude Code Web's built-in capabilities
- ✅ All processing happens locally
- ✅ No data leaves your machine

### Optional API Keys
```bash
# In Claude Code Web environment panel
OPENROUTER_API_KEY=sk-or-v1-xxxxx  # Limited scope
GEMINI_API_KEY=xxxxx                # Time-limited
```

**Security Notes:**
- Keys obfuscated through Rust proxy
- Never shared directly with LLMs
- Create keys with strict limits (time, rate, cost)
- Revoke after development session

---

## 📊 Service Health Monitoring

```bash
# Check individual service
curl http://localhost:3000/health  # agentic-flow
curl http://localhost:3001/health  # claude-flow
curl http://localhost:3002/health  # agentdb

# View logs
tail -f ~/.sbdk/agentic-flow.log
tail -f ~/.sbdk/claude-flow.log
tail -f ~/.sbdk/agentdb.log

# Check running processes
./swarm-manager.sh status
```

---

## 🎓 Best Practices

### 1. Always Use SPARC+TDD
```bash
# Good - Methodology enforced
/swarm "SPARC+TDD: Build feature X with tests first"

# Bad - No methodology
/swarm "Build feature X"
```

### 2. Specify Deliverables
```bash
/swarm "Build [FEATURE]

DELIVERABLES:
- Implementation with type hints
- Tests with 100% coverage
- Documentation
- CLI integration"
```

### 3. Set Performance Targets
```bash
/swarm "Build environment switcher

REQUIREMENTS:
- Switch in <2 seconds
- Memory usage <100MB
- Support 1000+ environments"
```

---

## 🐛 Troubleshooting

### Services Won't Start
```bash
# Clean restart
./swarm-manager.sh stop
killall node  # Force stop if needed
./swarm-manager.sh start
```

### Port Conflicts
```bash
# Check what's using ports
lsof -i :3000
lsof -i :3001
lsof -i :3002

# Change ports in swarm-manager.sh if needed
```

### Swarm Not Responding
```bash
# Check service health
./swarm-manager.sh health

# View logs for errors
./swarm-manager.sh logs

# Restart services
./swarm-manager.sh restart
```

---

## 📁 Directory Structure

```
.quickstart/
├── README.md           # This file
├── swarm-manager.sh    # Unified service manager
├── examples/           # Example swarm commands
│   ├── environment.md
│   ├── connectors.md
│   └── mcp-server.md
└── logs/              # Service logs
```

---

## 🎯 Success Metrics

Every swarm output should have:
- ✅ SPARC phases documented
- ✅ Tests written FIRST (TDD)
- ✅ 100% test coverage
- ✅ Type hints on all functions
- ✅ Comprehensive documentation
- ✅ Performance within targets
- ✅ Clean code (linted, formatted)

---

## 🚦 Quick Decision Guide

### When to Use Swarms

**YES for:**
- New feature development
- Complex refactoring
- Multi-component systems
- When you need parallel work

**NO for:**
- Simple bug fixes
- Documentation updates
- Configuration changes
- Single-function additions

---

## 📚 Learn More

- **SBDK Vision**: [SBDK_PLATFORM_VISION.md](../SBDK_PLATFORM_VISION.md)
- **Architecture**: See Phase 1-3 roadmap
- **Examples**: Browse `examples/` directory
- **Support**: GitHub Issues

---

**Ready to build?** Run `./swarm-manager.sh start` and spawn your first swarm! 🚀