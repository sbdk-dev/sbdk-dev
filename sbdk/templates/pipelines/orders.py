"""
Orders pipeline - Generate synthetic e-commerce order data
"""

import json
import random
import uuid
from datetime import timedelta
from pathlib import Path

import duckdb
import pandas as pd
from faker import Faker

fake = Faker()


def load_config() -> dict:
    """Load SBDK configuration"""
    with open("sbdk_config.json") as f:
        return json.load(f)


def generate_orders_data(num_orders: int = 20000, max_user_id: int = 10000) -> list:
    """Generate synthetic order data"""
    orders = []

    # Product categories with realistic pricing ranges
    product_categories = {
        "subscription": (9.99, 99.99),
        "premium_addon": (4.99, 49.99),
        "enterprise_addon": (19.99, 199.99),
        "renewal": (9.99, 149.99),
        "upgrade": (19.99, 299.99),
        "training": (99.99, 999.99),
        "support": (49.99, 499.99),
        "consulting": (199.99, 1999.99),
    }

    # Payment methods with realistic distribution
    payment_methods = [
        ("credit_card", 60),
        ("paypal", 20),
        ("stripe", 12),
        ("bank_transfer", 5),
        ("crypto", 2),
        ("wire", 1),
    ]

    weighted_payments = []
    for method, weight in payment_methods:
        weighted_payments.extend([method] * weight)

    # Order statuses with weights
    order_statuses = [
        ("completed", 80),
        ("pending", 10),
        ("cancelled", 5),
        ("refunded", 3),
        ("failed", 2),
    ]

    weighted_statuses = []
    for status, weight in order_statuses:
        weighted_statuses.extend([status] * weight)

    for i in range(1, num_orders + 1):
        # Some users make multiple orders
        if random.random() < 0.4:  # 40% repeat customers
            user_id = random.randint(1, max_user_id // 3)
        else:
            user_id = random.randint(1, max_user_id)

        # Order timing - more recent orders weighted higher
        days_ago = random.choices(
            range(1, 366), weights=[366 - i for i in range(1, 366)], k=1
        )[0]
        order_date = fake.date_time_between(start_date=f"-{days_ago}d", end_date="now")

        # Select product category and calculate amount
        category = random.choice(list(product_categories.keys()))
        min_price, max_price = product_categories[category]
        base_amount = round(random.uniform(min_price, max_price), 2)

        # Add potential discounts
        discount_rate = 0
        if random.random() < 0.3:  # 30% have discounts
            discount_rate = random.uniform(0.05, 0.5)

        # Calculate taxes (realistic rates)
        tax_rate = random.uniform(0.05, 0.15)
        subtotal = base_amount * (1 - discount_rate)
        tax_amount = subtotal * tax_rate
        total_amount = subtotal + tax_amount

        # Order status affects completion date
        status = random.choice(weighted_statuses)
        if status == "completed":
            completed_at = order_date + timedelta(hours=random.randint(1, 72))
        else:
            completed_at = None

        order = {
            "order_id": str(uuid.uuid4()),
            "user_id": user_id,
            "order_number": f"ORD-{i:06d}",
            "created_at": order_date,
            "completed_at": completed_at,
            "status": status,
            "product_category": category,
            "product_sku": f"{category.upper()}-{random.randint(100, 999)}",
            "quantity": random.randint(1, 5),
            "unit_price": base_amount,
            "subtotal": round(subtotal, 2),
            "discount_amount": (
                round(base_amount * discount_rate, 2) if discount_rate > 0 else 0
            ),
            "discount_code": fake.lexify("????##") if discount_rate > 0 else None,
            "tax_amount": round(tax_amount, 2),
            "total_amount": round(total_amount, 2),
            "currency": fake.random_element(
                elements=("USD", "EUR", "GBP", "CAD", "AUD")
            ),
            "payment_method": random.choice(weighted_payments),
            "payment_processor": fake.random_element(
                elements=("stripe", "paypal", "square", "braintree")
            ),
            "billing_country": fake.country_code(),
            "billing_state": fake.state_abbr(),
            "billing_city": fake.city(),
            "billing_postal_code": fake.postcode(),
            "is_recurring": fake.boolean(chance_of_getting_true=35),
            "subscription_period": (
                fake.random_element(elements=("monthly", "quarterly", "yearly"))
                if random.random() < 0.35
                else None
            ),
            "utm_source": fake.random_element(
                elements=("google", "facebook", "direct", "email", "affiliate")
            ),
            "utm_campaign": fake.catch_phrase() if random.random() < 0.4 else None,
            "referral_code": fake.lexify("REF####") if random.random() < 0.15 else None,
            "customer_notes": (
                fake.text(max_nb_chars=200) if random.random() < 0.2 else None
            ),
            "shipping_required": fake.boolean(chance_of_getting_true=20),
            "shipping_cost": (
                round(random.uniform(5, 50), 2) if random.random() < 0.2 else 0
            ),
            "estimated_delivery": (
                order_date + timedelta(days=random.randint(3, 14))
                if random.random() < 0.2
                else None
            ),
        }

        orders.append(order)

    return orders


def run():
    """Execute the orders pipeline"""
    print("🏃‍♂️ Running orders pipeline...")

    # Generate data
    orders_data = generate_orders_data()
    print(f"📊 Generated {len(orders_data)} order records")

    # Create DataFrame
    df = pd.DataFrame(orders_data)

    # Load config to get database path
    config = load_config()

    # Ensure data directory exists
    db_path = Path(config["duckdb_path"])
    db_path.parent.mkdir(exist_ok=True)

    # Connect to DuckDB
    con = duckdb.connect(str(db_path))

    # Register DataFrame with DuckDB
    con.register('df', df)

    # Create raw orders table
    con.execute("DROP TABLE IF EXISTS raw_orders")
    con.execute("CREATE TABLE raw_orders AS SELECT * FROM df")

    # Create indexes for better performance
    con.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON raw_orders(user_id)")
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_orders_created ON raw_orders(created_at)"
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON raw_orders(status)")
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_orders_category ON raw_orders(product_category)"
    )

    # Print comprehensive summary statistics
    summary = con.execute(
        """
        SELECT
            COUNT(*) as total_orders,
            COUNT(DISTINCT user_id) as unique_customers,
            COUNT(*) FILTER (WHERE status = 'completed') as completed_orders,
            COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_orders,
            COALESCE(SUM(total_amount) FILTER (WHERE status = 'completed'), 0) as total_revenue,
            COALESCE(AVG(total_amount) FILTER (WHERE status = 'completed'), 0) as avg_order_value,
            MIN(created_at) as earliest_order,
            MAX(created_at) as latest_order,
            COUNT(*) FILTER (WHERE is_recurring = true) as recurring_orders
        FROM raw_orders
    """
    ).fetchone()

    # Top categories by revenue
    top_categories = con.execute(
        """
        SELECT
            product_category,
            COUNT(*) as orders,
            COALESCE(SUM(total_amount) FILTER (WHERE status = 'completed'), 0) as revenue,
            ROUND(AVG(total_amount) FILTER (WHERE status = 'completed'), 2) as avg_value
        FROM raw_orders
        GROUP BY product_category
        ORDER BY revenue DESC
        LIMIT 5
    """
    ).fetchall()

    # Payment method distribution
    payment_dist = con.execute(
        """
        SELECT
            payment_method,
            COUNT(*) as orders,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM raw_orders), 1) as percentage
        FROM raw_orders
        WHERE status = 'completed'
        GROUP BY payment_method
        ORDER BY orders DESC
    """
    ).fetchall()

    print(
        f"""📈 Orders Pipeline Results:
    - Total orders: {summary[0]:,}
    - Unique customers: {summary[1]:,}
    - Completed orders: {summary[2]:,} ({summary[2]/summary[0]*100:.1f}%)
    - Cancelled orders: {summary[3]:,} ({summary[3]/summary[0]*100:.1f}%)
    - Total revenue: ${summary[4]:,.2f}
    - Average order value: ${summary[5]:.2f}
    - Recurring orders: {summary[8]:,} ({summary[8]/summary[0]*100:.1f}%)
    - Date range: {summary[6]} to {summary[7]}

    Top Categories by Revenue:"""
    )

    for category, orders, revenue, avg_value in top_categories:
        print(
            f"    - {category}: {orders:,} orders, ${revenue:,.2f} (avg: ${avg_value})"
        )

    print("\n    Payment Method Distribution:")
    for method, orders, percentage in payment_dist:
        print(f"    - {method}: {orders:,} orders ({percentage}%)")

    con.close()
    print("✅ Orders pipeline completed successfully!")


if __name__ == "__main__":
    run()
