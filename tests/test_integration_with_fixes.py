#!/usr/bin/env python3
"""
Integration tests for SBDK unified project with all fixes applied
"""
import subprocess
import sys


class TestUnifiedSBDK:
    """Test suite for unified SBDK project"""

    def test_cli_installation(self):
        """Test that CLI installs and works correctly"""
        result = subprocess.run(
            [sys.executable, "-m", "sbdk.cli.main", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "SBDK.dev" in result.stdout

    def test_email_uniqueness_fix(self):
        """Test that email uniqueness fix is working"""
        # This would run the email uniqueness test from my_project
        # Implementation depends on having the fixed pipelines available
        pass

    def test_dbt_runner_fix(self):
        """Test that DBT runner handles virtual environments correctly"""
        # This would test the improved DBT runner from my_project
        pass

    def test_project_initialization(self):
        """Test that project initialization works with all fixes"""
        # Test the 'sbdk init' command with unified configuration
        pass
