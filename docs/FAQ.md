# Frequently Asked Questions (FAQ)

## General Questions

### What is SBDK?

SBDK.dev (Sandbox Development Kit) is a local-first data pipeline framework that lets you build, test, and learn data engineering without cloud dependencies or costs. It combines DLT (data loading), DuckDB (analytics database), and dbt (transformations) into a single CLI tool.

### Who is SBDK for?

- **Data Engineers**: Rapid prototyping before production deployment
- **Data Analysts**: Learning SQL and data transformations
- **Students**: Hands-on data engineering education
- **Developers**: Understanding modern data stacks
- **Teams**: Collaborative local development

### Is SBDK production-ready?

SBDK is designed for **local development, prototyping, and learning**. For production:
- Use SBDK to validate your pipeline logic
- Test transformations locally
- Then deploy to production systems (Snowflake, BigQuery, etc.)

### How is SBDK different from...

#### vs. Airflow

| SBDK | Airflow |
|------|---------|
| Local-first, no setup | Requires Docker/Kubernetes |
| Focused on data pipelines | General workflow orchestration |
| Built-in data generation | Requires external data sources |
| Ready in 30 seconds | Setup takes hours |

#### vs. Docker-based solutions

| SBDK | Docker Stack |
|------|--------------|
| Native Python, no containers | Requires Docker |
| < 500MB memory | 4-8GB memory |
| Instant start | Slow container startup |
| Single CLI command | Multi-container orchestration |

#### vs. Cloud platforms (Snowflake, BigQuery)

| SBDK | Cloud Platforms |
|------|----------------|
| 100% local, $0 cost | Requires cloud account |
| Offline development | Internet required |
| Instant iteration | Network latency |
| Learning sandbox | Production systems |

## Installation & Setup

### What are the system requirements?

- **Python**: 3.9 or higher
- **RAM**: 512MB minimum, 1GB recommended
- **Disk**: 1GB free space
- **OS**: Windows, macOS, or Linux

### Do I need Docker?

**No!** SBDK runs natively without Docker or any containers.

### Can I use SBDK without Python?

Yes! Download standalone binaries from [GitHub Releases](https://github.com/sbdk-dev/sbdk-dev/releases):
- Windows: `sbdk-windows-x86_64.exe`
- macOS: `sbdk-macos-universal` (ARM & Intel)
- Linux: `sbdk-linux-x86_64`

### Why use uv instead of pip?

[uv](https://github.com/astral-sh/uv) is 10-11x faster than pip:

```bash
# pip: ~45 seconds
pip install sbdk-dev

# uv: ~4 seconds
uv pip install sbdk-dev
```

Both work perfectly - uv is just faster!

## Data & Databases

### Where is my data stored?

Data is stored in a DuckDB database file:
```
your_project/data/your_project.duckdb
```

DuckDB is an embedded analytics database (like SQLite for analytics).

### How do I view my data?

Three options:

1. **sbdk query**: `sbdk query "SELECT * FROM users"`
2. **query.py helper**: `python query.py --interactive`
3. **DuckDB CLI**: `duckdb data/my_project.duckdb`

### Can I use real data instead of synthetic?

Yes! You can:

1. **Import CSV files**:
   ```sql
   CREATE TABLE my_data AS
   SELECT * FROM read_csv_auto('data.csv')
   ```

2. **Import Parquet files**:
   ```sql
   CREATE TABLE my_data AS
   SELECT * FROM read_parquet('data.parquet')
   ```

3. **Write custom pipelines** to fetch from APIs, databases, etc.

### How do I export data?

```bash
# Export to CSV
sbdk query "
COPY (SELECT * FROM users)
TO 'export/users.csv' (FORMAT CSV, HEADER TRUE)
"

# Export to Parquet
sbdk query "
COPY (SELECT * FROM users)
TO 'export/users.parquet' (FORMAT PARQUET)
"

# Export to JSON
sbdk query "
COPY (SELECT * FROM users)
TO 'export/users.json' (FORMAT JSON)
"
```

### Can I connect to my existing database?

SBDK is designed for local DuckDB development. For external databases:

1. Use SBDK to develop and test your transformations
2. Export the SQL models
3. Deploy to your production database (Snowflake, PostgreSQL, etc.)

## Pipelines & Transformations

### How do I customize data generation?

Edit pipeline files in `pipelines/`:

```python
# pipelines/users.py
@dlt.resource
def users_pipeline():
    for i in range(10000):  # Change row count
        yield {
            "user_id": i + 1,
            "email": fake.email(),
            # Add/remove fields
            "custom_field": "your_value"
        }
```

### How do I add new transformations?

Create SQL files in `dbt/models/`:

```sql
-- dbt/models/marts/my_analysis.sql
SELECT
    category,
    COUNT(*) as count,
    SUM(amount) as total
FROM {{ ref('stg_orders') }}
GROUP BY category
```

### What if I want to use a different database?

DuckDB is embedded and optimized for analytics. For other databases:

1. Develop with SBDK/DuckDB locally
2. Export your dbt models (they're just SQL)
3. Run them on your target database

dbt supports: PostgreSQL, MySQL, Snowflake, BigQuery, Redshift, and more.

## Commands & CLI

### What's the difference between `sbdk run` and `sbdk dev dev`?

- **`sbdk run`**: Standard execution (production-like)
- **`sbdk dev dev`**: Development mode with:
  - Hot reload (auto-restart on file changes)
  - Enhanced logging
  - Better error messages

### Can I run only part of the pipeline?

Yes!

```bash
# Only data generation
sbdk run --pipelines-only

# Only dbt transformations
sbdk run --dbt-only

# Specific dbt model
cd dbt && dbt run --select stg_users
```

### How do I see what will happen before running?

Use `--dry-run`:

```bash
sbdk --dry-run run
```

This shows what would be executed without actually running it.

### Why is my command not found?

After installation, if `sbdk` command isn't found:

```bash
# Try with python -m
python -m sbdk version

# Or with uv
uv run sbdk version

# Add to PATH (if needed)
export PATH="$PATH:$HOME/.local/bin"
```

## Performance

### How fast is SBDK?

Typical performance:
- **Installation**: 4 seconds (uv) or 45 seconds (pip)
- **Project init**: < 1 second
- **Pipeline run**: 10-15 seconds for 85,000 records
- **Query response**: < 100ms for most queries

### How much data can SBDK handle?

DuckDB can handle:
- **Local files**: Multi-GB Parquet/CSV files
- **In-memory**: Limited by your RAM
- **On-disk**: Limited by your disk space

For very large datasets (TB+), consider cloud data warehouses.

### Can I speed up transformations?

Yes!

```bash
# Run models in parallel (dbt)
cd dbt
dbt run --threads 4

# Create indexes for faster queries
sbdk query "CREATE INDEX idx_user_id ON users(user_id)"
```

## Troubleshooting

### "Database is locked" error

This means another process is using the database:

```bash
# Find processes using the database
lsof data/*.duckdb  # macOS/Linux
# On Windows: Close DuckDB clients

# Or use read-only mode
sbdk query --read-only "SELECT * FROM users"
```

### "Module not found" error

Reinstall dependencies:

```bash
pip install --force-reinstall sbdk-dev

# Or with uv
uv pip install --reinstall sbdk-dev
```

### Pipeline fails with import error

Make sure you're in the project directory:

```bash
cd your_project
sbdk run
```

### dbt compilation error

Check your SQL syntax:

```bash
cd dbt
dbt compile
dbt run --select your_model
```

## Integration & Deployment

### Can I use SBDK with Git?

Yes! Version control best practices:

**Commit**:
- ✅ Pipeline files (`pipelines/`)
- ✅ dbt models (`dbt/models/`)
- ✅ Configuration (`sbdk_config.json`)

**Don't commit**:
- ❌ Database files (`data/*.duckdb`)
- ❌ dbt artifacts (`dbt/target/`)
- ❌ Python cache (`__pycache__/`)

Add to `.gitignore`:
```
data/*.duckdb
dbt/target/
dbt/logs/
__pycache__/
*.pyc
.sbdk/
```

### How do I deploy SBDK pipelines to production?

SBDK is for local development. For production:

1. **Export dbt models**:
   ```bash
   cp -r dbt/models/ production_dbt/models/
   ```

2. **Adapt pipelines** for your production data sources
3. **Use production dbt** with your target warehouse
4. **Schedule with Airflow/Dagster/Prefect**

### Can I use SBDK in CI/CD?

Yes! Example GitHub Actions:

```yaml
name: Test Data Pipeline
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install SBDK
        run: pip install sbdk-dev
      - name: Run pipeline
        run: |
          cd your_project
          sbdk run
      - name: Test data quality
        run: |
          cd your_project/dbt
          dbt test
```

### Can I containerize SBDK?

Yes, but you don't need to! If you must:

```dockerfile
FROM python:3.11-slim
RUN pip install sbdk-dev
WORKDIR /app
COPY . .
CMD ["sbdk", "run"]
```

But native Python is simpler and faster.

## Support & Community

### How do I report bugs?

[Open an issue on GitHub](https://github.com/sbdk-dev/sbdk-dev/issues) with:
- SBDK version (`sbdk version`)
- Python version
- Operating system
- Error message
- Steps to reproduce

### How do I request features?

[Open a feature request](https://github.com/sbdk-dev/sbdk-dev/issues/new) or start a [discussion](https://github.com/sbdk-dev/sbdk-dev/discussions).

### How can I contribute?

See the [Developer Guide](DEVELOPER_GUIDE.md) for:
- Setting up development environment
- Running tests
- Submitting pull requests
- Code style guidelines

### Is SBDK open source?

Yes! MIT License. Free to use, modify, and distribute.

**Repository**: https://github.com/sbdk-dev/sbdk-dev

### Who maintains SBDK?

SBDK is community-maintained. Contributions welcome!

## Learning Resources

### I'm new to data engineering. Where should I start?

1. **Install SBDK**: `pip install sbdk-dev`
2. **Follow**: [Getting Started Guide](GETTING_STARTED.md)
3. **Learn SQL**: Practice with `sbdk query --interactive`
4. **Learn dbt**: Edit files in `dbt/models/`
5. **Experiment**: Modify pipelines and see what happens!

### What should I learn next?

After mastering SBDK:

1. **dbt**: https://docs.getdbt.com/
2. **DuckDB**: https://duckdb.org/docs/
3. **Data pipelines**: https://dlthub.com/docs/
4. **Cloud warehouses**: Snowflake, BigQuery, Databricks

### Are there any tutorials?

- [Getting Started](GETTING_STARTED.md) - Your first pipeline
- [User Guide](USER_GUIDE.md) - Comprehensive features
- [API Reference](API_REFERENCE.md) - All commands

## Pricing & Licensing

### How much does SBDK cost?

**FREE!** SBDK is open source under the MIT License.

### What are the limitations?

None! Use SBDK for:
- ✅ Personal projects
- ✅ Commercial use
- ✅ Education
- ✅ Training
- ✅ Prototyping

### Do I need a cloud account?

No! SBDK runs 100% locally. No cloud accounts, no API keys, no billing.

---

**Still have questions?** [Ask in Discussions](https://github.com/sbdk-dev/sbdk-dev/discussions) or [open an issue](https://github.com/sbdk-dev/sbdk-dev/issues).
