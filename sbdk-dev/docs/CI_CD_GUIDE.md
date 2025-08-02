# 🚀 CI/CD Guide for SBDK.dev v2.0.0

## Overview

This guide provides comprehensive CI/CD configuration for SBDK.dev projects using modern tooling with **uv** for ultra-fast package management and **GitHub Actions** for automated testing, building, and deployment.

## 🎯 Benefits of uv-based CI/CD

- **⚡ 10-100x faster** than pip-based workflows
- **🔒 Deterministic builds** with lockfile support
- **📦 Modern dependency resolution** with conflict detection
- **🛠️ Integrated tooling** for linting, testing, and building
- **💾 Efficient caching** for faster CI runs

---

## 📋 Sample GitHub Actions Workflow

Create `.github/workflows/ci.yml` in your SBDK project:

```yaml
name: 🧪 SBDK.dev CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  release:
    types: [ published ]

env:
  PYTHON_VERSION: "3.11"
  UV_CACHE_DIR: /tmp/.uv-cache

jobs:
  test:
    name: 🧪 Test Suite
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]
        
    steps:
    - name: 📥 Checkout code
      uses: actions/checkout@v4
      
    - name: ⚡ Install uv
      uses: astral-sh/setup-uv@v3
      
    - name: 🐍 Set up Python ${{ matrix.python-version }}
      run: uv python install ${{ matrix.python-version }}
      
    - name: 📦 Restore uv cache
      uses: actions/cache@v4
      with:
        path: ${{ env.UV_CACHE_DIR }}
        key: uv-${{ runner.os }}-${{ hashFiles('**/uv.lock') }}
        
    - name: 🔧 Install dependencies
      run: uv sync --group dev
      
    - name: 🔍 Lint with ruff
      run: uv run ruff check sbdk/
      
    - name: 🎨 Check formatting with black
      run: uv run black --check sbdk/
      
    - name: 🧪 Run tests with pytest
      run: uv run pytest tests/ --cov=sbdk --cov-report=xml --cov-report=term
      
    - name: 📊 Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
        
  build:
    name: 🏗️ Build Package
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - name: 📥 Checkout code
      uses: actions/checkout@v4
      
    - name: ⚡ Install uv
      uses: astral-sh/setup-uv@v3
      
    - name: 🐍 Set up Python
      run: uv python install ${{ env.PYTHON_VERSION }}
      
    - name: 🔧 Install build dependencies
      run: uv sync
      
    - name: 📦 Build package
      run: uv build
      
    - name: 📤 Upload build artifacts
      uses: actions/upload-artifact@v4
      with:
        name: dist
        path: dist/
        
  publish:
    name: 🚀 Publish to PyPI
    runs-on: ubuntu-latest
    needs: [test, build]
    if: github.event_name == 'release' && github.event.action == 'published'
    
    steps:
    - name: 📥 Checkout code
      uses: actions/checkout@v4
      
    - name: ⚡ Install uv
      uses: astral-sh/setup-uv@v3
      
    - name: 📥 Download build artifacts
      uses: actions/download-artifact@v4
      with:
        name: dist
        path: dist/
        
    - name: 🚀 Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: uv run twine upload dist/*
```

---

## 🛠️ Local Development CI Commands

### Quick Quality Check
```bash
# Run all quality checks locally (matches CI)
uv run ruff check sbdk/ --fix     # Auto-fix linting issues
uv run black sbdk/                # Format code
uv run pytest tests/ -v          # Run tests
```

### Full CI Simulation
```bash
# Simulate complete CI pipeline locally
uv sync --group dev               # Install dependencies
uv run ruff check sbdk/           # Lint check
uv run black --check sbdk/        # Format check
uv run pytest tests/ --cov=sbdk  # Test with coverage
uv build                         # Build package
```

### Performance Testing
```bash
# Run performance benchmarks (CI optional)
uv run pytest tests/test_performance_benchmarks.py -v
```

---

## 📊 Advanced CI/CD Configurations

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black

  - repo: local
    hooks:
      - id: tests
        name: Run tests
        entry: uv run pytest tests/
        language: system
        pass_filenames: false
```

### Docker CI/CD
```dockerfile
# Dockerfile.ci
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY sbdk/ ./sbdk/
COPY tests/ ./tests/

# Install dependencies and run tests
RUN uv sync --group dev
RUN uv run pytest tests/ --cov=sbdk
```

---

## ⚡ Performance Optimizations

### 1. Dependency Caching
```yaml
# Optimized caching strategy
- name: 📦 Cache uv dependencies
  uses: actions/cache@v4
  with:
    path: |
      ${{ env.UV_CACHE_DIR }}
      ~/.cache/uv
    key: uv-${{ runner.os }}-${{ hashFiles('**/uv.lock') }}
    restore-keys: |
      uv-${{ runner.os }}-
```

### 2. Parallel Matrix Testing
```yaml
# Test multiple configurations simultaneously
strategy:
  matrix:
    python-version: ["3.9", "3.10", "3.11", "3.12"]
    os: [ubuntu-latest, windows-latest, macos-latest]
  max-parallel: 8
```

### 3. Conditional Job Execution
```yaml
# Skip expensive jobs for documentation-only changes
jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      code: ${{ steps.changes.outputs.code }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v2
        id: changes
        with:
          filters: |
            code:
              - 'sbdk/**'
              - 'tests/**'
              - 'pyproject.toml'

  test:
    needs: changes
    if: ${{ needs.changes.outputs.code == 'true' }}
    # ... rest of test job
```

---

## 🔒 Security Best Practices

### 1. Secret Management
```yaml
env:
  TWINE_USERNAME: __token__
  TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
  CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```

### 2. Permission Restrictions
```yaml
permissions:
  contents: read
  packages: write
  id-token: write  # For PyPI trusted publishing
```

### 3. Dependency Scanning
```yaml
- name: 🛡️ Security audit
  run: uv run pip-audit
```

---

## 📈 Monitoring and Metrics

### 1. Build Performance Tracking
```yaml
- name: 📊 Report build metrics
  run: |
    echo "Build time: ${{ job.duration }}"
    echo "Cache hit rate: ${{ steps.cache.outputs.cache-hit }}"
```

### 2. Test Coverage Reporting
```yaml
- name: 📊 Coverage report
  run: |
    uv run pytest tests/ --cov=sbdk --cov-report=html
    echo "Coverage: $(uv run coverage report --show-missing)"
```

### 3. Package Size Analysis
```yaml
- name: 📦 Analyze package size
  run: |
    uv build
    ls -lah dist/
    du -sh dist/*
```

---

## 🚀 Deployment Strategies

### 1. Staging Deployment
```yaml
deploy-staging:
  if: github.ref == 'refs/heads/develop'
  runs-on: ubuntu-latest
  environment: staging
  steps:
    - name: 🚀 Deploy to staging
      run: |
        uv build
        # Deploy to staging environment
```

### 2. Production Deployment
```yaml
deploy-production:
  if: github.event_name == 'release'
  runs-on: ubuntu-latest
  environment: production
  steps:
    - name: 🚀 Deploy to production
      run: |
        uv build
        # Deploy to production environment
```

---

## 💡 Best Practices Summary

### ✅ DO:
- **Use uv for all Python package operations** (10-100x faster)
- **Cache uv dependencies** for faster CI runs
- **Run tests in parallel** across multiple Python versions
- **Use pre-commit hooks** for local quality checks
- **Monitor build performance** and optimize bottlenecks
- **Implement security scanning** for dependencies
- **Use semantic versioning** for releases

### ❌ DON'T:
- **Use pip in CI pipelines** (slower, less reliable)
- **Skip dependency caching** (wastes CI time)
- **Run all tests on documentation changes** (inefficient)
- **Hardcode secrets** in workflow files
- **Ignore security vulnerabilities** in dependencies
- **Deploy without comprehensive testing**

---

## 🔧 Troubleshooting

### Common CI Issues

1. **uv cache miss**
   ```yaml
   # Solution: Use correct cache key
   key: uv-${{ runner.os }}-${{ hashFiles('**/uv.lock') }}
   ```

2. **Python version conflicts**
   ```yaml
   # Solution: Pin Python version consistently
   - run: uv python install 3.11
   ```

3. **Test failures in CI but not locally**
   ```bash
   # Debug with same environment
   uv run pytest tests/ --verbose --tb=long
   ```

### Performance Issues

1. **Slow dependency installation**
   - ✅ Use uv instead of pip
   - ✅ Implement proper caching
   - ✅ Use dependency groups for dev dependencies

2. **Long test execution**
   - ✅ Run tests in parallel
   - ✅ Use pytest-xdist for parallel execution
   - ✅ Skip slow tests for quick feedback

---

## 📚 Additional Resources

- **uv Documentation**: https://docs.astral.sh/uv/
- **GitHub Actions**: https://docs.github.com/en/actions
- **SBDK.dev Testing**: See `tests/` directory for examples
- **Performance Benchmarks**: `tests/test_performance_benchmarks.py`

---

**🎉 Result: Modern, fast, reliable CI/CD pipeline with uv**

This configuration provides a production-ready CI/CD pipeline that's 10-100x faster than traditional pip-based workflows, with comprehensive testing, security scanning, and automated deployment capabilities.