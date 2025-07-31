To install and run Claude-Flow v2 Alpha and swarm your SBDK.dev CLAUDE-FLOW-PYTHON.md template, follow these Node.js/NPM-based commands (not Python/uv):

1. Prerequisites
```
# Node.js 18+ and npm 9+ required
node --version
npm --version
```

2. Install Claude Code and Claude-Flow (Global, via npm)
```
# Install Claude Code CLI globally
npm install -g @anthropic-ai/claude-code

# Activate Claude Code with permissions (required for Claude-Flow)
claude --dangerously-skip-permissions

# Install Claude-Flow Alpha globally
npm install -g claude-flow@alpha

# Verify installations
claude --version
claude-flow --version
```

3. Initialize and Run Your Project
```
# (Optional) Initialize a new Claude-Flow project (creates .swarm, memory, etc.)
claude-flow init

# Run Template File
claude-flow templates apply web-development --output CLAUDE.md


# (Optional) Monitor swarm in real time
claude-flow hive monitor --live
```

4. Example: Swarm Orchestration
```
# Orchestrate a build with 5 agents in mesh topology
claude-flow hive init --topology mesh --agents 5

# Run your SBDK.dev orchestration (parallel, with all agents)
claude-flow orchestrate "build SBDK.dev local-first data pipeline with DLT, DuckDB, dbt, FastAPI, uv, Typer, Rich, Dynaconf" --agents 5 --parallel
```

5. (Optional) GitHub Integration, MCP, and Advanced Features
```
# Add Claude-Flow as MCP server to Claude Code
claude mcp add claude-flow npx claude-flow@alpha mcp start

# List available MCP tools
claude-flow mcp tools list

# Enable advanced hooks
claude-flow hooks enable --all
```

6. Troubleshooting
If you see permission errors, try:
```
sudo chown -R $(whoami) ~/.npm
```

If you need to reset everything:
```
claude-flow reset --hard
claude-flow init
```

Summary:

Use npm install -g for all Claude-Flow and Claude-Code installation.
Use claude-flow run CLAUDE-FLOW-PYTHON.md to swarm your project.
All orchestration, agent spawning, and memory is managed by Claude-Flow (Node.js, not Python/uv).
Reference:

Your CLAUDE-FLOW-PYTHON.md, @README.md, and @duckdb-dev-env for project details.
Claude-Flow Wiki for advanced usage.
You are now ready to swarm-build your SBDK.dev project with Claude-Flow!