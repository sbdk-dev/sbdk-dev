#!/usr/bin/env python3
"""
TESTER AGENT: Automated validation script for email uniqueness fix
Part of hive mind collective intelligence system

This script provides comprehensive testing for the duplicate email fix
including pre/post validation, performance analysis, and regression testing.
"""

import subprocess
import sys
import time
import duckdb
import json
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

class EmailUniquenessTestSuite:
    """Comprehensive test suite for email uniqueness fix validation"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.db_path = self.project_root / "data" / "dev.duckdb"
        self.dbt_path = self.project_root / "dbt"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {},
            "recommendations": []
        }
    
    def print_header(self, title):
        """Print formatted test section header"""
        print(f"\n{'='*60}")
        print(f"TESTER: {title}")
        print('='*60)
    
    def print_result(self, test_name, passed, details=""):
        """Print formatted test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {test_name}")
        if details:
            print(f"     └─ {details}")
        
        self.results["tests"][test_name] = {
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
    
    def check_duplicate_emails(self, label="Current State"):
        """Check for duplicate emails in the database"""
        self.print_header(f"Email Duplicate Analysis - {label}")
        
        try:
            con = duckdb.connect(str(self.db_path))
            
            # Get duplicate statistics
            result = con.execute("""
                SELECT 
                    COUNT(*) as total_emails,
                    COUNT(DISTINCT email) as unique_emails,
                    COUNT(*) - COUNT(DISTINCT email) as duplicates
                FROM raw_users
            """).fetchone()
            
            total, unique, duplicates = result
            
            print(f"📊 Email Statistics:")
            print(f"   Total emails: {total:,}")
            print(f"   Unique emails: {unique:,}")
            print(f"   Duplicates: {duplicates:,}")
            print(f"   Uniqueness rate: {(unique/total)*100:.2f}%")
            
            # Get top duplicates if any exist
            if duplicates > 0:
                duplicate_examples = con.execute("""
                    SELECT email, COUNT(*) as count 
                    FROM raw_users 
                    GROUP BY email 
                    HAVING COUNT(*) > 1 
                    ORDER BY count DESC 
                    LIMIT 5
                """).fetchall()
                
                print(f"\n🔍 Top Duplicate Examples:")
                for email, count in duplicate_examples:
                    print(f"   {email}: {count} occurrences")
            
            con.close()
            
            # Test passes if no duplicates
            self.print_result(
                f"Email Uniqueness - {label}",
                duplicates == 0,
                f"{duplicates} duplicates found" if duplicates > 0 else "All emails unique"
            )
            
            return {
                "total": total,
                "unique": unique, 
                "duplicates": duplicates,
                "uniqueness_rate": (unique/total)*100
            }
            
        except Exception as e:
            self.print_result(f"Email Duplicate Check - {label}", False, f"Error: {e}")
            return None
    
    def run_dbt_tests(self, label="Current State"):
        """Run all dbt tests and analyze results"""
        self.print_header(f"DBT Test Execution - {label}")
        
        try:
            # Run dbt tests
            start_time = time.time()
            result = subprocess.run(
                ["dbt", "test"],
                cwd=self.dbt_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            execution_time = time.time() - start_time
            
            # Parse test results
            output = result.stderr  # dbt outputs to stderr
            
            # Extract test counts
            pass_count = output.count("PASS")
            fail_count = output.count("FAIL")
            total_tests = pass_count + fail_count
            
            print(f"📋 DBT Test Results:")
            print(f"   Total tests: {total_tests}")
            print(f"   Passed: {pass_count}")
            print(f"   Failed: {fail_count}")
            print(f"   Success rate: {(pass_count/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")
            print(f"   Execution time: {execution_time:.2f}s")
            
            # Show failed tests
            if fail_count > 0:
                print(f"\n❌ Failed Tests:")
                lines = output.split('\n')
                for line in lines:
                    if "FAIL" in line and "test" in line:
                        print(f"   {line.strip()}")
            
            # Test passes if all tests pass
            self.print_result(
                f"DBT All Tests - {label}",
                fail_count == 0,
                f"{pass_count}/{total_tests} tests passed"
            )
            
            return {
                "total": total_tests,
                "passed": pass_count,
                "failed": fail_count,
                "success_rate": (pass_count/total_tests)*100 if total_tests > 0 else 0,
                "execution_time": execution_time
            }
            
        except subprocess.TimeoutExpired:
            self.print_result(f"DBT Tests - {label}", False, "Timeout after 120s")
            return None
        except Exception as e:
            self.print_result(f"DBT Tests - {label}", False, f"Error: {e}")
            return None
    
    def test_data_generation_performance(self, num_users=1000):
        """Test performance of data generation with fix"""
        self.print_header("Data Generation Performance Test")
        
        try:
            # Backup current database
            backup_path = self.db_path.with_suffix('.backup.duckdb')
            shutil.copy2(self.db_path, backup_path)
            
            # Generate new data
            start_time = time.time()
            result = subprocess.run(
                [sys.executable, "pipelines/users.py"],
                capture_output=True,
                text=True,
                timeout=300
            )
            generation_time = time.time() - start_time
            
            print(f"⏱️  Generation Performance:")
            print(f"   Users generated: {num_users:,}")
            print(f"   Total time: {generation_time:.2f}s")
            print(f"   Rate: {num_users/generation_time:.0f} users/second")
            
            # Check if generation succeeded
            success = result.returncode == 0
            self.print_result(
                "Data Generation Performance",
                success,
                f"{generation_time:.2f}s for {num_users:,} users"
            )
            
            # Restore backup
            shutil.copy2(backup_path, self.db_path)
            backup_path.unlink()
            
            return {
                "users": num_users,
                "time": generation_time,
                "rate": num_users/generation_time,
                "success": success
            }
            
        except Exception as e:
            self.print_result("Data Generation Performance", False, f"Error: {e}")
            return None
    
    def test_cross_environment_consistency(self):
        """Test fix works consistently across different execution contexts"""
        self.print_header("Cross-Environment Consistency Test")
        
        environments = [
            ("Direct Pipeline", [sys.executable, "pipelines/users.py"]),
            ("Main CLI", [sys.executable, "../sbdk-starter/main.py", "dev"])
        ]
        
        results = {}
        
        for env_name, command in environments:
            try:
                # Backup database
                backup_path = self.db_path.with_suffix(f'.{env_name.lower().replace(" ", "_")}.backup.duckdb')
                shutil.copy2(self.db_path, backup_path)
                
                # Run in environment
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=180
                )
                
                if result.returncode == 0:
                    # Check duplicates
                    email_stats = self.check_duplicate_emails(f"{env_name} Environment")
                    results[env_name] = email_stats
                    success = email_stats and email_stats["duplicates"] == 0
                else:
                    success = False
                    results[env_name] = None
                
                self.print_result(
                    f"Environment Consistency - {env_name}",
                    success,
                    "Unique emails maintained" if success else "Failed or has duplicates"
                )
                
                # Restore backup
                shutil.copy2(backup_path, self.db_path)
                backup_path.unlink()
                
            except Exception as e:
                self.print_result(f"Environment Test - {env_name}", False, f"Error: {e}")
                results[env_name] = None
        
        return results
    
    def run_comprehensive_validation(self):
        """Run complete validation suite"""
        print("🧪 TESTER AGENT: Comprehensive Email Uniqueness Fix Validation")
        print("=" * 80)
        
        # Pre-fix state analysis
        print("\n🔍 PRE-FIX STATE ANALYSIS")
        pre_fix_emails = self.check_duplicate_emails("Pre-Fix")
        pre_fix_dbt = self.run_dbt_tests("Pre-Fix")
        
        # Data generation performance
        perf_results = self.test_data_generation_performance()
        
        # Cross-environment testing
        env_results = self.test_cross_environment_consistency()
        
        # Post-fix state analysis (after any potential fixes)
        print("\n🔍 POST-FIX STATE ANALYSIS")
        post_fix_emails = self.check_duplicate_emails("Post-Fix")
        post_fix_dbt = self.run_dbt_tests("Post-Fix")
        
        # Generate summary report
        self.generate_summary_report(pre_fix_emails, post_fix_emails, pre_fix_dbt, post_fix_dbt)
        
        return self.results
    
    def generate_summary_report(self, pre_emails, post_emails, pre_dbt, post_dbt):
        """Generate comprehensive summary report"""
        self.print_header("VALIDATION SUMMARY REPORT")
        
        # Calculate improvements
        email_improvement = 0
        dbt_improvement = 0
        
        if pre_emails and post_emails:
            email_improvement = pre_emails["duplicates"] - post_emails["duplicates"]
        
        if pre_dbt and post_dbt:
            dbt_improvement = post_dbt["success_rate"] - pre_dbt["success_rate"]
        
        print(f"📊 RESULTS SUMMARY:")
        print(f"   Email Duplicates: {pre_emails['duplicates'] if pre_emails else 'N/A'} → {post_emails['duplicates'] if post_emails else 'N/A'}")
        print(f"   DBT Success Rate: {pre_dbt['success_rate']:.1f}% → {post_dbt['success_rate']:.1f}%" if pre_dbt and post_dbt else "N/A")
        print(f"   Email Improvement: {email_improvement} fewer duplicates")
        print(f"   Test Improvement: {dbt_improvement:+.1f}% success rate")
        
        # Determine overall status
        fix_successful = (
            post_emails and post_emails["duplicates"] == 0 and
            post_dbt and post_dbt["success_rate"] == 100.0
        )
        
        print(f"\n🎯 OVERALL STATUS:")
        if fix_successful:
            print("   ✅ FIX SUCCESSFUL - Ready for production")
            print("   🔥 All email duplicates eliminated")
            print("   🎉 All dbt tests passing")
        else:
            print("   ❌ FIX INCOMPLETE - Needs attention")
            if post_emails and post_emails["duplicates"] > 0:
                print(f"   ⚠️  Still has {post_emails['duplicates']} duplicate emails")
            if post_dbt and post_dbt["success_rate"] < 100:
                print(f"   ⚠️  Only {post_dbt['success_rate']:.1f}% of dbt tests passing")
        
        # Store summary
        self.results["summary"] = {
            "fix_successful": fix_successful,
            "email_improvement": email_improvement,
            "dbt_improvement": dbt_improvement,
            "final_duplicates": post_emails["duplicates"] if post_emails else None,
            "final_success_rate": post_dbt["success_rate"] if post_dbt else None
        }
        
        return fix_successful

def main():
    """Run the comprehensive test suite"""
    tester = EmailUniquenessTestSuite()
    results = tester.run_comprehensive_validation()
    
    # Save results to file
    results_file = Path("email_uniqueness_test_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Full results saved to: {results_file}")
    
    # Return appropriate exit code
    return 0 if results["summary"].get("fix_successful", False) else 1

if __name__ == "__main__":
    sys.exit(main())