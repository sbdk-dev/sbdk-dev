# SBDK Unified Project Setup

## Installation

1. **Install the package in development mode:**
   ```bash
   cd sbdk-unified
   pip install -e .
   ```

2. **Verify CLI installation:**
   ```bash
   sbdk --help
   ```

3. **Run tests to validate setup:**
   ```bash
   pytest tests/
   ```

## Using the Fixes

### Email Uniqueness Fix
Copy `examples/my_project_fixed/test_email_uniqueness_fix.py` to your project and run:
```bash
python test_email_uniqueness_fix.py
```

### Enhanced DBT Runner
Copy `examples/my_project_fixed/run_dbt_fixed.py` and use it instead of direct DBT calls:
```bash
python run_dbt_fixed.py --debug run
```

### Project Structure
Use the examples in `examples/` as templates for your own projects.

## Development

To contribute or modify:
1. Make changes to the sbdk/ package
2. Run tests: `pytest tests/`
3. Test CLI: `sbdk --help`
4. Build package: `python -m build`
