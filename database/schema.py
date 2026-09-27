from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    create_engine
)

from sqlalchemy.orm import declarative_base

from database.db import DATABASE_URL


Base = declarative_base()


# -------------------------
# PRODUCTS
# -------------------------

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    sku = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    variant = Column(String, nullable=False)
    price = Column(Float, nullable=False)


# -------------------------
# CUSTOMERS
# -------------------------

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String)
    city = Column(String)
    state = Column(String)


# -------------------------
# WAREHOUSES
# -------------------------

class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    location = Column(String, nullable=False)


# -------------------------
# INVENTORY
# -------------------------

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True)

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    warehouse_id = Column(
        Integer,
        ForeignKey("warehouses.id"),
        nullable=False
    )

    system_stock = Column(Integer, nullable=False)
    physical_stock = Column(Integer, nullable=False)
    reserved_stock = Column(Integer, default=0)


# -------------------------
# ORDERS
# -------------------------

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False
    )

    warehouse_id = Column(
        Integer,
        ForeignKey("warehouses.id"),
        nullable=False
    )

    channel = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    status = Column(String, nullable=False)

    created_at = Column(DateTime, nullable=False)
    deadline = Column(DateTime, nullable=False)


# -------------------------
# ORDER ITEMS
# -------------------------

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    quantity = Column(Integer, nullable=False)

    # Used for our simple mismatch demonstration
    picked_product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=True
    )

    picked_variant = Column(String, nullable=True)


# -------------------------
# SHIPMENTS
# -------------------------

class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True)

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False
    )

    courier = Column(String, nullable=False)
    tracking_number = Column(String, nullable=False)
    status = Column(String, nullable=False)
    pickup_time = Column(DateTime, nullable=False)


# -------------------------
# ISSUES
# -------------------------

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True)

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=True
    )

    type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)


# -------------------------
# CREATE DATABASE
# -------------------------

def create_database():
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

    Base.metadata.create_all(engine)

    print("Database created successfully.")


if __name__ == "__main__":
    create_database()