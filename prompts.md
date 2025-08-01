Reference:
Build my open source SBDK.dev offering. SBDK.dev is a developer sandbox framework designed for local-first data pipeline development using DLT, DuckDB, and dbt. It includes synthetic data ingestion, transform pipelines, local execution tooling, a CLI, and webhook support. It’s the foundation for a future commercial SaaS version built on Snowflake Native Apps with AI-assisted development, sandbox orchestration, and telemetry. Reference the self-contained @duckdb-dev-env/ folder of a complete dlt + duckdb pipeline. My spec is in @README.md. use context7 mcp server to pull accurate examples and docs. 



# Create complete full-stack app

claude-flow hive-mind spawn \
  "Build my open source SBDK.dev offering. SBDK.dev is a developer sandbox framework designed for local-first data pipeline development using DLT, DuckDB, and dbt. It includes synthetic data ingestion, transform pipelines, local execution tooling, a CLI, and webhook support. It’s the foundation for a future commercial SaaS version built on Snowflake Native Apps with AI-assisted development, sandbox orchestration, and telemetry. Reference the self-contained @duckdb-dev-env/ folder of a complete dlt + duckdb pipeline. My spec is in @README.md. use context7 mcp server to pull accurate examples and docs. @CLAUDE-FLOW-PYTHON.md is our project development and execution template." \
  --agents 8 --topology hierarchical --parallel --auto-scale --auto-spawn --claude



# prompt 2: fix dbt error and optimize flow
```

claude-flow hive-mind spawn " fix the flow. in the cli, dbt fails, if run from the console, it works. reference the log in @../error.md" --auto-spawn --claude

```


# prompt 3:

```
claude-flow hive-mind spawn \
"the project now builds, but doesn't match a real flow where the user wants to import their own dbt repo. take all the learnings from @my_project and optimize @sbdk-starter. Do I still need @duckdb-dev-env? Or is that redundant. If so, delete. THen update the @docs, @README.md. Then build my cli app as a package so I can test it better. also, the CLI should accept input and run all commands from the starter not the new my_project, correct? a CLI isn't a nice visual output, it's interactive."\
--agents 8 --topology hierarchical --parallel --auto-scale --auto-spawn --claude
```

# prompt 4:
```
<!-- claude-flow hive-mind spawn \ -->

npx claude-flow@alpha sparc mode --type "neural-tdd" --auto-learn
npx claude-flow@alpha sparc workflow --phases "all" --ai-guided --memory-enhanced

"review the errors in @error.md. the cli doesn't build and there are still errors. package everything up into a single folder. evaluate @my_project/ and @sbdk-starter/demo_project. Since we fixed @my_project, are their things in demo_project that need to be updated? and add a robust readme for the project. then run end to end tests and make sure the project works as expected. " \
  --strategy parallel \
  --auto-spawn \ 
  -- auto-scale

# Monitor progress in real-time
npx claude-flow@alpha swarm monitor --dashboard --real-time
```

<!-- # Deploy complete development swarm
npx claude-flow@alpha hive-mind spawn "Build e-commerce platform with React, Node.js, and PostgreSQL" \
  --agents 10 \
  --strategy parallel \
  --memory-namespace ecommerce -->

# Monitor progress in real-time
npx claude-flow@alpha swarm monitor --dashboard --real-time