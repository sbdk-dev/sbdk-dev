"""
SBDK project management
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

from sbdk.core.config import SBDKConfig


class SBDKProject:
    """SBDK project manager"""

    def __init__(
        self, config: Optional[SBDKConfig] = None, project_root: Optional[Path] = None
    ):
        """Initialize project manager"""
        self.project_root = project_root or Path.cwd()

        if config is None:
            config_path = self.project_root / "sbdk_config.json"
            if config_path.exists():
                self.config = SBDKConfig.load_from_file(str(config_path))
            else:
                raise FileNotFoundError(f"No config found at {config_path}")
        else:
            self.config = config

    def validate_project(self) -> dict[str, Any]:
        """Validate project structure and dependencies"""
        validation_results = {
            "paths": self.config.validate_paths(),
            "dependencies": self._check_dependencies(),
            "dbt_profile": self._check_dbt_profile(),
        }

        return validation_results

    def _check_dependencies(self) -> dict[str, bool]:
        """Check if required CLI tools are available"""
        dependencies = {}

        required_tools = ["dbt", "python"]

        for tool in required_tools:
            try:
                subprocess.run(
                    [tool, "--version"], capture_output=True, text=True, check=True
                )
                dependencies[tool] = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                dependencies[tool] = False

        return dependencies

    def _check_dbt_profile(self) -> bool:
        """Check if dbt profile exists for this project"""
        profiles_dir = self.config.get_profiles_dir()
        profiles_file = profiles_dir / "profiles.yml"

        if not profiles_file.exists():
            return False

        try:
            with open(profiles_file) as f:
                content = f.read()

            # Simple check if project name is in profiles
            return self.config.project in content
        except Exception:
            return False

    def run_pipelines(self, pipeline_names: Optional[list[str]] = None) -> bool:
        """Run DLT pipelines"""
        if pipeline_names is None:
            pipeline_names = ["users", "events", "orders"]

        pipelines_path = self.config.get_pipelines_path()

        for pipeline_name in pipeline_names:
            pipeline_file = pipelines_path / f"{pipeline_name}.py"

            if not pipeline_file.exists():
                print(f"Pipeline not found: {pipeline_file}")
                continue

            try:
                # Run pipeline module
                result = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        f"import sys; sys.path.insert(0, '{pipelines_path.parent}'); "
                        f"from pipelines.{pipeline_name} import run; run()",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=self.project_root,
                )

                if result.stdout:
                    print(f"Pipeline {pipeline_name} output: {result.stdout}")

            except subprocess.CalledProcessError as e:
                print(f"Pipeline {pipeline_name} failed: {e.stderr}")
                return False

        return True

    def run_dbt(
        self, command: str = "run", extra_args: Optional[list[str]] = None
    ) -> bool:
        """Run dbt commands"""
        if extra_args is None:
            extra_args = []

        dbt_path = self.config.get_dbt_path()
        profiles_dir = self.config.get_profiles_dir()

        cmd = [
            "dbt",
            command,
            "--project-dir",
            str(dbt_path),
            "--profiles-dir",
            str(profiles_dir),
        ] + extra_args

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, cwd=self.project_root
            )

            if result.stdout:
                print(f"dbt {command} output: {result.stdout}")

            return True

        except subprocess.CalledProcessError as e:
            print(f"dbt {command} failed: {e.stderr}")
            return False

    def get_project_info(self) -> dict[str, Any]:
        """Get project information"""
        return {
            "name": self.config.project,
            "root": str(self.project_root),
            "config": self.config.model_dump(),
            "validation": self.validate_project(),
        }
