"""
Users pipeline - Generate synthetic user data
"""
import dlt
import duckdb
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta
import random
from pathlib import Path

fake = Faker()

def generate_users_data(num_users: int = 10000) -> list:
    """Generate synthetic user data with guaranteed unique emails"""
    users = []
    used_emails = set()  # Track generated emails to ensure uniqueness
    max_attempts = 10    # Maximum attempts to generate unique email per user
    
    for i in range(1, num_users + 1):
        created_date = fake.date_time_between(start_date='-2y', end_date='now')
        
        # Generate unique email with retry logic
        email = None
        attempts = 0
        while email is None and attempts < max_attempts:
            candidate_email = fake.email()
            if candidate_email not in used_emails:
                email = candidate_email
                used_emails.add(email)
            attempts += 1
        
        # Fallback: if we can't generate unique email, create one manually
        if email is None:
            email = f"user{i}_{fake.random_int(min=1000, max=9999)}@{fake.domain_name()}"
            # Ensure this fallback email is also unique
            while email in used_emails:
                email = f"user{i}_{fake.random_int(min=1000, max=9999)}@{fake.domain_name()}"
            used_emails.add(email)
        
        user = {
            "user_id": i,
            "username": fake.user_name(),
            "email": email,  # Use our guaranteed unique email
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "created_at": created_date,
            "updated_at": fake.date_time_between(start_date=created_date, end_date='now'),
            "country": fake.country_code(),
            "city": fake.city(),
            "subscription_tier": fake.random_element(elements=('free', 'basic', 'premium', 'enterprise')),
            "referrer": fake.random_element(elements=('google', 'bing', 'direct', 'email', 'social', 'affiliate')),
            "is_active": fake.boolean(chance_of_getting_true=85),
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=80),
            "phone": fake.phone_number(),
            "company": fake.company() if fake.boolean(chance_of_getting_true=60) else None,
            "job_title": fake.job() if fake.boolean(chance_of_getting_true=60) else None
        }
        users.append(user)
    
    return users

def run():
    """Execute the users pipeline"""
    print("🏃‍♂️ Running users pipeline...")
    
    # Generate data
    users_data = generate_users_data()
    print(f"📊 Generated {len(users_data)} user records")
    
    # Create DataFrame
    df = pd.DataFrame(users_data)
    
    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)
    
    # Connect to DuckDB
    con = duckdb.connect('data/dev.duckdb')
    
    # Create raw users table
    con.execute("DROP TABLE IF EXISTS raw_users")
    con.execute("CREATE TABLE raw_users AS SELECT * FROM df")
    
    # Create some indexes for better performance
    con.execute("CREATE INDEX IF NOT EXISTS idx_users_id ON raw_users(user_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_users_created ON raw_users(created_at)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_users_country ON raw_users(country)")
    
    # Print summary statistics
    result = con.execute("""
        SELECT 
            COUNT(*) as total_users,
            COUNT(DISTINCT country) as countries,
            COUNT(*) FILTER (WHERE is_active = true) as active_users,
            MIN(created_at) as earliest_user,
            MAX(created_at) as latest_user
        FROM raw_users
    """).fetchone()
    
    print(f"""📈 Users Pipeline Results:
    - Total users: {result[0]:,}
    - Countries: {result[1]}
    - Active users: {result[2]:,} ({result[2]/result[0]*100:.1f}%)
    - Date range: {result[3]} to {result[4]}
    """)
    
    con.close()
    print("✅ Users pipeline completed successfully!")

if __name__ == "__main__":
    run()