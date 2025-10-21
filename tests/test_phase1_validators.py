"""
Unit tests for Phase 1: Validators Module
Tests Pydantic schemas and configuration validation
"""

import pytest
from pathlib import Path
from pydantic import ValidationError

from sbdk.validators import (
    TargetEnvironment,
    FeatureFlags,
    PerformanceConfig,
    PipelineConfig,
    DBTConfig,
    DuckDBConfig,
    WebhookConfig,
    LoggingConfig,
    SBDKConfig,
    InitCommandInput,
    RunCommandInput,
)


class TestTargetEnvironment:
    """Test TargetEnvironment enum"""

    def test_valid_environments(self):
        """Test valid environment values"""
        assert TargetEnvironment.DEV == "dev"
        assert TargetEnvironment.TEST == "test"
        assert TargetEnvironment.PROD == "prod"


class TestFeatureFlags:
    """Test FeatureFlags configuration"""

    def test_default_feature_flags(self):
        """Test default feature flag values"""
        flags = FeatureFlags()

        assert flags.parallel_processing is True
        assert flags.memory_optimization is True
        assert flags.quality_monitoring is True
        assert flags.visual_interface is True

    def test_custom_feature_flags(self):
        """Test custom feature flag values"""
        flags = FeatureFlags(
            parallel_processing=False,
            visual_interface=False
        )

        assert flags.parallel_processing is False
        assert flags.visual_interface is False
        assert flags.memory_optimization is True  # Still default


class TestPerformanceConfig:
    """Test PerformanceConfig"""

    def test_default_performance_config(self):
        """Test default performance configuration"""
        perf = PerformanceConfig()

        assert perf.batch_size == 10000
        assert perf.worker_threads == 4
        assert perf.cache_strategy == "intelligent"
        assert perf.memory_limit_mb is None

    def test_custom_performance_config(self):
        """Test custom performance configuration"""
        perf = PerformanceConfig(
            batch_size=5000,
            worker_threads=8,
            cache_strategy="aggressive",
            memory_limit_mb=2048
        )

        assert perf.batch_size == 5000
        assert perf.worker_threads == 8
        assert perf.cache_strategy == "aggressive"
        assert perf.memory_limit_mb == 2048

    def test_batch_size_validation(self):
        """Test batch size bounds validation"""
        # Too small
        with pytest.raises(ValidationError):
            PerformanceConfig(batch_size=50)

        # Too large
        with pytest.raises(ValidationError):
            PerformanceConfig(batch_size=200000)

    def test_worker_threads_validation(self):
        """Test worker threads bounds validation"""
        # Too small
        with pytest.raises(ValidationError):
            PerformanceConfig(worker_threads=0)

        # Too large
        with pytest.raises(ValidationError):
            PerformanceConfig(worker_threads=64)

    def test_cache_strategy_validation(self):
        """Test cache strategy pattern validation"""
        # Valid strategies
        for strategy in ["intelligent", "aggressive", "conservative", "none"]:
            perf = PerformanceConfig(cache_strategy=strategy)
            assert perf.cache_strategy == strategy

        # Invalid strategy
        with pytest.raises(ValidationError):
            PerformanceConfig(cache_strategy="invalid")


class TestPipelineConfig:
    """Test PipelineConfig"""

    def test_valid_pipeline_config(self):
        """Test valid pipeline configuration"""
        pipeline = PipelineConfig(
            name="test_pipeline",
            module_path="pipelines.test"
        )

        assert pipeline.name == "test_pipeline"
        assert pipeline.enabled is True
        assert pipeline.module_path == "pipelines.test"
        assert pipeline.dependencies == []

    def test_pipeline_name_validation(self):
        """Test pipeline name validation"""
        # Valid names
        for name in ["test", "test_pipeline", "test-pipeline", "test123"]:
            pipeline = PipelineConfig(name=name, module_path="test")
            assert pipeline.name == name

        # Invalid names (spaces, special chars)
        with pytest.raises(ValidationError):
            PipelineConfig(name="test pipeline", module_path="test")

        with pytest.raises(ValidationError):
            PipelineConfig(name="test@pipeline", module_path="test")

    def test_pipeline_with_dependencies(self):
        """Test pipeline with dependencies"""
        pipeline = PipelineConfig(
            name="orders",
            module_path="pipelines.orders",
            dependencies=["users", "products"]
        )

        assert pipeline.dependencies == ["users", "products"]


class TestDBTConfig:
    """Test DBTConfig"""

    def test_default_dbt_config(self):
        """Test default dbt configuration"""
        dbt = DBTConfig()

        assert dbt.project_dir == Path("./dbt")
        # profiles_dir should be expanded (the validator expands it)
        assert dbt.profiles_dir == (Path.home() / ".dbt")
        assert dbt.target == "dev"
        assert dbt.threads == 4
        assert dbt.vars == {}

    def test_path_expansion(self):
        """Test path expansion for ~ home directory"""
        dbt = DBTConfig(profiles_dir=Path("~/.dbt"))

        assert str(dbt.profiles_dir) == str(Path.home() / ".dbt")

    def test_custom_dbt_vars(self):
        """Test custom dbt variables"""
        dbt = DBTConfig(vars={"env": "test", "debug": True})

        assert dbt.vars["env"] == "test"
        assert dbt.vars["debug"] is True


class TestDuckDBConfig:
    """Test DuckDBConfig"""

    def test_valid_duckdb_config(self):
        """Test valid DuckDB configuration"""
        duckdb = DuckDBConfig(path=Path("data/test.duckdb"))

        assert duckdb.path == Path("data/test.duckdb")
        assert duckdb.memory_limit is None
        assert duckdb.threads is None
        assert duckdb.read_only is False

    def test_memory_limit_validation(self):
        """Test memory limit pattern validation"""
        # Valid formats
        for limit in ["4GB", "512MB", "2TB"]:
            duckdb = DuckDBConfig(path=Path("test.db"), memory_limit=limit)
            assert duckdb.memory_limit == limit

        # Invalid format
        with pytest.raises(ValidationError):
            DuckDBConfig(path=Path("test.db"), memory_limit="4G")


class TestWebhookConfig:
    """Test WebhookConfig"""

    def test_default_webhook_config(self):
        """Test default webhook configuration"""
        webhook = WebhookConfig()

        assert webhook.enabled is False
        assert webhook.host == "0.0.0.0"
        assert webhook.port == 8000
        assert webhook.secret is None
        assert "github" in webhook.endpoints

    def test_webhook_port_validation(self):
        """Test webhook port bounds validation"""
        # Valid ports
        webhook = WebhookConfig(port=8080)
        assert webhook.port == 8080

        # Port too low (reserved)
        with pytest.raises(ValidationError):
            WebhookConfig(port=80)

        # Port too high
        with pytest.raises(ValidationError):
            WebhookConfig(port=70000)

    def test_webhook_secret_validation(self):
        """Test webhook secret length validation"""
        # Valid secret (16+ chars)
        webhook = WebhookConfig(secret="a" * 16)
        assert len(webhook.secret) == 16

        # Too short
        with pytest.raises(ValidationError):
            WebhookConfig(secret="short")


class TestLoggingConfig:
    """Test LoggingConfig"""

    def test_default_logging_config(self):
        """Test default logging configuration"""
        logging = LoggingConfig()

        assert logging.level == "INFO"
        assert logging.file is None
        assert "%(asctime)s" in logging.format

    def test_logging_level_validation(self):
        """Test logging level validation"""
        # Valid levels
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logging = LoggingConfig(level=level)
            assert logging.level == level

        # Invalid level
        with pytest.raises(ValidationError):
            LoggingConfig(level="TRACE")


class TestSBDKConfig:
    """Test main SBDKConfig schema"""

    def test_minimal_valid_config(self):
        """Test minimal valid configuration"""
        config = SBDKConfig(
            project="test_project",
            duckdb_path="data/test.duckdb"
        )

        assert config.project == "test_project"
        assert config.duckdb_path == "data/test.duckdb"
        assert config.target == TargetEnvironment.DEV
        assert config.version == "1.0.0"

    def test_full_config(self):
        """Test full configuration with all fields"""
        config = SBDKConfig(
            project="full_project",
            version="2.0.0",
            description="Test project",
            target="test",
            duckdb_path="data/full.duckdb",
            pipelines_path="./custom_pipelines",
            dbt_path="./custom_dbt",
            features={"parallel_processing": False},
            performance={"batch_size": 5000, "worker_threads": 2},
        )

        assert config.project == "full_project"
        assert config.version == "2.0.0"
        assert config.description == "Test project"
        assert config.features.parallel_processing is False
        assert config.performance.batch_size == 5000

    def test_version_validation(self):
        """Test semantic version validation"""
        # Valid versions
        for version in ["1.0.0", "2.1.3", "10.20.30"]:
            config = SBDKConfig(project="test", duckdb_path="test.db", version=version)
            assert config.version == version

        # Invalid versions
        with pytest.raises(ValidationError):
            SBDKConfig(project="test", duckdb_path="test.db", version="1.0")

        with pytest.raises(ValidationError):
            SBDKConfig(project="test", duckdb_path="test.db", version="v1.0.0")

    def test_pipeline_dependencies_validation(self):
        """Test pipeline dependency validation"""
        # Valid dependencies
        config = SBDKConfig(
            project="test",
            duckdb_path="test.db",
            pipelines=[
                {"name": "users", "module_path": "pipelines.users"},
                {"name": "orders", "module_path": "pipelines.orders", "dependencies": ["users"]}
            ]
        )

        assert len(config.pipelines) == 2

        # Invalid dependency (non-existent pipeline)
        with pytest.raises(ValidationError) as exc_info:
            SBDKConfig(
                project="test",
                duckdb_path="test.db",
                pipelines=[
                    {"name": "orders", "module_path": "pipelines.orders", "dependencies": ["users"]}
                ]
            )

        assert "non-existent pipeline" in str(exc_info.value)

    def test_to_dict(self):
        """Test conversion to dictionary"""
        config = SBDKConfig(
            project="test",
            duckdb_path="data/test.duckdb"
        )

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["project"] == "test"
        assert "duckdb_path" in config_dict

    def test_to_json(self):
        """Test conversion to JSON"""
        config = SBDKConfig(
            project="test",
            duckdb_path="data/test.duckdb"
        )

        json_str = config.to_json()

        assert isinstance(json_str, str)
        assert '"project": "test"' in json_str

    def test_from_dict(self):
        """Test creation from dictionary"""
        config_dict = {
            "project": "test",
            "duckdb_path": "data/test.duckdb"
        }

        config = SBDKConfig.from_dict(config_dict)

        assert config.project == "test"

    def test_from_json(self):
        """Test creation from JSON string"""
        json_str = '{"project": "test", "duckdb_path": "data/test.duckdb"}'

        config = SBDKConfig.from_json(json_str)

        assert config.project == "test"


class TestInitCommandInput:
    """Test InitCommandInput validator"""

    def test_valid_init_input(self):
        """Test valid init command input"""
        input_data = InitCommandInput(project_name="my_project")

        assert input_data.project_name == "my_project"
        assert input_data.template == "default"
        assert input_data.force is False

    def test_project_name_validation(self):
        """Test project name validation"""
        # Valid names
        for name in ["test", "my_project", "test-123", "test_project"]:
            input_data = InitCommandInput(project_name=name)
            assert input_data.project_name == name

        # Invalid names
        with pytest.raises(ValidationError):
            InitCommandInput(project_name="my project")  # Space

        with pytest.raises(ValidationError):
            InitCommandInput(project_name="my@project")  # Special char


class TestRunCommandInput:
    """Test RunCommandInput validator"""

    def test_default_run_input(self):
        """Test default run command input"""
        input_data = RunCommandInput()

        assert input_data.visual is False
        assert input_data.watch is False
        assert input_data.pipelines_only is False
        assert input_data.dbt_only is False
        assert input_data.quiet is False
        assert input_data.dry_run is False

    def test_custom_run_input(self):
        """Test custom run command input"""
        input_data = RunCommandInput(
            visual=True,
            watch=True,
            quiet=False,
            dry_run=True
        )

        assert input_data.visual is True
        assert input_data.watch is True
        assert input_data.dry_run is True

    def test_mutually_exclusive_validation(self):
        """Test mutually exclusive options validation"""
        # pipelines_only and dbt_only are mutually exclusive
        with pytest.raises(ValidationError) as exc_info:
            RunCommandInput(pipelines_only=True, dbt_only=True)

        assert "mutually exclusive" in str(exc_info.value)

        # quiet and visual are mutually exclusive
        with pytest.raises(ValidationError) as exc_info:
            RunCommandInput(quiet=True, visual=True)

        assert "mutually exclusive" in str(exc_info.value)
