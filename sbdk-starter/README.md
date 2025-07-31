# 🚀 SBDK.dev - Local-First Data Pipeline Sandbox

> **Build data pipelines with DLT, DuckDB, and dbt - no cloud required!**

SBDK.dev is a modern, local-first data pipeline framework that lets you build, test, and iterate on data transformations using industry-standard tools. Perfect for learning, prototyping, or building production-ready pipelines.

## ✨ Features

- 🏗️ **Modern CLI** - Built with Typer and Rich for beautiful terminal UX
- 📊 **Synthetic Data Generation** - Realistic users, events, and orders data
- 🦆 **DuckDB Integration** - Fast, embedded OLAP database
- 🔄 **dbt Transformations** - SQL-based data modeling and testing  
- 🚀 **FastAPI Webhooks** - GitHub integration and tracking server
- 👀 **File Watching** - Auto-rebuild on code changes
- 📈 **Rich Analytics** - Pre-built user metrics and RFM analysis

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download SBDK starter
git clone https://github.com/your-org/sbdk-starter.git
cd sbdk-starter

# Set up Python environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install --upgrade pip
uv pip install -r requirements.txt
```

### 2. Initialize Your First Project

```bash
# Create a new SBDK project
python main.py init my_data_project

# Navigate to your project
cd my_data_project
```

### 3. Run Your Pipeline

```bash
# Run the complete pipeline (data generation + dbt transformations)
python ../main.py dev

# Start development server with file watching
python ../main.py start

# Start webhook server (optional)
python ../main.py webhooks
```

### 4. Explore Your Data

```bash
# Connect to your DuckDB database
duckdb data/my_data_project.duckdb

# Query your transformed data
SELECT * FROM user_metrics LIMIT 10;
SELECT value_tier, COUNT(*) FROM user_metrics GROUP BY value_tier;
```

## 📊 What You Get

### Synthetic Data Pipelines

- **Users** (10K records): Demographics, subscriptions, referrers
- **Events** (50K records): Page views, clicks, purchases with UTM tracking  
- **Orders** (20K records): E-commerce transactions with full details

### dbt Models

- **Staging**: Clean, validated raw data
- **Intermediate**: User activity aggregations
- **Marts**: Final analytics tables with RFM scoring

### Pre-built Analytics

- Customer Lifetime Value (CLV) estimates
- Engagement scoring (0-100)
- RFM analysis (Recency, Frequency, Monetary)
- Churn risk classification
- Conversion funnel metrics

## 🛠️ CLI Commands

| Command | Description | Example |
|---------|-------------|---------|
| `init` | Create new project | `python main.py init ecommerce` |
| `dev` | Run pipelines + dbt | `python main.py dev` |
| `start` | Development server | `python main.py start` |
| `webhooks` | Webhook listener | `python main.py webhooks` |

### Advanced Options

```bash
# Run only pipelines (skip dbt)
python main.py dev --pipelines-only

# Run only dbt (skip data generation) 
python main.py dev --dbt-only

# Custom watch paths
python main.py start --watch pipelines/ --watch custom/

# Webhook server on custom port
python main.py webhooks --port 9000 --host localhost
```

## 📁 Project Structure

```
my_data_project/
├── pipelines/           # Data generation scripts
│   ├── users.py         # User demographic data
│   ├── events.py        # Event tracking data  
│   └── orders.py        # E-commerce order data
├── dbt/                 # dbt transformation project
│   ├── models/
│   │   ├── staging/     # Clean raw data
│   │   ├── intermediate/# Aggregated data
│   │   └── marts/       # Final analytics tables
│   └── dbt_project.yml
├── fastapi_server/      # Webhook server
│   └── webhook_listener.py
├── data/                # DuckDB database files
├── sbdk_config.json     # Project configuration
└── README.md
```

## 🔗 GitHub Integration

SBDK includes webhook support for GitHub integration:

1. **Start webhook server**: `python main.py webhooks`
2. **Configure GitHub webhook**: Point to `http://your-server:8000/webhook/github`
3. **Auto-rebuild**: Pushes to main branch trigger pipeline rebuilds

### Webhook Events Supported

- `push` to main branch → Rebuild pipeline
- `pull_request` opened/updated → Run tests
- Custom event handling via FastAPI

## 🧪 Testing & Quality

```bash
# Install test dependencies
uv pip install pytest black flake8

# Run tests
pytest tests/

# Format code
black .

# Lint code  
flake8 .
```

## 📈 Analytics Deep Dive

### User Metrics Table

The final `user_metrics` table includes:

- **Demographics**: Age, location, subscription tier
- **Engagement**: Page views, sessions, activity frequency
- **Revenue**: Total spend, average order value, CLV estimate
- **Behavior**: Conversion rates, product categories purchased
- **Scoring**: Engagement score (0-100), RFM scores (1-5 each)
- **Classification**: User type, value tier, churn risk

### Sample Queries

```sql
-- Top customers by CLV
SELECT username, total_revenue, estimated_clv, value_tier
FROM user_metrics 
WHERE user_type = 'customer'
ORDER BY estimated_clv DESC 
LIMIT 10;

-- Churn risk analysis
SELECT risk_category, COUNT(*) as users, 
       AVG(total_revenue) as avg_revenue
FROM user_metrics 
GROUP BY risk_category;

-- Conversion funnel
SELECT 
  COUNT(*) as total_users,
  SUM(CASE WHEN signups > 0 THEN 1 ELSE 0 END) as signed_up,
  SUM(CASE WHEN total_orders > 0 THEN 1 ELSE 0 END) as purchased,
  ROUND(SUM(CASE WHEN total_orders > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as conversion_rate
FROM user_metrics;
```

## 🚀 Next Steps

### Extend Your Pipeline

1. **Add Custom Data Sources**: Create new pipeline modules
2. **Build Custom Models**: Add dbt models for your specific use case
3. **Create Dashboards**: Connect Metabase, Grafana, or Streamlit
4. **Deploy to Cloud**: Use DuckDB Cloud, MotherDuck, or Snowflake

### Production Deployment

- **Database**: Migrate to PostgreSQL, Snowflake, or BigQuery
- **Orchestration**: Use Airflow, Prefect, or dbt Cloud
- **CI/CD**: GitHub Actions with automated testing
- **Monitoring**: Add data quality tests and alerting

## 📚 Learn More

- [DuckDB Documentation](https://duckdb.org/docs/) - Embedded analytics database
- [dbt Documentation](https://docs.getdbt.com/) - SQL-based transformations
- [DLT Documentation](https://dlthub.com/docs/) - Data loading framework
- [FastAPI Documentation](https://fastapi.tiangolo.com/) - Modern Python API framework

## 🤝 Contributing

SBDK.dev is open source! Contributions welcome:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the Polyform Noncommercial License 1.0.0.

**TL;DR**: Free for personal, academic, and non-commercial use. Commercial use requires a license.

---

**Built with ❤️ for the data community**

*SBDK.dev - Because data pipelines should be simple, fast, and local-first.*