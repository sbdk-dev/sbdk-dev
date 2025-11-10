# ✅ Swarm Setup Checklist

## Quick Setup
```bash
□ Run: ./quickstart.sh
□ See: "✅ Ready to Spawn Swarms!"
□ Test: /swarm "TDD: Create simple test function"
```

## Service Health
```bash
□ Port 3000: agentic-flow ✅
□ Port 3001: claude-flow ✅
□ Port 3002: agentdb ✅
```

## First Swarm
```bash
□ Copy command from examples.md
□ Paste in Claude Code Web
□ See agents working
□ Review generated code
□ Run tests: pytest tests/ -v
```

## Optional: API Keys
```bash
□ Create limited keys (time/rate/cost)
□ Add to Claude Code Web env panel:
  OPENROUTER_API_KEY=sk-or-v1-xxxxx
  GEMINI_API_KEY=xxxxx
□ Test with enhanced swarm
```

---

## If Issues

**Services not starting?**
```bash
killall node
./quickstart.sh
```

**Swarm not responding?**
```bash
curl http://localhost:3000/health
curl http://localhost:3001/health
curl http://localhost:3002/health
```

**Need to stop services?**
```bash
pkill -f agentic-flow
pkill -f claude-flow
pkill -f agentdb
```

---

## SPARC+TDD Verification

Every swarm output should have:
- ✅ Specification document
- ✅ Pseudocode design
- ✅ Architecture description
- ✅ Refinement notes
- ✅ Tests written FIRST
- ✅ 100% test coverage
- ✅ All tests passing

---

**Ready?** Start building with `./quickstart.sh`! 🚀