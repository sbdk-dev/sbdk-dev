"""
Users pipeline - Generate synthetic user data
"""

import json
from pathlib import Path

import duckdb
import pandas as pd
from faker import Faker

fake = Faker()


def load_config() -> dict:
    """Load SBDK configuration"""
    with open("sbdk_config.json") as f:
        return json.load(f)


def generate_users_data(num_users: int = None) -> list:
    """Generate synthetic user data"""
    import os

    # Use environment variable with fallback default
    if num_users is None:
        num_users = int(os.getenv("SBDK_NUM_USERS", "10000"))

    users = []

    for i in range(1, num_users + 1):
        created_date = fake.date_time_between(start_date="-2y", end_date="now")

        user = {
            "user_id": i,
            "username": fake.user_name(),
            "email": fake.email(),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "created_at": created_date,
            "updated_at": fake.date_time_between(
                start_date=created_date, end_date="now"
            ),
            "country": fake.country_code(),
            "city": fake.city(),
            "subscription_tier": fake.random_element(
                elements=("free", "basic", "premium", "enterprise")
            ),
            "referrer": fake.random_element(
                elements=("google", "bing", "direct", "email", "social", "affiliate")
            ),
            "is_active": fake.boolean(chance_of_getting_true=85),
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=80),
            "phone": fake.phone_number(),
            "company": (
                fake.company() if fake.boolean(chance_of_getting_true=60) else None
            ),
            "job_title": (
                fake.job() if fake.boolean(chance_of_getting_true=60) else None
            ),
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

    # Load config to get database path
    config = load_config()

    # Ensure data directory exists
    db_path = Path(config["duckdb_path"])
    db_path.parent.mkdir(exist_ok=True)

    # Connect to DuckDB
    con = duckdb.connect(str(db_path))

    # Register DataFrame with DuckDB
    con.register('df', df)

    # Create raw users table
    con.execute("DROP TABLE IF EXISTS raw_users")
    con.execute("CREATE TABLE raw_users AS SELECT * FROM df")

    # Create some indexes for better performance
    con.execute("CREATE INDEX IF NOT EXISTS idx_users_id ON raw_users(user_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_users_created ON raw_users(created_at)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_users_country ON raw_users(country)")

    # Print summary statistics
    result = con.execute(
        """
        SELECT
            COUNT(*) as total_users,
            COUNT(DISTINCT country) as countries,
            COUNT(*) FILTER (WHERE is_active = true) as active_users,
            MIN(created_at) as earliest_user,
            MAX(created_at) as latest_user
        FROM raw_users
    """
    ).fetchone()

    print(
        f"""📈 Users Pipeline Results:
    - Total users: {result[0]:,}
    - Countries: {result[1]}
    - Active users: {result[2]:,} ({result[2]/result[0]*100:.1f}%)
    - Date range: {result[3]} to {result[4]}
    """
    )

    con.close()
    print("✅ Users pipeline completed successfully!")


if __name__ == "__main__":
    run()
