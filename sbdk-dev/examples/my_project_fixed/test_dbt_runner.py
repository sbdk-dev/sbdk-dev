#!/usr/bin/env python3
"""
Comprehensive test suite for the DBT runner fix.
Tests various scenarios including edge cases and error conditions.
"""

import unittest
import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import json

# Import the fixed runner
from run_dbt_fixed import DBTRunner


class TestDBTRunner(unittest.TestCase):
    """Test cases for the DBT Runner fix."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        # Create a mock dbt project structure
        self.project_dir = Path(self.test_dir) / 'test_project'
        self.project_dir.mkdir(parents=True)
        
        # Create dbt_project.yml
        dbt_project_content = """
name: 'test_project'
version: '1.0.0'
profile: 'test_profile'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["data"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

target-path: "target"
clean-targets:
  - "target"
  - "dbt_packages"

models:
  test_project:
    materialized: table
"""
        (self.project_dir / 'dbt_project.yml').write_text(dbt_project_content)
        
        # Create models directory
        (self.project_dir / 'models').mkdir()
        
        # Create a simple model
        model_content = """
{{ config(materialized='table') }}

select 1 as id
"""
        (self.project_dir / 'models' / 'test_model.sql').write_text(model_content)
        
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    def test_find_dbt_in_virtual_env(self):
        """Test finding dbt in virtual environment."""
        with patch.dict(os.environ, {'VIRTUAL_ENV': '/fake/venv'}):
            with patch('pathlib.Path.exists') as mock_exists:
                mock_exists.side_effect = lambda self: str(self) == '/fake/venv/bin/dbt'
                
                runner = DBTRunner(self.project_dir)
                self.assertEqual(runner.dbt_path, '/fake/venv/bin/dbt')
    
    def test_find_dbt_in_system_path(self):
        """Test finding dbt in system PATH."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/local/bin/dbt'
            with patch('pathlib.Path.exists', return_value=False):
                runner = DBTRunner(self.project_dir)
                self.assertEqual(runner.dbt_path, '/usr/local/bin/dbt')
    
    def test_dbt_not_found_error(self):
        """Test error when dbt is not found."""
        with patch('shutil.which', return_value=None):
            with patch('pathlib.Path.exists', return_value=False):
                with patch('subprocess.run', side_effect=Exception("Not found")):
                    with self.assertRaises(FileNotFoundError) as ctx:
                        DBTRunner(self.project_dir)
                    self.assertIn("dbt not found", str(ctx.exception))
    
    def test_validate_project_dir(self):
        """Test project directory validation."""
        # Valid project
        runner = DBTRunner(self.project_dir)
        self.assertTrue(runner._validate_project_dir())
        
        # Invalid project
        invalid_dir = Path(self.test_dir) / 'invalid'
        invalid_dir.mkdir()
        runner = DBTRunner(invalid_dir)
        with self.assertRaises(FileNotFoundError) as ctx:
            runner._validate_project_dir()
        self.assertIn("No dbt_project.yml found", str(ctx.exception))
    
    def test_nested_dbt_directory(self):
        """Test handling of nested dbt directory structure."""
        # Create structure: project/dbt/dbt_project.yml
        nested_project = Path(self.test_dir) / 'nested_project'
        nested_dbt_dir = nested_project / 'dbt'
        nested_dbt_dir.mkdir(parents=True)
        (nested_dbt_dir / 'dbt_project.yml').write_text("name: nested")
        
        runner = DBTRunner(nested_project)
        runner._validate_project_dir()
        self.assertEqual(runner.project_dir, nested_dbt_dir)
    
    @patch('subprocess.run')
    def test_run_dbt_command_success(self, mock_run):
        """Test successful dbt command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "dbt version 1.7.0"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        with patch('shutil.which', return_value='/usr/bin/dbt'):
            runner = DBTRunner(self.project_dir)
            result = runner.run_dbt_command(['--version'])
            
            self.assertEqual(result.returncode, 0)
            mock_run.assert_called_once()
            
            # Check command construction
            call_args = mock_run.call_args
            self.assertEqual(call_args[0][0][0], '/usr/bin/dbt')
            self.assertEqual(call_args[0][0][1], '--version')
    
    @patch('subprocess.run')
    def test_run_dbt_command_with_python_module(self, mock_run):
        """Test running dbt as Python module when executable not found."""
        # First call for version check succeeds
        version_result = MagicMock()
        version_result.returncode = 0
        version_result.stdout = "dbt version 1.7.0"
        
        # Second call for actual command
        command_result = MagicMock()
        command_result.returncode = 0
        command_result.stdout = "Running dbt"
        command_result.stderr = ""
        
        mock_run.side_effect = [version_result, command_result]
        
        with patch('shutil.which', return_value=None):
            with patch('pathlib.Path.exists', return_value=False):
                runner = DBTRunner(self.project_dir)
                result = runner.run_dbt_command(['run'])
                
                # Should use python -m dbt
                call_args = mock_run.call_args_list[1]
                self.assertEqual(call_args[0][0][0], sys.executable)
                self.assertEqual(call_args[0][0][1], '-m')
                self.assertEqual(call_args[0][0][2], 'dbt')
                self.assertEqual(call_args[0][0][3], 'run')
    
    @patch('subprocess.run')
    def test_run_dbt_command_failure(self, mock_run):
        """Test handling of failed dbt command."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Error output"
        mock_result.stderr = "Error details"
        mock_run.return_value = mock_result
        
        with patch('shutil.which', return_value='/usr/bin/dbt'):
            runner = DBTRunner(self.project_dir)
            
            with self.assertRaises(subprocess.CalledProcessError) as ctx:
                runner.run_dbt_command(['run'])
            
            self.assertEqual(ctx.exception.returncode, 1)
    
    def test_profiles_dir_resolution(self):
        """Test profiles directory resolution."""
        # Test environment variable
        with patch.dict(os.environ, {'DBT_PROFILES_DIR': '/custom/profiles'}):
            with patch('pathlib.Path.exists', return_value=True):
                runner = DBTRunner(self.project_dir)
                self.assertEqual(str(runner.profiles_dir), '/custom/profiles')
        
        # Test default location
        with patch('pathlib.Path.exists') as mock_exists:
            def exists_side_effect(self):
                return str(self) == str(Path.home() / '.dbt')
            
            mock_exists.side_effect = exists_side_effect
            runner = DBTRunner(self.project_dir)
            self.assertEqual(runner.profiles_dir, Path.home() / '.dbt')
    
    @patch('subprocess.run')
    def test_environment_setup(self, mock_run):
        """Test proper environment variable setup."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        with patch('shutil.which', return_value='/usr/bin/dbt'):
            with patch.dict(os.environ, {'VIRTUAL_ENV': '/fake/venv'}):
                runner = DBTRunner(self.project_dir)
                runner.run_dbt_command(['run'])
                
                # Check environment setup
                call_kwargs = mock_run.call_args[1]
                env = call_kwargs['env']
                
                # Should have DBT_PROFILES_DIR set
                self.assertIn('DBT_PROFILES_DIR', env)
                
                # Should have virtual env in PATH
                self.assertIn('/fake/venv/bin:', env['PATH'])
    
    def test_debug_info(self):
        """Test debug information output."""
        with patch('shutil.which', return_value='/usr/bin/dbt'):
            runner = DBTRunner(self.project_dir)
            
            # Should not raise any exceptions
            with patch('builtins.print'):
                runner.debug_info()


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for real-world scenarios."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / 'integration_project'
        self.project_dir.mkdir(parents=True)
        
        # Create a minimal dbt project
        (self.project_dir / 'dbt_project.yml').write_text("""
name: 'integration_test'
version: '1.0.0'
profile: 'test'
        """)
        
        (self.project_dir / 'models').mkdir()
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.test_dir)
    
    @patch('subprocess.run')
    def test_multiple_commands_sequence(self, mock_run):
        """Test running multiple dbt commands in sequence."""
        # Mock successful runs
        mock_run.return_value = MagicMock(
            returncode=0, stdout="Success", stderr=""
        )
        
        with patch('shutil.which', return_value='/usr/bin/dbt'):
            runner = DBTRunner(self.project_dir)
            
            # Run multiple commands
            commands = ['deps', 'compile', 'run', 'test']
            for cmd in commands:
                result = runner.run_dbt_command([cmd])
                self.assertEqual(result.returncode, 0)
            
            # Should have been called 4 times
            self.assertEqual(mock_run.call_count, 4)
    
    def test_cli_interface(self):
        """Test the command-line interface."""
        test_script = self.project_dir / 'test_cli.py'
        test_script.write_text("""
import sys
sys.path.insert(0, '.')
from run_dbt_fixed import main

# Mock sys.argv
sys.argv = ['run_dbt_fixed.py', '--debug', '--project-dir', '.', 'run']

try:
    main()
except SystemExit as e:
    print(f"Exit code: {e.code}")
""")
        
        # This would test the CLI interface
        # In a real test, we'd run this as a subprocess


def run_edge_case_tests():
    """Run additional edge case tests manually."""
    print("\n=== Running Edge Case Tests ===\n")
    
    # Test 1: Missing dbt_project.yml
    print("Test 1: Missing dbt_project.yml")
    try:
        runner = DBTRunner("/tmp/nonexistent")
        runner.run_dbt_command(['run'])
        print("❌ Should have raised FileNotFoundError")
    except FileNotFoundError as e:
        print(f"✅ Correctly raised: {e}")
    
    # Test 2: Invalid command
    print("\nTest 2: Invalid dbt command")
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / 'test'
        project_dir.mkdir()
        (project_dir / 'dbt_project.yml').write_text("name: test")
        
        try:
            runner = DBTRunner(project_dir)
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(
                    1, ['dbt', 'invalid'], "Error", "Invalid command"
                )
                runner.run_dbt_command(['invalid'])
                print("❌ Should have raised CalledProcessError")
        except subprocess.CalledProcessError as e:
            print(f"✅ Correctly raised: {e}")
    
    print("\n=== Edge Case Tests Complete ===\n")


if __name__ == '__main__':
    # Run unit tests
    print("Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run edge case tests
    run_edge_case_tests()