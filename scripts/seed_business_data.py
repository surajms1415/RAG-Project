import os
import sys
from datetime import datetime, timedelta, timezone

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from src.app.core.database import SessionLocal
from src.app.models.analytics import Customer, Product, Order, OrderItem


def seed_business_data(reset: bool = False) -> None:
    """Populates the database with realistic business analytics data."""
    db = SessionLocal()
    try:
        if reset:
            print("Resetting business analytics tables...")
            db.query(OrderItem).delete()
            db.query(Order).delete()
            db.query(Product).delete()
            db.query(Customer).delete()
            db.commit()

        existing_customers = db.query(Customer).count()
        if existing_customers > 0 and not reset:
            print(f"Database already contains {existing_customers} customers. Skipping seeding. (Use --reset to override)")
            return

        print("Seeding business analytics dataset...")

        # 1. Seed Customers
        customers_data = [
            {"id": "cust-001", "name": "Acme Global Industries", "email": "procurement@acme.com", "segment": "Enterprise", "country": "United States", "city": "New York"},
            {"id": "cust-002", "name": "TechTrend Solutions", "email": "ops@techtrend.io", "segment": "SMB", "country": "United States", "city": "Austin"},
            {"id": "cust-003", "name": "Zenith Retail Corp", "email": "inventory@zenith.com", "segment": "Consumer", "country": "United States", "city": "Chicago"},
            {"id": "cust-004", "name": "Apex Global UK", "email": "billing@apex.co.uk", "segment": "Enterprise", "country": "United Kingdom", "city": "London"},
            {"id": "cust-005", "name": "Quantum Dynamics", "email": "systems@quantumdyn.com", "segment": "Enterprise", "country": "United States", "city": "San Francisco"},
            {"id": "cust-006", "name": "Pulse Cloud Systems", "email": "admin@pulsecloud.com", "segment": "SMB", "country": "United States", "city": "Seattle"},
            {"id": "cust-007", "name": "Summit Healthcare AI", "email": "info@summithealth.org", "segment": "Enterprise", "country": "United States", "city": "Boston"},
            {"id": "cust-008", "name": "Horizon Innovation Labs", "email": "contact@horizonlabs.de", "segment": "SMB", "country": "Germany", "city": "Berlin"},
        ]

        customers_map = {}
        for c in customers_data:
            cust = Customer(**c)
            db.add(cust)
            customers_map[c["id"]] = cust
        db.commit()

        # 2. Seed Products
        products_data = [
            {"id": "prod-001", "name": "AI Workflow Platform", "category": "Software", "unit_price": 1200.0, "cost": 150.0, "stock_quantity": 999},
            {"id": "prod-002", "name": "Enterprise Knowledge Assistant", "category": "Software", "unit_price": 2400.0, "cost": 300.0, "stock_quantity": 999},
            {"id": "prod-003", "name": "Edge Inference Gateway", "category": "Hardware", "unit_price": 850.0, "cost": 420.0, "stock_quantity": 45},
            {"id": "prod-004", "name": "GPU Acceleration Node", "category": "Hardware", "unit_price": 4500.0, "cost": 2800.0, "stock_quantity": 20},
            {"id": "prod-005", "name": "MLOps Integration Consulting", "category": "Services", "unit_price": 3500.0, "cost": 1200.0, "stock_quantity": 100},
            {"id": "prod-006", "name": "Cloud Storage Dedicated (TB)", "category": "Cloud", "unit_price": 120.0, "cost": 25.0, "stock_quantity": 5000},
            {"id": "prod-007", "name": "Managed Vector Index Service", "category": "Cloud", "unit_price": 450.0, "cost": 80.0, "stock_quantity": 500},
            {"id": "prod-008", "name": "Data Pipeline Audit & Review", "category": "Services", "unit_price": 1800.0, "cost": 600.0, "stock_quantity": 50},
        ]

        products_map = {}
        for p in products_data:
            prod = Product(**p)
            db.add(prod)
            products_map[p["id"]] = prod
        db.commit()

        # 3. Seed Orders and Line Items
        now = datetime.now(timezone.utc)
        orders_spec = [
            {
                "id": "ord-1001", "customer_id": "cust-001", "status": "Completed", "shipping_city": "New York",
                "days_ago": 60,
                "items": [
                    {"product_id": "prod-002", "quantity": 2, "unit_price": 2400.0},
                    {"product_id": "prod-007", "quantity": 4, "unit_price": 450.0},
                ]
            },
            {
                "id": "ord-1002", "customer_id": "cust-002", "status": "Completed", "shipping_city": "Austin",
                "days_ago": 55,
                "items": [
                    {"product_id": "prod-001", "quantity": 1, "unit_price": 1200.0},
                    {"product_id": "prod-003", "quantity": 2, "unit_price": 850.0},
                ]
            },
            {
                "id": "ord-1003", "customer_id": "cust-005", "status": "Completed", "shipping_city": "San Francisco",
                "days_ago": 45,
                "items": [
                    {"product_id": "prod-004", "quantity": 3, "unit_price": 4500.0},
                    {"product_id": "prod-005", "quantity": 1, "unit_price": 3500.0},
                ]
            },
            {
                "id": "ord-1004", "customer_id": "cust-007", "status": "Completed", "shipping_city": "Boston",
                "days_ago": 40,
                "items": [
                    {"product_id": "prod-002", "quantity": 1, "unit_price": 2400.0},
                    {"product_id": "prod-008", "quantity": 1, "unit_price": 1800.0},
                ]
            },
            {
                "id": "ord-1005", "customer_id": "cust-004", "status": "Completed", "shipping_city": "London",
                "days_ago": 30,
                "items": [
                    {"product_id": "prod-001", "quantity": 3, "unit_price": 1200.0},
                    {"product_id": "prod-006", "quantity": 10, "unit_price": 120.0},
                ]
            },
            {
                "id": "ord-1006", "customer_id": "cust-003", "status": "Completed", "shipping_city": "Chicago",
                "days_ago": 25,
                "items": [
                    {"product_id": "prod-003", "quantity": 1, "unit_price": 850.0},
                ]
            },
            {
                "id": "ord-1007", "customer_id": "cust-006", "status": "Completed", "shipping_city": "Seattle",
                "days_ago": 20,
                "items": [
                    {"product_id": "prod-006", "quantity": 25, "unit_price": 120.0},
                    {"product_id": "prod-007", "quantity": 2, "unit_price": 450.0},
                ]
            },
            {
                "id": "ord-1008", "customer_id": "cust-008", "status": "Completed", "shipping_city": "Berlin",
                "days_ago": 15,
                "items": [
                    {"product_id": "prod-001", "quantity": 2, "unit_price": 1200.0},
                    {"product_id": "prod-005", "quantity": 1, "unit_price": 3500.0},
                ]
            },
            {
                "id": "ord-1009", "customer_id": "cust-001", "status": "Completed", "shipping_city": "New York",
                "days_ago": 10,
                "items": [
                    {"product_id": "prod-004", "quantity": 1, "unit_price": 4500.0},
                    {"product_id": "prod-002", "quantity": 1, "unit_price": 2400.0},
                ]
            },
            {
                "id": "ord-1010", "customer_id": "cust-005", "status": "Pending", "shipping_city": "San Francisco",
                "days_ago": 2,
                "items": [
                    {"product_id": "prod-007", "quantity": 6, "unit_price": 450.0},
                    {"product_id": "prod-006", "quantity": 15, "unit_price": 120.0},
                ]
            },
        ]

        for o_spec in orders_spec:
            order_date = now - timedelta(days=o_spec["days_ago"])
            total_amount = sum(item["quantity"] * item["unit_price"] for item in o_spec["items"])
            order = Order(
                id=o_spec["id"],
                customer_id=o_spec["customer_id"],
                order_date=order_date,
                status=o_spec["status"],
                total_amount=total_amount,
                shipping_city=o_spec["shipping_city"],
            )
            db.add(order)

            for i, itm in enumerate(o_spec["items"]):
                order_item = OrderItem(
                    id=f"{o_spec['id']}-item-{i+1}",
                    order_id=o_spec["id"],
                    product_id=itm["product_id"],
                    quantity=itm["quantity"],
                    unit_price=itm["unit_price"],
                    total_price=itm["quantity"] * itm["unit_price"],
                )
                db.add(order_item)

        db.commit()
        print(f"Successfully seeded {len(customers_data)} customers, {len(products_data)} products, and {len(orders_spec)} orders.")

    except Exception as e:
        print(f"Error seeding business data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    seed_business_data(reset=reset_flag)
