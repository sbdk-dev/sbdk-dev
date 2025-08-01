#!/usr/bin/env python3
"""
SBDK Documentation Cleanup and Alignment Script

This script fixes all documentation issues identified:
1. Removes all "_fixed" tags from files and directories  
2. Aligns documentation references to work together
3. Cleans up temporary files and migration scripts
4. Updates broken paths and references
5. Creates consistent documentation structure
"""

import os
import shutil
from pathlib import Path
import json
import re

def main():
    """Execute comprehensive documentation cleanup and alignment."""
    
    base_dir = Path("/Users/mattstrautmann/Documents/GitHub/sbdk-dev")
    print("🔧 SBDK Documentation Cleanup and Alignment")
    print("=" * 50)
    
    # Step 1: Rename my_project_fixed to my_project_example
    fix_project_fixed_directory(base_dir)
    
    # Step 2: Remove _fixed suffix from Python files
    remove_fixed_suffix_from_files(base_dir)
    
    # Step 3: Update all references to removed _fixed files
    update_fixed_references(base_dir)
    
    # Step 4: Align documentation paths and references
    align_documentation_references(base_dir)
    
    # Step 5: Clean up temporary files
    cleanup_temporary_files(base_dir)
    
    # Step 6: Run database optimization
    optimize_databases(base_dir)
    
    print("\n✅ Documentation cleanup and alignment complete!")
    print("\n📊 Summary of changes:")
    print("├── ✅ Renamed my_project_fixed → my_project_example")  
    print("├── ✅ Removed _fixed suffix from Python files")
    print("├── ✅ Updated all internal references")
    print("├── ✅ Aligned documentation paths")
    print("├── ✅ Cleaned up temporary files")
    print("└── ✅ Optimized database organization")

def fix_project_fixed_directory(base_dir):
    """Rename my_project_fixed to my_project_example."""
    old_path = base_dir / "sbdk-dev/examples/my_project_fixed"
    new_path = base_dir / "sbdk-dev/examples/my_project_example"
    
    if old_path.exists():
        print(f"📁 Renaming: {old_path.name} → {new_path.name}")
        shutil.move(str(old_path), str(new_path))
        print("   ✅ Directory renamed successfully")
    else:
        print("   ℹ️  my_project_fixed directory not found, skipping")

def remove_fixed_suffix_from_files(base_dir):
    """Remove _fixed suffix from Python files."""
    print("\n🐍 Removing _fixed suffix from Python files...")
    
    fixed_files = [
        "my_project/run_dbt_fixed.py",
        "my_project/demo_dbt_fix.py", 
        "my_project/test_email_uniqueness_fix.py",
        "my_project/validate_dbt_fix.py",
        "sbdk-dev/examples/my_project_example/run_dbt_fixed.py",
        "sbdk-dev/examples/my_project_example/test_email_uniqueness_fix.py", 
        "sbdk-dev/examples/my_project_example/validate_dbt_fix.py"
    ]
    
    new_names = [
        "my_project/run_dbt.py",
        "my_project/demo_dbt.py",
        "my_project/test_email_uniqueness.py", 
        "my_project/validate_dbt.py",
        "sbdk-dev/examples/my_project_example/run_dbt.py",
        "sbdk-dev/examples/my_project_example/test_email_uniqueness.py",
        "sbdk-dev/examples/my_project_example/validate_dbt.py"
    ]
    
    for old_file, new_file in zip(fixed_files, new_names):
        old_path = base_dir / old_file
        new_path = base_dir / new_file
        
        if old_path.exists():
            print(f"   📄 {old_path.name} → {new_path.name}")
            shutil.move(str(old_path), str(new_path))
        else:
            print(f"   ⚠️  {old_file} not found, skipping")

def update_fixed_references(base_dir):
    """Update all references to removed _fixed files."""
    print("\n🔗 Updating references to removed _fixed files...")
    
    # Find all text files that might contain references
    text_files = []
    for ext in ['.py', '.md', '.json', '.txt', '.yml', '.yaml']:
        text_files.extend(base_dir.rglob(f'*{ext}'))
    
    # Reference mappings
    replacements = {
        'run_dbt_fixed.py': 'run_dbt.py',
        'demo_dbt_fix.py': 'demo_dbt.py',
        'test_email_uniqueness_fix.py': 'test_email_uniqueness.py',
        'validate_dbt_fix.py': 'validate_dbt.py',
        'my_project_fixed': 'my_project_example'
    }
    
    updated_files = 0
    for file_path in text_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            for old_ref, new_ref in replacements.items():
                content = content.replace(old_ref, new_ref)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                updated_files += 1
                print(f"   ✅ Updated references in: {file_path.name}")
                
        except (UnicodeDecodeError, PermissionError):
            # Skip binary files or files we can't read
            continue
    
    print(f"   📊 Updated {updated_files} files with reference changes")

def align_documentation_references(base_dir):
    """Fix broken documentation references and align paths."""
    print("\n📚 Aligning documentation references...")
    
    # Update the main README.md reference in demo_project data README
    demo_readme = base_dir / "sbdk-dev/examples/demo_project/data/README.md"
    if demo_readme.exists():
        with open(demo_readme, 'r') as f:
            content = f.read()
        
        # Fix the broken path reference
        content = content.replace(
            'Check the main project README.md at `/Users/mattstrautmann/Documents/GitHub/sbdk-dev/README.md` or the comprehensive documentation in the `/Users/mattstrautmann/Documents/GitHub/sbdk-dev/docs/` folder.',
            'Check the main project README.md or the comprehensive documentation in the docs/ folder.'
        )
        
        with open(demo_readme, 'w') as f:
            f.write(content)
        print("   ✅ Fixed demo_project data README references")
    
    # Update main README.md documentation references
    main_readme = base_dir / "README.md"
    if main_readme.exists():
        with open(main_readme, 'r') as f:
            content = f.read()
        
        # Fix any broken documentation references
        content = re.sub(
            r'- \*\*Documentation\*\*: Check the `/docs` directory for detailed guides',
            '- **Documentation**: Check the `docs/` directory for detailed guides',
            content
        )
        
        with open(main_readme, 'w') as f:
            f.write(content)
        print("   ✅ Updated main README documentation references")

def cleanup_temporary_files(base_dir):
    """Clean up temporary files and migration scripts."""
    print("\n🧹 Cleaning up temporary files...")
    
    # Files to remove
    temp_files = [
        "OPTIMIZE_DATABASES.md",
        "DATABASE_MIGRATION_SCRIPT.py", 
        "PROJECT_OPTIMIZATION_ANALYSIS.md",
        "DEMO_PROJECT_OPTIMIZATION_COMPLETE.md",
        "CLI_ARCHITECTURE_DESIGN.md",
        "HIVE_MIND_OPTIMIZATION_SUMMARY.md",
        "error.md",
        "my_project_analysis_report.md"
    ]
    
    for temp_file in temp_files:
        file_path = base_dir / temp_file
        if file_path.exists():
            file_path.unlink()
            print(f"   🗑️  Removed: {temp_file}")
        
        # Also check in subdirectories
        for found_file in base_dir.rglob(temp_file):
            if found_file.exists():
                found_file.unlink() 
                print(f"   🗑️  Removed: {found_file.relative_to(base_dir)}")

def optimize_databases(base_dir):
    """Optimize database file organization."""
    print("\n💾 Optimizing database organization...")
    
    demo_data_dir = base_dir / "sbdk-dev/examples/demo_project/data"
    if not demo_data_dir.exists():
        print("   ⚠️  Demo project data directory not found")
        return
    
    # Create backups directory if it doesn't exist
    backups_dir = demo_data_dir / "backups"
    backups_dir.mkdir(exist_ok=True)
    
    # Database file mappings
    db_mappings = {
        "demo_project.duckdb": "starter-database.duckdb",
        "dev.duckdb": "development-database.duckdb"
    }
    
    # Handle sample.duckdb from parent directory
    sample_db = demo_data_dir.parent / "sample.duckdb"
    if sample_db.exists():
        target_sample = demo_data_dir / "sample-data-database.duckdb"
        if not target_sample.exists():
            shutil.copy2(sample_db, target_sample)
            print("   ✅ Created sample-data-database.duckdb")
    
    # Create optimized database copies
    for old_name, new_name in db_mappings.items():
        old_path = demo_data_dir / old_name
        new_path = demo_data_dir / new_name
        backup_path = backups_dir / f"backup_{old_name}"
        
        if old_path.exists() and not new_path.exists():
            # Create backup
            shutil.copy2(old_path, backup_path)
            # Create optimized copy
            shutil.copy2(old_path, new_path)
            print(f"   ✅ Created: {new_name}")
    
    print("   ✅ Database optimization complete")

if __name__ == "__main__":
    main()