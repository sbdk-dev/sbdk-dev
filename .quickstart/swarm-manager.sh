#!/bin/bash

# 🌊 SBDK Unified Swarm Manager
# Orchestrates agentic-flow, claude-flow@alpha hive-mind, and agentdb
# Version: 1.0

set -e

COMMAND=${1:-"start"}
TASK=${2:-""}

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service configuration
AGENTIC_FLOW_PORT=3000
CLAUDE_FLOW_PORT=3001
AGENTDB_PORT=3002

# PID file management
PID_DIR="$HOME/.sbdk/swarm-pids"
mkdir -p "$PID_DIR"

function print_header() {
    echo -e "${BLUE}
╔════════════════════════════════════════════════════╗
║     🌊 SBDK Unified Swarm Management System        ║
║   agentic-flow + claude-flow@alpha + agentdb      ║
╚════════════════════════════════════════════════════╝${NC}"
}

function start_services() {
    print_header

    echo -e "${YELLOW}📍 Cleaning up any existing services...${NC}"
    stop_services silent

    echo -e "${GREEN}🚀 Starting swarm infrastructure...${NC}"

    # Start agentic-flow
    echo -e "${BLUE}  → Starting agentic-flow on port $AGENTIC_FLOW_PORT${NC}"
    npx agentic-flow > "$HOME/.sbdk/agentic-flow.log" 2>&1 &
    echo $! > "$PID_DIR/agentic-flow.pid"

    # Start claude-flow@alpha with hive-mind
    echo -e "${BLUE}  → Starting claude-flow@alpha hive-mind on port $CLAUDE_FLOW_PORT${NC}"
    npx claude-flow@alpha hive-mind > "$HOME/.sbdk/claude-flow.log" 2>&1 &
    echo $! > "$PID_DIR/claude-flow.pid"

    # Start agentdb
    echo -e "${BLUE}  → Starting agentdb on port $AGENTDB_PORT${NC}"
    npx agentdb > "$HOME/.sbdk/agentdb.log" 2>&1 &
    echo $! > "$PID_DIR/agentdb.pid"

    echo -e "${YELLOW}⏳ Waiting for services to initialize...${NC}"
    sleep 10

    check_health
    show_commands
}

function stop_services() {
    local SILENT=${1:-""}

    if [ "$SILENT" != "silent" ]; then
        echo -e "${YELLOW}🛑 Stopping swarm services...${NC}"
    fi

    # Stop services using PID files
    for service in agentic-flow claude-flow agentdb; do
        if [ -f "$PID_DIR/$service.pid" ]; then
            PID=$(cat "$PID_DIR/$service.pid")
            if ps -p $PID > /dev/null 2>&1; then
                kill $PID 2>/dev/null || true
                if [ "$SILENT" != "silent" ]; then
                    echo -e "${GREEN}  ✓ Stopped $service (PID: $PID)${NC}"
                fi
            fi
            rm -f "$PID_DIR/$service.pid"
        fi
    done

    # Fallback: kill by process name
    pkill -f agentic-flow 2>/dev/null || true
    pkill -f claude-flow 2>/dev/null || true
    pkill -f agentdb 2>/dev/null || true

    if [ "$SILENT" != "silent" ]; then
        echo -e "${GREEN}✅ All services stopped${NC}"
    fi
}

function check_health() {
    echo -e "${BLUE}🔍 Checking service health...${NC}"

    local ALL_HEALTHY=true

    # Check agentic-flow
    if curl -s http://localhost:$AGENTIC_FLOW_PORT/health > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ agentic-flow: Running on port $AGENTIC_FLOW_PORT${NC}"
    else
        echo -e "${RED}  ✗ agentic-flow: Not responding on port $AGENTIC_FLOW_PORT${NC}"
        ALL_HEALTHY=false
    fi

    # Check claude-flow
    if curl -s http://localhost:$CLAUDE_FLOW_PORT/health > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ claude-flow: Running on port $CLAUDE_FLOW_PORT${NC}"
    else
        echo -e "${RED}  ✗ claude-flow: Not responding on port $CLAUDE_FLOW_PORT${NC}"
        ALL_HEALTHY=false
    fi

    # Check agentdb
    if curl -s http://localhost:$AGENTDB_PORT/health > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ agentdb: Running on port $AGENTDB_PORT${NC}"
    else
        echo -e "${RED}  ✗ agentdb: Not responding on port $AGENTDB_PORT${NC}"
        ALL_HEALTHY=false
    fi

    if [ "$ALL_HEALTHY" = true ]; then
        echo -e "${GREEN}✅ All services healthy!${NC}"
    else
        echo -e "${YELLOW}⚠️  Some services may need more time to initialize${NC}"
    fi
}

function show_logs() {
    SERVICE=${1:-"all"}

    echo -e "${BLUE}📋 Showing logs...${NC}"

    if [ "$SERVICE" = "all" ] || [ "$SERVICE" = "agentic-flow" ]; then
        echo -e "${YELLOW}=== agentic-flow logs ===${NC}"
        tail -n 20 "$HOME/.sbdk/agentic-flow.log" 2>/dev/null || echo "No logs found"
    fi

    if [ "$SERVICE" = "all" ] || [ "$SERVICE" = "claude-flow" ]; then
        echo -e "${YELLOW}=== claude-flow logs ===${NC}"
        tail -n 20 "$HOME/.sbdk/claude-flow.log" 2>/dev/null || echo "No logs found"
    fi

    if [ "$SERVICE" = "all" ] || [ "$SERVICE" = "agentdb" ]; then
        echo -e "${YELLOW}=== agentdb logs ===${NC}"
        tail -n 20 "$HOME/.sbdk/agentdb.log" 2>/dev/null || echo "No logs found"
    fi
}

function spawn_swarm() {
    local TASK="$1"

    if [ -z "$TASK" ]; then
        echo -e "${RED}Error: Task description required${NC}"
        echo "Usage: ./swarm-manager.sh spawn \"Your task description\""
        exit 1
    fi

    echo -e "${GREEN}🐝 Spawning 5-agent swarm...${NC}"
    echo -e "${BLUE}Task: $TASK${NC}"

    # Check services are running
    check_health

    echo -e "${YELLOW}
To spawn your swarm, use this command in Claude Code Web:

/swarm \"Using SPARC methodology and TDD principles:

TASK: $TASK

AGENTS:
1. Architect: Design system architecture and APIs
2. Developer: Implement with TDD (tests first!)
3. Tester: Ensure 100% test coverage
4. Reviewer: Optimize code and performance
5. Documenter: Create comprehensive docs

DELIVERABLES:
- Tests with 100% coverage
- Implementation passing all tests
- Full documentation
- Code review and optimization

Follow SPARC phases:
S - Specification
P - Pseudocode
A - Architecture
R - Refinement
C - Code (with TDD)
\"${NC}"
}

function show_commands() {
    echo -e "${GREEN}
╔════════════════════════════════════════════════════╗
║           ✅ Swarm Infrastructure Ready!           ║
╚════════════════════════════════════════════════════╝${NC}

${YELLOW}Quick Commands:${NC}

${BLUE}Basic Swarm:${NC}
/swarm \"Build [FEATURE] with SPARC+TDD\"

${BLUE}Environment Management:${NC}
/swarm \"SPARC+TDD: Implement SBDK environment management with dev/staging/prod support\"

${BLUE}Data Connector:${NC}
/swarm \"SPARC+TDD: Build PostgreSQL connector with DLT, sampling, and schema detection\"

${BLUE}MCP Server:${NC}
/swarm \"SPARC+TDD: Create MCP server for AI tool integration on port 3000\"

${GREEN}Management Commands:${NC}
  ./swarm-manager.sh start    - Start all services
  ./swarm-manager.sh stop     - Stop all services
  ./swarm-manager.sh status   - Check service health
  ./swarm-manager.sh logs     - View service logs
  ./swarm-manager.sh spawn \"task\" - Generate swarm command

${YELLOW}Optional API Keys (in Claude Code Web env panel):${NC}
  OPENROUTER_API_KEY=sk-or-v1-xxxxx
  GEMINI_API_KEY=xxxxx

${BLUE}Logs Location:${NC}
  ~/.sbdk/agentic-flow.log
  ~/.sbdk/claude-flow.log
  ~/.sbdk/agentdb.log
"
}

function show_status() {
    print_header
    check_health

    echo -e "${BLUE}
📊 Service Details:${NC}"

    for service in agentic-flow claude-flow agentdb; do
        if [ -f "$PID_DIR/$service.pid" ]; then
            PID=$(cat "$PID_DIR/$service.pid")
            if ps -p $PID > /dev/null 2>&1; then
                echo -e "${GREEN}  $service: Running (PID: $PID)${NC}"
            else
                echo -e "${RED}  $service: Stopped (stale PID file)${NC}"
            fi
        else
            echo -e "${YELLOW}  $service: Not started${NC}"
        fi
    done
}

# Main command router
case "$COMMAND" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 2
        start_services
        ;;
    status)
        show_status
        ;;
    health)
        check_health
        ;;
    logs)
        show_logs "$2"
        ;;
    spawn)
        spawn_swarm "$TASK"
        ;;
    help)
        echo "Usage: ./swarm-manager.sh [command] [options]"
        echo ""
        echo "Commands:"
        echo "  start    - Start all swarm services"
        echo "  stop     - Stop all swarm services"
        echo "  restart  - Restart all services"
        echo "  status   - Show service status"
        echo "  health   - Check service health"
        echo "  logs [service] - Show logs (all|agentic-flow|claude-flow|agentdb)"
        echo "  spawn \"task\" - Generate swarm command for task"
        echo "  help     - Show this help message"
        ;;
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        echo "Use: ./swarm-manager.sh help"
        exit 1
        ;;
esac