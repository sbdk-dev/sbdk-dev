Claude Code Configuration for Python Projects

🚨 CRITICAL: PYTHON PARALLEL EXECUTION PATTERNS
MANDATORY RULE: Python projects require virtual environment coordination with uv parallel operations.

🚨 CRITICAL: CONCURRENT EXECUTION FOR ALL PYTHON OPERATIONS
ABSOLUTE RULE: ALL Python operations MUST be concurrent/parallel in a single message.

🔴 MANDATORY CONCURRENT PATTERNS FOR PYTHON (SBDK.dev, UV, FastAPI ONLY):
- Virtual Environment: ALWAYS batch ALL venv setup in ONE message.
- Package Management: ALWAYS batch ALL uv install commands together.
- FastAPI Operations: ALWAYS batch ALL FastAPI framework commands.
- Testing: ALWAYS run ALL test suites in parallel (pytest, unittest).
- Data Science: ALWAYS batch ALL Jupyter/pandas operations.

⚡ PYTHON GOLDEN RULE: "1 MESSAGE = ALL PYTHON ECOSYSTEM OPERATIONS (USING UV + FASTAPI ONLY)"

---

# 📦 SBDK.dev Project Context

**Reference:**  
- See `@README.md` for the full PRD, CLI/UX, and directory structure.
- See `@duckdb-dev-env/` for a complete DLT + DuckDB + dbt pipeline example.

**Goal:**  
Build an open source, local-first data pipeline sandbox using DLT, DuckDB, dbt, and FastAPI, with a modern CLI (Typer, Rich), config (Dynaconf), and uv for all dependency management.  
This is the foundation for a future SaaS with AI/LLM agent support.
Use Context7 MCP server for accurate, up-to-date code docs and examples.

---

# 🔧 Rich Project Setup (Swarm Pattern)

[BatchTool]:
  - Bash("python3 -m venv .venv")
  - Bash("source .venv/bin/activate && uv pip install --upgrade pip")
  - Bash("uv pip install fastapi uvicorn duckdb pandas faker dbt-core typer rich dynaconf httpx")
  - Write("requirements.txt", requirementsContent)  # See @README.md for full list
  - Write("main.py", mainPyContent)                 # Typer CLI, see @README.md
  - Write("fastapi_server/webhook_listener.py", webhookListenerContent)  # See @README.md
  - Write("cli/init.py", cliInitContent)
  - Write("cli/dev.py", cliDevContent)
  - Write("cli/start.py", cliStartContent)
  - Write("cli/webhooks.py", cliWebhooksContent)
  - Write("pipelines/users.py", usersPipelineContent)    # See @duckdb-dev-env
  - Write("pipelines/events.py", eventsPipelineContent)  # See @duckdb-dev-env
  - Write("pipelines/orders.py", ordersPipelineContent)  # See @duckdb-dev-env
  - Write("dbt/dbt_project.yml", dbtProjectContent)      # See @duckdb-dev-env
  - Write("dbt/models/staging/stg_users.sql", stgUsersContent)
  - Write("dbt/models/staging/stg_events.sql", stgEventsContent)
  - Write("dbt/models/intermediate/int_user_activity.sql", intUserActivityContent)
  - Write("dbt/models/marts/user_metrics.sql", userMetricsContent)
  - Write("sbdk_config.json", configContent)
  - Write("README.md", readmeContent)                   # Full PRD, see @README.md
  - Write("LICENSE", licenseContent)
  - Bash("uv pip install pytest black flake8")
  - Bash("pytest tests/")
  - Bash("black --check .")
  - Bash("flake8 .")

---

# 🐝 Swarm Agent Specialization

- **CLI Agent:** Typer, Rich, Dynaconf, project orchestration.
- **Data Pipeline Agent:** DLT + DuckDB, synthetic data, see @duckdb-dev-env.
- **DBT Agent:** dbt-core, model/test orchestration, see @duckdb-dev-env.
- **FastAPI Agent:** Webhook/tracking server, see @README.md.
- **AI Agent:** CLI stub for pipeline suggestion/test generation.
- **Config Agent:** Dynaconf/JSON config.

All agents operate in parallel, coordinated by a single CLAUDE.md message.

---

# 🧪 Testing & Quality (UV ONLY)

[BatchTool]:
  - Bash("uv pip install pytest black flake8")
  - Bash("pytest tests/")
  - Bash("black --check .")
  - Bash("flake8 .")

---

# 📝 Best Practices

- **All package management is via uv only.**
- **All backend is FastAPI only.**
- **All setup, install, and test steps are batched in a single message.**
- **Reference @README.md for project goals, UX, and structure.**
- **Reference @duckdb-dev-env for DLT + DuckDB + dbt pipeline patterns.**

---

# 🚀 Quick Start (from @README.md)

```sh
python3 -m venv .venv
source .venv/bin/activate
uv pip install --upgrade pip
uv pip install -r requirements.txt
python main.py init my_project
cd my_project
python ../main.py dev
python ../main.py webhooks  # optional


📚 References
@README.md: Full SBDK.dev PRD, CLI, and UX.
@duckdb-dev-env: Example DLT + DuckDB + dbt pipeline code.
https://github.com/astral-sh/uv: uv package manager.
https://fastapi.tiangolo.com/: FastAPI docs.

Remember:
Batch all uv operations, use only FastAPI for backend, and follow the swarm pattern for all Python ecosystem tasks. Reference your README and duckdb-dev-env for all implementation details.