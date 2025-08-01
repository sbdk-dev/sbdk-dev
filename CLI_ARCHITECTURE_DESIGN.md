# 🚀 Interactive CLI Architecture Design

## Overview

This document outlines the enhanced interactive CLI architecture for SBDK.dev, building on the existing Typer + Rich foundation to create a user-friendly, guided experience for data pipeline development.

## Current State Analysis

### Existing Strengths
- ✅ **Typer Framework**: Solid CLI foundation with auto-completion and help
- ✅ **Rich Output**: Beautiful visual feedback with progress bars and panels  
- ✅ **Modular Design**: Clean separation of concerns across CLI modules
- ✅ **File Watching**: Real-time development with auto-rebuild
- ✅ **Configuration Management**: JSON-based project configuration

### Areas for Enhancement
- ❌ **Limited Interactivity**: Commands are mostly batch operations
- ❌ **No User Prompts**: No guided setup or configuration wizards
- ❌ **Basic Error Handling**: Errors don't provide actionable guidance
- ❌ **No Repository Import**: Can't import existing dbt projects
- ❌ **Static Configuration**: No interactive config management

## Enhanced Architecture Design

### 1. Core Interactive Patterns

#### A. Guided Wizards
```python
# Interactive project initialization
@app.command("init")
def interactive_init():
    project_name = prompt_with_validation(
        "Project name", 
        validator=validate_project_name,
        help_text="Use lowercase, underscores allowed"
    )
    
    template = select_from_options(
        "Choose template",
        options=[
            ("basic", "Simple pipelines with users/events/orders"),
            ("ecommerce", "E-commerce analytics template"),
            ("saas", "SaaS metrics template"),
            ("custom", "Import from existing dbt repository")
        ]
    )
    
    if template == "custom":
        repo_url = prompt_git_repository()
        import_dbt_repository(repo_url, project_name)
```

#### B. Progressive Disclosure
```python
# Show complexity only when needed
def show_advanced_options():
    if confirm("Configure advanced settings?", default=False):
        return configure_advanced_settings()
    return default_advanced_settings()
```

#### C. Rich Feedback Loops
```python
# Enhanced error handling with guidance
def handle_dbt_error(error):
    console.print(Panel(
        f"[red]dbt Error:[/red] {error.message}\n\n"
        f"[cyan]Suggested fixes:[/cyan]\n"
        f"• Check your SQL syntax in {error.file}\n"
        f"• Verify column names match your source data\n"
        f"• Run 'sbdk debug' for detailed diagnostics",
        title="❌ Build Failed",
        style="red"
    ))
    
    if confirm("Open the problematic file for editing?"):
        open_file_in_editor(error.file)
```

### 2. New CLI Modules

#### A. `cli/interactive.py` - Core Interactive Components
```python
"""
Interactive prompts, wizards, and user input handling
"""

def prompt_with_validation(message: str, validator: callable, help_text: str = None):
    """Enhanced prompt with validation and help"""
    
def select_from_options(message: str, options: List[Tuple], help_text: str = None):
    """Multi-choice selection with rich formatting"""
    
def confirm_with_details(message: str, details: str, default: bool = False):
    """Confirmation with expandable details"""
    
def progress_wizard(steps: List[WizardStep]):
    """Multi-step wizard with progress tracking"""
```

#### B. `cli/repo_import.py` - Repository Import
```python
"""
Import and integrate existing dbt repositories
"""

def import_dbt_repository(repo_url: str, project_name: str):
    """Clone and integrate external dbt repository"""
    
def validate_dbt_structure(repo_path: Path):
    """Validate dbt project structure and dependencies"""
    
def migrate_dbt_config(source_config: dict, target_config: dict):
    """Migrate dbt configuration to SBDK format"""
    
def setup_data_sources(dbt_sources: dict):
    """Configure data sources for imported models"""
```

#### C. `cli/config_wizard.py` - Configuration Management
```python
"""
Interactive configuration management and updates
"""

def config_wizard():
    """Step-by-step configuration setup"""
    
def update_database_config():
    """Database connection configuration"""
    
def setup_environment_configs():
    """Environment-specific configuration setup"""
    
def validate_and_test_config(config: dict):
    """Validate configuration and test connections"""
```

#### D. `cli/validation.py` - Input Validation
```python
"""
Input validation with user-friendly error messages
"""

def validate_project_name(name: str) -> ValidationResult:
    """Validate project name with helpful suggestions"""
    
def validate_git_url(url: str) -> ValidationResult:
    """Validate git repository URL"""
    
def validate_database_config(config: dict) -> ValidationResult:
    """Validate database configuration"""
    
def suggest_fixes(validation_errors: List[ValidationError]):
    """Provide actionable suggestions for validation errors"""
```

#### E. `cli/utils.py` - Rich Output Utilities
```python
"""
Shared utilities for rich console output
"""

def create_status_panel(title: str, items: List[StatusItem]):
    """Create standardized status panels"""
    
def show_progress_with_details(tasks: List[Task]):
    """Progress tracking with expandable details"""
    
def display_success_celebration(message: str, next_steps: List[str]):
    """Success message with guided next steps"""
    
def create_help_panel(command: str, examples: List[str]):
    """Context-sensitive help with examples"""
```

### 3. Enhanced User Experience Flows

#### A. Interactive Project Initialization
```bash
$ sbdk init

🚀 Welcome to SBDK.dev Interactive Setup!

? Project name: my_analytics_project
? Choose your template:
  ❯ 📊 Basic Analytics (users, events, orders)
    🛒 E-commerce Template (products, sales, customers) 
    💼 SaaS Template (subscriptions, usage, churn)
    📂 Import Existing dbt Repository
    
? Configure database:
  ❯ 🦆 DuckDB (recommended for local development)
    🐘 PostgreSQL
    ❄️  Snowflake
    
✨ Setting up your project...
├── 📁 Creating directory structure
├── 📋 Installing dependencies  
├── 🗄️  Initializing database
├── 🔧 Configuring dbt profiles
└── ✅ Running initial data load

🎉 Project created successfully!

Next steps:
1. cd my_analytics_project
2. sbdk dev     # Run your first pipeline
3. sbdk start   # Start development server
```

#### B. Repository Import Workflow
```bash
$ sbdk init --import

📂 Import Existing dbt Repository

? Repository URL: https://github.com/company/analytics-dbt
? Project name: company_analytics

🔍 Analyzing repository...
├── ✅ Valid dbt project found
├── 📋 Dependencies: dbt-snowflake, dbt-utils
├── 🗄️  Sources: 5 tables detected
└── 🔧 Models: 23 models, 3 tests

? Import configuration:
  ❯ 🔄 Migrate to DuckDB (recommended)
    ⚡ Keep original Snowflake config
    🔧 Custom configuration
    
? Configure data sources:
  📊 users table -> Sample data? [Y/n] 
  📅 events table -> Sample data? [Y/n]
  💰 orders table -> Sample data? [Y/n]

✨ Importing and configuring...
├── 📁 Cloning repository
├── 🔄 Converting configurations  
├── 📊 Generating sample data
├── 🧪 Running dbt tests
└── ✅ Import complete

🎉 Repository imported successfully!
```

#### C. Enhanced Error Handling
```bash
$ sbdk dev

🔧 Running development pipeline...

❌ dbt Build Failed

┌─ SQL Error in model 'user_metrics' ─┐
│                                      │
│ Column 'signup_date' not found      │
│                                      │
│ 💡 Suggested fixes:                 │
│ • Check column name in stg_users    │
│ • Verify source data schema         │
│ • Run 'sbdk debug' for details      │
│                                      │
│ ? Open file for editing? [Y/n]      │
└──────────────────────────────────────┘
```

### 4. Implementation Strategy

#### Phase 1: Core Interactive Components
1. Create `cli/interactive.py` with basic prompts and validation
2. Enhance existing commands with interactive options
3. Add rich error handling and guidance

#### Phase 2: Repository Import
1. Implement `cli/repo_import.py` with git integration
2. Add dbt project analysis and validation
3. Create configuration migration utilities

#### Phase 3: Configuration Management
1. Build `cli/config_wizard.py` for guided setup
2. Add environment-specific configuration support
3. Implement configuration testing and validation

#### Phase 4: Enhanced User Experience
1. Add comprehensive help system with examples
2. Implement progress tracking with detailed feedback
3. Create success celebrations and next-step guidance

### 5. Technical Considerations

#### Dependencies
- **questionary**: Advanced prompts and selections
- **GitPython**: Git repository operations
- **pydantic**: Configuration validation
- **jinja2**: Template rendering
- **click-spinner**: Enhanced progress indicators

#### Configuration Schema
```python
class SBDKConfig(BaseModel):
    project: str
    version: str = "1.0"
    target: str = "dev"
    
    database: DatabaseConfig
    pipelines: PipelinesConfig  
    dbt: DBTConfig
    
    environments: Dict[str, EnvironmentConfig] = {}
    imported_repos: List[ImportedRepoConfig] = []
```

#### Error Recovery
- Automatic backup creation before destructive operations
- Rollback capabilities for failed configurations
- Detailed diagnostic information with suggested fixes
- Integration with logging for debugging

### 6. Future Enhancements

#### AI-Assisted Development
- Intelligent pipeline suggestions based on data schema
- Automated test generation for dbt models
- Code completion and optimization suggestions

#### Team Collaboration
- Shared configuration templates
- Multi-environment deployment workflows  
- Integration with CI/CD pipelines

#### Advanced Analytics
- Usage analytics and optimization suggestions
- Performance monitoring and alerting
- Data quality scoring and recommendations

## Conclusion

This enhanced interactive CLI design transforms SBDK.dev from a tool-focused framework into a user-centered development experience. By providing guided wizards, rich feedback, and intelligent error handling, developers can focus on building great data pipelines rather than wrestling with configuration and setup complexity.

The modular architecture ensures maintainability while the progressive disclosure pattern keeps the CLI approachable for beginners yet powerful for advanced users.