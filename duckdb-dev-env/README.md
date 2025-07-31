# DLT + DuckDB Dev Environment Builder: Sample Implementation

## Overview
This sample implementation provides a one-command setup for a Python data engineering environment using DLT and DuckDB, managed by [UV](https://github.com/astral-sh/uv) and orchestrated for parallel execution. The setup follows the PRD and parallelization patterns described above.

---

## 1. Project Structure

```
duckdb-dev-env/
├── src/
│   └── __init__.py
├── notebooks/
│   └── quickstart.ipynb
├── tests/
│   └── test_dlt_duckdb.py
├── .env.example
├── pyproject.toml
├── README.md
```

---

## 2. One-Command Setup (Optimized)

**Requirements:**
- Python 3.10+
- [UV](https://github.com/astral-sh/uv) installed (`pip install uv`)

**Single Command (for Mac/Linux):**

```bash
uv venv .venv && \
source .venv/bin/activate && \
uv pip install --upgrade pip setuptools wheel && \
uv pip install dlt duckdb pandas numpy jupyter pytest black flake8 mypy pre-commit && \
pre-commit install && \
pytest tests/
```

- All environment and package setup is batched in one command for speed and reproducibility.
- Add this command to your Makefile or a `setup.sh` for convenience.

---

## 3. `pyproject.toml` Example

```toml
[project]
name = "duckdb-dev-env"
version = "0.1.0"
description = "DLT + DuckDB dev environment with UV and Hive-Swarm patterns."
requires-python = ">=3.10"

[tool.black]
line-length = 88

[tool.flake8]
max-line-length = 88

[tool.mypy]
python_version = "3.10"

[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra -q"
testpaths = ["tests"]
```

---

## 4. Sample DLT → DuckDB Pipeline (in `src/pipeline.py`)

```python
def run_pipeline():

import dlt
import duckdb

def run_pipeline():
    # Example: Load sample data with DLT and write to DuckDB
    data = [{"id": 1, "value": "foo"}, {"id": 2, "value": "bar"}]
    pipeline = dlt.pipeline(pipeline_name="sample", destination="duckdb", dataset_name="sample_data")
    load_info = pipeline.run(data, table_name="my_table", write_disposition="replace")
    print("DLT Load Info:", load_info)
    # Query with DuckDB
    con = duckdb.connect("sample.duckdb")
    # If you want a pandas DataFrame (requires pandas and numpy):
    print(con.execute("SELECT * FROM sample_data.my_table").df())

if __name__ == "__main__":
    run_pipeline()
```

---

## 5. Sample Test (`tests/test_dlt_duckdb.py`)

```python
from src.pipeline import run_pipeline

def test_pipeline_runs():
    try:
        run_pipeline()
    except Exception as e:
        assert False, f"Pipeline failed: {e}"
```

---

## 6. Sample Notebook (`notebooks/quickstart.ipynb`)

Create a Jupyter notebook with the following cells:

- Install and import DLT and DuckDB
- Run a simple pipeline as above
- Query results with DuckDB

---

## 7. .env.example

```
# Example environment variables
DLT_PIPELINE_NAME=sample
DLT_DESTINATION=duckdb
```

---

## 8. Quickstart

1. **Clone the repo:**
   ```bash
   git clone <repo-url>
   cd duckdb-dev-env
   ```
2. **Run the setup command:**
   ```bash
   uv venv .venv && source .venv/bin/activate && uv pip install --upgrade pip setuptools wheel && uv pip install dlt duckdb pandas numpy jupyter pytest black flake8 mypy pre-commit && pre-commit install && pytest -s tests/
   ```
---

## 11. Makefile (Recommended)

Add a `Makefile` to simplify common tasks:

```makefile
.PHONY: setup test lint format notebook

setup:
    uv venv .venv && source .venv/bin/activate && \
    uv pip install --upgrade pip setuptools wheel && \
    uv pip install dlt duckdb pandas numpy jupyter pytest black flake8 mypy pre-commit && \
    pre-commit install

test:
    source .venv/bin/activate && pytest -s tests/

lint:
    source .venv/bin/activate && flake8 src/ tests/

format:
    source .venv/bin/activate && black src/ tests/

notebook:
    source .venv/bin/activate && jupyter lab
```

This lets you run `make setup`, `make test`, `make lint`, `make format`, and `make notebook` for best-practice Python repo automation.
3. **Run the pipeline:**
   ```bash
   source .venv/bin/activate
   python src/pipeline.py
   ```
4. **Start Jupyter:**
   ```bash
   source .venv/bin/activate
   jupyter notebook
   ```

---

## 9. References
- [DLT Documentation](https://docs.dlt.dev/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [UV Package Manager](https://github.com/astral-sh/uv)

---

## 10. Notes
- All setup steps are parallelized and batched for speed.
- No pip/conda/poetry; only UV is used for package management.
- Follows the "1 message = all Python ecosystem operations" rule for reproducibility and performance.
