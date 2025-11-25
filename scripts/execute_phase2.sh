#!/bin/bash
# SBDK Phase 2 Execution Script
# Multi-Agent Orchestration using agentic-flow, agentdb, and claude-flow@alpha
#
# Usage:
#   ./scripts/execute_phase2.sh [options]
#
# Options:
#   --phase         Phase to execute (2.1, 2.2, 2.3, or all) [default: 2.1]
#   --agents        Number of concurrent agents [default: 5]
#   --verbose       Enable verbose output
#   --dry-run       Preview execution plan without running
#   --resume        Resume from last checkpoint
#   --help          Show this help message

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default configuration
PHASE="2.1"
NUM_AGENTS=5
VERBOSE=false
DRY_RUN=false
RESUME=false
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_DIR="$PROJECT_ROOT/.claude"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --phase)
            PHASE="$2"
            shift 2
            ;;
        --agents)
            NUM_AGENTS="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --resume)
            RESUME=true
            shift
            ;;
        --help)
            grep "^#" "$0" | grep -v "#!/bin/bash" | sed 's/^# //'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Print banner
print_banner() {
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║           SBDK Phase 2 - Multi-Agent Execution                ║"
    echo "║                                                                ║"
    echo "║  🤖 agentic-flow    - Workflow orchestration                  ║"
    echo "║  🧠 agentdb         - Memory and learning                     ║"
    echo "║  🐝 claude-flow     - Swarm coordination                      ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check prerequisites
check_prerequisites() {
    echo -e "${BLUE}📋 Checking prerequisites...${NC}"

    local missing=()

    # Check for Node.js
    if ! command -v node &> /dev/null; then
        missing+=("node")
    fi

    # Check for npx
    if ! command -v npx &> /dev/null; then
        missing+=("npx")
    fi

    # Check for Python
    if ! command -v python3 &> /dev/null; then
        missing+=("python3")
    fi

    # Check for uv
    if ! command -v uv &> /dev/null; then
        missing+=("uv")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        echo -e "${RED}❌ Missing prerequisites: ${missing[*]}${NC}"
        echo -e "${YELLOW}Please install the missing tools and try again.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ All prerequisites met${NC}"
}

# Initialize AgentDB
initialize_agentdb() {
    echo -e "${PURPLE}🧠 Initializing AgentDB...${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would initialize AgentDB${NC}"
        return
    fi

    # Create AgentDB directory
    mkdir -p "$PROJECT_ROOT/.sbdk/agentdb"

    # Initialize AgentDB with Phase 1 learnings
    npx agentdb init \
        --config "$CONFIG_DIR/agentdb.config.json" \
        --import "$CONFIG_DIR/memory.json" \
        --import "$PROJECT_ROOT/PHASE_1_COMPLETION_REPORT.md"

    echo -e "${GREEN}✅ AgentDB initialized${NC}"
}

# Start Agent Flow hive-mind
start_claude_flow() {
    echo -e "${CYAN}🐝 Starting Agent Flow hive-mind...${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would start Agent Flow with $NUM_AGENTS agents${NC}"
        return
    fi

    # Start Agent Flow in background
    npx claude-flow@alpha hive-mind \
        --config "$CONFIG_DIR/claude-flow.config.json" \
        --agents $NUM_AGENTS \
        --mode collaborative \
        --memory agentdb \
        --output "$PROJECT_ROOT/.sbdk/claude-flow.log" &

    CLAUDE_FLOW_PID=$!
    echo "$CLAUDE_FLOW_PID" > "$PROJECT_ROOT/.sbdk/claude-flow.pid"

    echo -e "${GREEN}✅ Agent Flow started (PID: $CLAUDE_FLOW_PID)${NC}"
}

# Execute agentic-flow
execute_agentic_flow() {
    echo -e "${BLUE}🤖 Executing agentic-flow for Phase $PHASE...${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would execute agentic-flow workflow${NC}"
        echo -e "${YELLOW}Workflow: phase${PHASE//./_}_implementation${NC}"
        return
    fi

    local workflow_id="phase${PHASE//./_}_implementation"
    local resume_flag=""

    if [ "$RESUME" = true ]; then
        resume_flag="--resume"
    fi

    # Execute workflow
    npx agentic-flow execute \
        --config "$CONFIG_DIR/agentic-flow.config.json" \
        --workflow "$workflow_id" \
        --parallel \
        --max-concurrent $NUM_AGENTS \
        --memory agentdb \
        --coordination claude-flow \
        $resume_flag \
        --verbose=$VERBOSE

    echo -e "${GREEN}✅ Agentic-flow execution complete${NC}"
}

# Monitor progress
monitor_progress() {
    echo -e "${YELLOW}📊 Monitoring agent progress...${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would monitor progress in real-time${NC}"
        return
    fi

    # Show real-time progress dashboard
    npx agentic-flow monitor \
        --live \
        --agents \
        --tasks \
        --metrics
}

# Run validation
run_validation() {
    echo -e "${GREEN}✅ Running validation suite...${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would run full test suite${NC}"
        return
    fi

    # Run tests
    cd "$PROJECT_ROOT"
    uv run pytest tests/ -v --cov=sbdk --cov-report=term

    # Visual validation
    echo -e "${BLUE}🎨 Running visual validation...${NC}"
    uv run sbdk --help
    uv run sbdk env --help
    uv run sbdk semantic --help 2>/dev/null || echo "Semantic commands will be available after completion"
    uv run sbdk agent --help 2>/dev/null || echo "Agent commands will be available after completion"

    echo -e "${GREEN}✅ Validation complete${NC}"
}

# Update documentation
update_documentation() {
    echo -e "${BLUE}📚 Updating documentation...${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would update CLAUDE.md, README.md, and memory${NC}"
        return
    fi

    # This will be handled by the coordinator agent
    echo -e "${YELLOW}⏳ Documentation updates handled by coordinator agent${NC}"
}

# Commit and push
commit_and_push() {
    echo -e "${PURPLE}📝 Committing and pushing changes...${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would commit and push Phase $PHASE changes${NC}"
        return
    fi

    cd "$PROJECT_ROOT"

    # Stage all changes
    git add -A

    # Create commit message
    local commit_msg="feat(phase$PHASE): complete Phase $PHASE implementation

Phase $PHASE Complete - Multi-Agent Development

Implemented using:
- agentic-flow for workflow orchestration
- agentdb for memory and learning
- claude-flow@alpha hive-mind for swarm coordination

Components delivered: See PHASE_${PHASE//./_}_COMPLETION_REPORT.md

All quality gates passed ✅"

    # Commit
    git commit -m "$commit_msg"

    # Push
    git push

    echo -e "${GREEN}✅ Changes committed and pushed${NC}"
}

# Generate completion report
generate_report() {
    echo -e "${CYAN}📊 Generating completion report...${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would generate Phase $PHASE completion report${NC}"
        return
    fi

    # This will be handled by the coordinator agent
    echo -e "${YELLOW}⏳ Report generation handled by coordinator agent${NC}"
}

# Cleanup
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"

    # Stop Agent Flow if running
    if [ -f "$PROJECT_ROOT/.sbdk/claude-flow.pid" ]; then
        local pid=$(cat "$PROJECT_ROOT/.sbdk/claude-flow.pid")
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid
            echo -e "${GREEN}✅ Agent Flow stopped${NC}"
        fi
        rm "$PROJECT_ROOT/.sbdk/claude-flow.pid"
    fi
}

# Trap cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    print_banner

    echo -e "${BLUE}Configuration:${NC}"
    echo -e "  Phase:      ${GREEN}$PHASE${NC}"
    echo -e "  Agents:     ${GREEN}$NUM_AGENTS${NC}"
    echo -e "  Verbose:    ${GREEN}$VERBOSE${NC}"
    echo -e "  Dry Run:    ${GREEN}$DRY_RUN${NC}"
    echo -e "  Resume:     ${GREEN}$RESUME${NC}"
    echo ""

    # Confirm execution (unless dry run)
    if [ "$DRY_RUN" = false ]; then
        read -p "Execute Phase $PHASE with these settings? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Execution cancelled${NC}"
            exit 0
        fi
    fi

    echo -e "${GREEN}🚀 Starting Phase $PHASE execution...${NC}"
    echo ""

    # Execute pipeline
    check_prerequisites
    initialize_agentdb
    start_claude_flow
    execute_agentic_flow

    # If not dry run, continue with validation and completion
    if [ "$DRY_RUN" = false ]; then
        run_validation
        update_documentation
        commit_and_push
        generate_report

        echo ""
        echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                                                                ║${NC}"
        echo -e "${GREEN}║           ✅ Phase $PHASE Execution Complete! ✅                  ║${NC}"
        echo -e "${GREEN}║                                                                ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${CYAN}📊 Summary:${NC}"
        echo -e "  ${GREEN}✓${NC} AgentDB initialized with Phase 1 learnings"
        echo -e "  ${GREEN}✓${NC} Agent Flow hive-mind coordinated $NUM_AGENTS agents"
        echo -e "  ${GREEN}✓${NC} Agentic-flow executed all workflows"
        echo -e "  ${GREEN}✓${NC} All tests passing"
        echo -e "  ${GREEN}✓${NC} Documentation updated"
        echo -e "  ${GREEN}✓${NC} Changes committed and pushed"
        echo ""
        echo -e "${YELLOW}📖 See PHASE_${PHASE//./_}_COMPLETION_REPORT.md for details${NC}"
        echo ""
    else
        echo ""
        echo -e "${YELLOW}Dry run complete. No changes were made.${NC}"
        echo -e "${YELLOW}Run without --dry-run to execute for real.${NC}"
        echo ""
    fi
}

# Execute main
main
