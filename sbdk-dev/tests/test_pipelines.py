"""
Test cases for SBDK.dev pipelines
"""
import pytest
import duckdb
import os
from pathlib import Path

# Test fixtures
@pytest.fixture
def test_db_path():
    """Create a temporary test database"""
    return "test_data.duckdb"

@pytest.fixture(autouse=True)
def cleanup_test_db(test_db_path):
    """Clean up test database after each test"""
    yield
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

def test_users_pipeline():
    """Test users pipeline generates valid data"""
    from pipelines.users import generate_users_data
    
    # Generate small sample
    users = generate_users_data(100)
    
    # Validate structure
    assert len(users) == 100
    assert all('user_id' in user for user in users)
    assert all('email' in user for user in users)
    assert all('created_at' in user for user in users)
    
    # Validate data types
    assert all(isinstance(user['user_id'], int) for user in users)
    assert all('@' in user['email'] for user in users)
    assert all(user['subscription_tier'] in ['free', 'basic', 'premium', 'enterprise'] for user in users)

def test_events_pipeline():
    """Test events pipeline generates valid data"""
    from pipelines.events import generate_events_data
    
    # Generate small sample
    events = generate_events_data(500, max_user_id=100)
    
    # Validate structure
    assert len(events) == 500
    assert all('event_id' in event for event in events)
    assert all('user_id' in event for event in events)
    assert all('event_type' in event for event in events)
    assert all('timestamp' in event for event in events)
    
    # Validate user_id range
    assert all(1 <= event['user_id'] <= 100 for event in events)
    
    # Validate event types
    valid_events = ['page_view', 'click', 'scroll', 'signup', 'login', 'logout', 'purchase', 'add_to_cart', 'search']
    assert all(event['event_type'] in valid_events for event in events)

def test_orders_pipeline():
    """Test orders pipeline generates valid data"""
    from pipelines.orders import generate_orders_data
    
    # Generate small sample
    orders = generate_orders_data(200, max_user_id=100)
    
    # Validate structure
    assert len(orders) == 200
    assert all('order_id' in order for order in orders)
    assert all('user_id' in order for order in orders)
    assert all('total_amount' in order for order in orders)
    assert all('status' in order for order in orders)
    
    # Validate amounts are positive
    assert all(order['total_amount'] > 0 for order in orders)
    
    # Validate status values
    valid_statuses = ['completed', 'pending', 'cancelled', 'refunded', 'failed']
    assert all(order['status'] in valid_statuses for order in orders)

def test_database_creation(test_db_path):
    """Test that DuckDB database can be created and queried"""
    import pandas as pd
    
    # Create sample data
    sample_data = [
        {"id": 1, "name": "test1", "value": 100},
        {"id": 2, "name": "test2", "value": 200}
    ]
    
    df = pd.DataFrame(sample_data)
    
    # Create database and table
    con = duckdb.connect(test_db_path)
    con.execute("CREATE TABLE test_table AS SELECT * FROM df")
    
    # Query data
    result = con.execute("SELECT COUNT(*) FROM test_table").fetchone()
    assert result[0] == 2
    
    # Query specific values
    result = con.execute("SELECT SUM(value) FROM test_table").fetchone()
    assert result[0] == 300
    
    con.close()

def test_pipeline_integration():
    """Test full pipeline integration with DuckDB"""
    from pipelines import users, events, orders
    import tempfile
    import os
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        # Create data directory
        os.makedirs("data", exist_ok=True)
        
        try:
            # Run pipelines (small scale)
            # Note: We'd need to modify the pipeline modules to accept parameters
            # For now, just test that they can be imported
            assert hasattr(users, 'run')
            assert hasattr(events, 'run')
            assert hasattr(orders, 'run')
            
        finally:
            os.chdir(original_cwd)

def test_cli_commands():
    """Test CLI command functions"""
    from cli.init import cli_init
    from cli.dev import load_config
    import tempfile
    import json
    
    # Test config loading
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_config = {
            "project": "test_project",
            "target": "dev",
            "duckdb_path": "test.duckdb"
        }
        json.dump(test_config, f)
        f.flush()
        
        # Test config loading
        config = load_config(f.name)
        assert config['project'] == 'test_project'
        assert config['target'] == 'dev'
        
        # Clean up
        os.unlink(f.name)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])