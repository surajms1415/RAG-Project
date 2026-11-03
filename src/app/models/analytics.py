from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Date,
    ForeignKey,
    Numeric,
)
from sqlalchemy.orm import relationship
from src.app.core.database import Base
from src.app.models.base import TimeStampedModel, generate_uuid, utc_now


class Customer(TimeStampedModel):
    """Customer entity representing enterprise and retail clients."""

    __tablename__ = "customers"

    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    segment = Column(String(50), nullable=False, index=True)  # Enterprise, SMB, Consumer
    country = Column(String(100), nullable=False, default="United States")
    city = Column(String(100), nullable=False)

    # Relationships
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")


class Product(TimeStampedModel):
    """Product catalog with unit pricing and inventory levels."""

    __tablename__ = "products"

    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)  # Software, Hardware, Services, Cloud
    unit_price = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    stock_quantity = Column(Integer, nullable=False, default=0)

    # Relationships
    order_items = relationship("OrderItem", back_populates="product")


class Order(TimeStampedModel):
    """Business sales order placed by a customer."""

    __tablename__ = "orders"

    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    order_date = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    status = Column(String(50), nullable=False, default="Completed", index=True)  # Completed, Pending, Cancelled, Shipped
    total_amount = Column(Float, nullable=False, default=0.0)
    shipping_city = Column(String(100), nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(TimeStampedModel):
    """Line item within a customer order representing specific product sale."""

    __tablename__ = "order_items"

    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
