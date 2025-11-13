# ⚡ SBDK Swarm Development - Quick Start

## 30-Second Setup

```bash
# 1. Navigate to quickstart
cd .quickstart

# 2. Start infrastructure
./swarm-manager.sh start

# 3. Copy any command from examples.md and paste in Claude Code Web
```

## Essential Commands

### Start Everything
```bash
./swarm-manager.sh start
```

### Your First Swarm
```bash
/swarm "SPARC+TDD: Create simple Python utility with tests"
```

### Build SBDK Feature
```bash
/swarm "SPARC+TDD: Implement SBDK environment management"
```

### Check Status
```bash
./swarm-manager.sh status
```

### Stop Services
```bash
./swarm-manager.sh stop
```

## What You Get

✅ **3 Services Running:**
- agentic-flow (port 3000) - Parallel agents
- claude-flow@alpha (port 3001) - Hive-mind coordination
- agentdb (port 3002) - Persistent memory

✅ **Automatic SPARC+TDD:**
- Every swarm follows best practices
- Tests written first
- 100% coverage enforced

✅ **Security Built-in:**
- Works without API keys
- Optional keys obfuscated through Rust proxy
- Local-first, no data leaves machine

## Next Steps

1. Browse `examples.md` for ready-to-use commands
2. Read `README.md` for full documentation
3. Start building SBDK features!

---

**Questions?** Check troubleshooting in README.md or run:
```bash
./swarm-manager.sh help
```