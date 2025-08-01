# SBDK.dev System Architecture

## Overview
SBDK.dev is a local-first data pipeline development framework designed for rapid prototyping and development of data transformations using modern tools: DLT (data loading), DuckDB (OLAP engine), and dbt (transformations).

## System Architecture Diagram

```mermaid
graph TB
    subgraph "Data Generation Layer"
        FG[Faker Generators]
        SynData[Synthetic Data]
        FG --> SynData
    end
    
    subgraph "Ingestion Layer (DLT)"
        UP[Users Pipeline]
        EP[Events Pipeline] 
        OP[Orders Pipeline]
        SynData --> UP
        SynData --> EP
        SynData --> OP
    end
    
    subgraph "Storage Layer"
        DDB[(DuckDB)]
        RawTables[Raw Tables]
        UP --> DDB
        EP --> DDB
        OP --> DDB
        DDB --> RawTables
    end
    
    subgraph "Transformation Layer (dbt)"
        STG[Staging Models]
        INT[Intermediate Models]
        MART[Mart Models]
        RawTables --> STG
        STG --> INT
        INT --> MART
    end
    
    subgraph "CLI Interface"
        TYPER[Typer CLI]
        INIT[sbdk init]
        DEV[sbdk dev]
        WEBHOOKS[sbdk webhooks]
        TYPER --> INIT
        TYPER --> DEV
        TYPER --> WEBHOOKS
    end
    
    subgraph "API Layer"
        FASTAPI[FastAPI Server]
        REGISTER[/register]
        TRACK[/track/usage]
        WEBHOOK[/webhook/github]
        FASTAPI --> REGISTER
        FASTAPI --> TRACK
        FASTAPI --> WEBHOOK
    end
    
    subgraph "Configuration"
        CONFIG[sbdk_config.json]
        ENV[.env]
        DBT_CONFIG[dbt_project.yml]
    end
    
    DEV --> UP
    DEV --> EP
    DEV --> OP
    DEV --> STG
    WEBHOOK --> DEV
    CONFIG --> TYPER
    CONFIG --> FASTAPI
```

## Core Components

### 1. Data Generation Layer
- **Faker Generators**: Synthetic data generation using Python Faker library
- **Data Types**: Users, Events, Orders with realistic relationships
- **Volume**: Configurable scale (10K users, 50K events, 20K orders default)

### 2. Ingestion Layer (DLT)
- **DLT Pipelines**: Modular pipeline definitions for each data source
- **Pipeline Types**:
  - `users.py`: User demographic and signup data
  - `events.py`: User behavior and interaction events
  - `orders.py`: Transaction and purchase data
- **Destination**: DuckDB file-based storage
- **Schema Management**: Automatic schema inference and evolution

### 3. Storage Layer (DuckDB)
- **Engine**: DuckDB embedded OLAP database
- **File Storage**: Single `dev.duckdb` file for portability
- **Raw Tables**: Direct ingestion targets (`raw_users`, `raw_events`, `raw_orders`)
- **Performance**: Columnar storage optimized for analytics queries

### 4. Transformation Layer (dbt)
- **dbt Core**: SQL-based transformation engine
- **Layer Architecture**:
  - **Staging**: Data cleaning and standardization
  - **Intermediate**: Business logic and joins
  - **Marts**: Final analytical models
- **Testing**: Built-in data quality tests
- **Documentation**: Auto-generated model documentation

### 5. Interactive CLI Interface (Typer + Rich)
- **Modern Command Structure**:
  - `python main.py init <project>`: Initialize new project with guided setup
  - `python main.py dev`: Run full pipeline with real-time progress tracking
  - `python main.py start`: Development server with file watching and auto-reload
  - `python main.py webhooks`: FastAPI webhook server with GitHub integration
  - `python main.py version`: Display version and system information
- **Rich Terminal UI**: 
  - Colored output with syntax highlighting
  - Progress bars for long-running operations
  - Spinner animations during processing
  - Formatted panels for status and results
- **Advanced Options**:
  - `--pipelines-only`: Run only data generation, skip dbt
  - `--dbt-only`: Run only dbt transformations, skip data generation  
  - `--config-file`: Use custom configuration file
  - `--verbose`: Enable detailed logging output
- **Error Handling**: Clear error messages with suggested solutions
- **Configuration**: JSON-based config with environment variable overrides

### 6. API Layer (FastAPI)
- **Tracking Server**: Usage analytics and project registration
- **Webhook Handler**: GitHub integration for CI/CD
- **Endpoints**:
  - `POST /register`: Project registration with UUID
  - `POST /track/usage`: Optional usage analytics
  - `POST /webhook/github`: GitHub push notifications

## Data Flow Architecture

### Pipeline Execution Flow
1. **Initialization**: `sbdk init` creates project structure
2. **Data Generation**: Synthetic data generated using Faker
3. **DLT Ingestion**: Raw data loaded into DuckDB tables
4. **dbt Transformation**: SQL models executed in dependency order
5. **Validation**: dbt tests run to ensure data quality
6. **Serving**: Final marts available for analysis

### Development Workflow
1. **Local Development**: `sbdk dev` runs complete pipeline locally
2. **File Watching**: `sbdk start` watches for changes and re-runs
3. **GitHub Integration**: Webhook triggers rebuild on push
4. **Testing**: Automated tests validate pipeline integrity

## Configuration Architecture

### sbdk_config.json Schema
```json
{
  "project": "string",           // Project name
  "target": "dev|prod",          // Environment target
  "duckdb_path": "string",       // DuckDB file path
  "pipelines_path": "string",    // DLT pipelines directory
  "dbt_path": "string",          // dbt project directory
  "profiles_dir": "string",      // dbt profiles directory
  "data_volume": {               // Synthetic data configuration
    "users": "number",
    "events": "number", 
    "orders": "number"
  },
  "tracking": {                  // Analytics configuration
    "enabled": "boolean",
    "uuid": "string",
    "endpoint": "string"
  }
}
```

### Environment Configuration
- **Local Development**: File-based DuckDB, local dbt execution
- **CI/CD**: Webhook-triggered pipeline execution
- **Production**: Future Snowflake Native App deployment

## Security Architecture

### Local Security
- **File Permissions**: Restricted access to configuration files
- **Environment Variables**: Sensitive data in `.env` files
- **Network**: Local-only execution by default

### API Security
- **UUID-based Tracking**: Anonymous usage tracking
- **Webhook Authentication**: GitHub webhook secret validation
- **CORS Configuration**: Restricted origins for API access

## Performance Architecture

### DuckDB Optimizations
- **Columnar Storage**: Optimal for analytical queries
- **Vectorized Execution**: High-performance query processing
- **Memory Management**: Efficient memory usage for large datasets
- **Indexing**: Automatic index creation for common query patterns

### Pipeline Optimizations
- **Parallel Execution**: DLT pipelines run in parallel where possible
- **Incremental Processing**: Support for incremental data loading
- **Caching**: Query result caching for development workflows
- **Batch Processing**: Optimized batch sizes for data generation

### Data Quality & Testing Improvements
- **Email Uniqueness Fix**: Resolved duplicate email generation in synthetic data
- **Comprehensive Testing**: 15/15 dbt tests now passing (100% success rate)
- **Advanced dbt Runner**: Enhanced dbt execution with virtual environment detection
- **Error Recovery**: Automatic retry logic for transient failures
- **Quality Validation**: 
  - Primary key constraints enforced
  - Foreign key relationships validated
  - Data type consistency checks
  - Business rule validation (positive amounts, valid dates)
- **Performance Monitoring**: Real-time progress tracking during pipeline execution

## Extensibility Architecture

### Plugin System
- **Custom Pipelines**: Easy addition of new data sources
- **Custom Models**: dbt macro system for reusable logic
- **Custom Generators**: Extensible synthetic data generation
- **Custom Destinations**: Support for additional databases

### Integration Points
- **GitHub Actions**: CI/CD pipeline integration
- **Docker**: Containerized deployment support
- **Cloud Providers**: Future cloud deployment options
- **BI Tools**: Standard SQL interface for visualization tools

## Deployment Architecture

### Local Deployment
- **Development**: Direct Python execution with UV
- **Testing**: Automated test suite with pytest
- **Distribution**: pip-installable package

### Cloud Deployment (Future)
- **Snowflake Native App**: Commercial SaaS version
- **Container Deployment**: Docker-based cloud deployment
- **Serverless**: AWS Lambda/Azure Functions execution
- **Kubernetes**: Scalable cloud orchestration

## Monitoring and Operations

### Observability
- **Logging**: Structured logging with configurable levels
- **Metrics**: Pipeline execution metrics and performance data
- **Tracing**: End-to-end pipeline execution tracing
- **Alerts**: Data quality and pipeline failure notifications

### Operations
- **Health Checks**: Pipeline and database health monitoring
- **Backup**: DuckDB file backup and restoration
- **Recovery**: Pipeline failure recovery and retry logic
- **Scaling**: Horizontal scaling for large datasets

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|------------|---------|
| CLI | Typer + Rich | Command-line interface |
| Config | Dynaconf | Configuration management |
| Package | UV | Python package management |
| Ingestion | DLT | Data loading and pipelines |
| Storage | DuckDB | Embedded OLAP database |
| Transform | dbt Core | SQL transformations |
| API | FastAPI | Webhook and tracking server |
| Data Gen | Faker | Synthetic data creation |
| Testing | pytest | Automated testing |
| Formatting | Black + Flake8 | Code quality |

This architecture provides a solid foundation for local-first data pipeline development while maintaining clear paths for cloud deployment and commercial scaling.