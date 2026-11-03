from typing import Dict, List, Any
from sqlalchemy import inspect
from src.app.core.database import engine

APPROVED_ANALYTICS_TABLES = {"customers", "products", "orders", "order_items"}

SCHEMA_DOCUMENTATION = """
TABLE: customers
Description: Client organizations and customer profiles.
Columns:
  - id (VARCHAR(36), PRIMARY KEY): Unique customer identifier (e.g. 'cust-001')
  - name (VARCHAR(255)): Company or individual name
  - email (VARCHAR(255)): Contact email address
  - segment (VARCHAR(50)): Customer segment: 'Enterprise', 'SMB', or 'Consumer'
  - country (VARCHAR(100)): Country of location
  - city (VARCHAR(100)): City of location
  - created_at (TIMESTAMP): Registration date

TABLE: products
Description: Catalog of products and services sold.
Columns:
  - id (VARCHAR(36), PRIMARY KEY): Product identifier (e.g. 'prod-001')
  - name (VARCHAR(255)): Product or service name
  - category (VARCHAR(100)): Category: 'Software', 'Hardware', 'Services', or 'Cloud'
  - unit_price (FLOAT): Selling price per unit in USD
  - cost (FLOAT): Cost of goods sold per unit in USD
  - stock_quantity (INTEGER): Available inventory quantity
  - created_at (TIMESTAMP): Creation date

TABLE: orders
Description: Sales orders placed by customers.
Columns:
  - id (VARCHAR(36), PRIMARY KEY): Order identifier (e.g. 'ord-1001')
  - customer_id (VARCHAR(36), FOREIGN KEY -> customers.id): Ordering customer
  - order_date (TIMESTAMP): Timestamp when order was placed
  - status (VARCHAR(50)): Order fulfillment status: 'Completed', 'Pending', 'Cancelled'
  - total_amount (FLOAT): Total order dollar amount in USD
  - shipping_city (VARCHAR(100)): Destination shipping city
  - created_at (TIMESTAMP): Order record timestamp

TABLE: order_items
Description: Line items belonging to an order specifying quantity and product.
Columns:
  - id (VARCHAR(36), PRIMARY KEY): Order item identifier (e.g. 'ord-1001-item-1')
  - order_id (VARCHAR(36), FOREIGN KEY -> orders.id): Associated order
  - product_id (VARCHAR(36), FOREIGN KEY -> products.id): Ordered product
  - quantity (INTEGER): Quantity purchased
  - unit_price (FLOAT): Price per unit at purchase time
  - total_price (FLOAT): Line total (quantity * unit_price)
  - created_at (TIMESTAMP): Item record timestamp
"""


def get_analytics_schema_context() -> str:
    """Returns the schema description used for LLM SQL generation prompts."""
    dialect_name = engine.dialect.name
    return f"DATABASE DIALECT: {dialect_name.upper()}\n\nAPPROVED TABLES & SCHEMA:\n{SCHEMA_DOCUMENTATION}"


def get_approved_tables() -> List[str]:
    """Returns list of approved analytics tables."""
    return sorted(list(APPROVED_ANALYTICS_TABLES))
