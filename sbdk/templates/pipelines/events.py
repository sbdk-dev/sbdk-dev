"""
Events pipeline - Generate synthetic event tracking data
"""

import json
import random
import uuid
from pathlib import Path

import duckdb
import pandas as pd
from faker import Faker

fake = Faker()


def load_config() -> dict:
    """Load SBDK configuration"""
    with open("sbdk_config.json") as f:
        return json.load(f)


def generate_events_data(num_events: int = None, max_user_id: int = None) -> list:
    """Generate synthetic event tracking data"""
    import os

    # Use environment variables with fallback defaults
    if num_events is None:
        num_events = int(os.getenv("SBDK_NUM_EVENTS", "50000"))
    if max_user_id is None:
        max_user_id = int(os.getenv("SBDK_NUM_USERS", "10000"))

    events = []

    # Define event types with weights (more realistic distribution)
    event_types = [
        ("page_view", 40),
        ("click", 25),
        ("scroll", 15),
        ("signup", 2),
        ("login", 8),
        ("logout", 3),
        ("purchase", 1),
        ("add_to_cart", 4),
        ("search", 2),
    ]

    # Create weighted list for sampling
    weighted_events = []
    for event_type, weight in event_types:
        weighted_events.extend([event_type] * weight)

    # UTM sources with realistic distribution
    utm_sources = [
        ("google", 30),
        ("facebook", 20),
        ("direct", 25),
        ("email", 10),
        ("instagram", 8),
        ("twitter", 4),
        ("linkedin", 3),
    ]

    weighted_utm = []
    for utm, weight in utm_sources:
        weighted_utm.extend([utm] * weight)

    for _i in range(1, num_events + 1):
        # Random user (some users are more active)
        if random.random() < 0.3:  # 30% of events from power users (first 20% of users)
            user_id = random.randint(1, max_user_id // 5)
        else:
            user_id = random.randint(1, max_user_id)

        event_time = fake.date_time_between(start_date="-90d", end_date="now")
        event_type = random.choice(weighted_events)

        event = {
            "event_id": str(uuid.uuid4()),
            "user_id": user_id,
            "session_id": (
                str(uuid.uuid4()) if random.random() < 0.1 else None
            ),  # 10% have session tracking
            "event_type": event_type,
            "timestamp": event_time,
            "utm_source": random.choice(weighted_utm),
            "utm_medium": fake.random_element(
                elements=("cpc", "organic", "email", "social", "referral")
            ),
            "utm_campaign": fake.catch_phrase() if random.random() < 0.3 else None,
            "page_url": fake.url(),
            "referrer_url": fake.url() if random.random() < 0.7 else None,
            "user_agent": fake.user_agent(),
            "ip_address": fake.ipv4(),
            "country": fake.country_code(),
            "device_type": fake.random_element(
                elements=("desktop", "mobile", "tablet")
            ),
            "browser": fake.random_element(
                elements=("Chrome", "Firefox", "Safari", "Edge", "Opera")
            ),
            "os": fake.random_element(
                elements=("Windows", "macOS", "Linux", "iOS", "Android")
            ),
            "screen_resolution": f"{random.choice([1920, 1366, 1536, 1440, 1024])}x{random.choice([1080, 768, 864, 900, 768])}",
            "is_mobile": fake.boolean(chance_of_getting_true=45),
            "duration_seconds": (
                random.randint(1, 1800) if event_type == "page_view" else None
            ),
            "revenue": (
                round(random.uniform(10, 500), 2) if event_type == "purchase" else None
            ),
        }

        events.append(event)

    return events


def run():
    """Execute the events pipeline"""
    print("🏃‍♂️ Running events pipeline...")

    # Generate data
    events_data = generate_events_data()
    print(f"📊 Generated {len(events_data)} event records")

    # Create DataFrame
    df = pd.DataFrame(events_data)

    # Load config to get database path
    config = load_config()

    # Ensure data directory exists
    db_path = Path(config["duckdb_path"])
    db_path.parent.mkdir(exist_ok=True)

    # Connect to DuckDB
    con = duckdb.connect(str(db_path))

    # Register DataFrame with DuckDB
    con.register('df', df)

    # Create raw events table
    con.execute("DROP TABLE IF EXISTS raw_events")
    con.execute("CREATE TABLE raw_events AS SELECT * FROM df")

    # Create indexes for better performance
    con.execute("CREATE INDEX IF NOT EXISTS idx_events_user ON raw_events(user_id)")
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON raw_events(timestamp)"
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON raw_events(event_type)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_events_utm ON raw_events(utm_source)")

    # Print summary statistics
    result = con.execute(
        """
        SELECT
            COUNT(*) as total_events,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT event_type) as event_types,
            COUNT(*) FILTER (WHERE event_type = 'purchase') as purchases,
            COALESCE(SUM(revenue), 0) as total_revenue,
            MIN(timestamp) as earliest_event,
            MAX(timestamp) as latest_event
        FROM raw_events
    """
    ).fetchone()

    # Top event types
    top_events = con.execute(
        """
        SELECT event_type, COUNT(*) as count,
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM raw_events), 1) as percentage
        FROM raw_events
        GROUP BY event_type
        ORDER BY count DESC
        LIMIT 5
    """
    ).fetchall()

    print(
        f"""📈 Events Pipeline Results:
    - Total events: {result[0]:,}
    - Unique users: {result[1]:,}
    - Event types: {result[2]}
    - Purchases: {result[3]:,}
    - Total revenue: ${result[4]:,.2f}
    - Date range: {result[5]} to {result[6]}

    Top Event Types:"""
    )

    for event_type, count, percentage in top_events:
        print(f"    - {event_type}: {count:,} ({percentage}%)")

    con.close()
    print("✅ Events pipeline completed successfully!")


if __name__ == "__main__":
    run()
