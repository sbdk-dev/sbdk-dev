# Data Directory

This directory is used for local DuckDB database files created by SBDK projects.

## Purpose

When you run `sbdk run`, DuckDB database files (`.duckdb`) will be created here based on your project configuration in `sbdk_config.json`.

## What Goes Here

- Local DuckDB database files
- Temporary data files during pipeline execution
- Analytics query results (optional)

## .gitignore

Database files (`.duckdb`) should be added to your `.gitignore` to avoid committing large binary files to version control.

## Example

After running a pipeline, you might see:
```
data/
├── README.md
├── my_project.duckdb    # Main database file
└── my_project.duckdb.wal # Write-ahead log (temporary)
```

## Cleanup

To start fresh, you can safely delete `.duckdb` files in this directory. They will be recreated on the next pipeline run.
