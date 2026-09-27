import random
import uuid
from datetime import datetime, timedelta

from faker import Faker
from sqlalchemy.orm import sessionmaker

from database.db import engine
from database.schema import (
    Product,
    Customer,
    Warehouse,
    Inventory,
    Order,
    OrderItem,
    Shipment,
    Issue,
)


# ============================================================
# CONFIGURATION
# ============================================================

fake = Faker("en_IN")

PRODUCT_COUNT = 2_000
CUSTOMER_COUNT = 10_000
ORDER_COUNT = 30_000

BATCH_SIZE = 1_000

random.seed(42)
Faker.seed(42)


# ============================================================
# CONSTANTS
# ============================================================

CATEGORIES = [
    "Electronics",
    "Clothing",
    "Footwear",
    "Home & Kitchen",
    "Beauty",
    "Sports",
    "Accessories",
    "Books",
]

BRANDS = [
    "Nike",
    "Adidas",
    "Samsung",
    "Apple",
    "Puma",
    "Sony",
    "Philips",
    "Boat",
    "OnePlus",
    "Lenovo",
    "HP",
    "Dell",
]

CHANNELS = [
    "Amazon",
    "Flipkart",
    "Shopify",
    "Website",
]

PRIORITIES = [
    "NORMAL",
    "HIGH",
    "URGENT",
]

STATUSES = [
    "RECEIVED",
    "PROCESSING",
    "PICKING",
    "PACKED",
    "STAGED",
    "SHIPPED",
    "DELIVERED",
]

COURIERS = [
    "BlueDart",
    "Delhivery",
    "DTDC",
    "Ecom Express",
]

ISSUE_TYPES = [
    "INVENTORY_SHORTAGE",
    "INVENTORY_MISMATCH",
    "PICKING_MISMATCH",
    "PICKING_DELAY",
    "PACKING_DELAY",
    "COURIER_DELAY",
]

SEVERITIES = [
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
]


# ============================================================
# DATABASE SESSION
# ============================================================

Session = sessionmaker(bind=engine)


# ============================================================
# CLEAR OLD DATA
# ============================================================

def clear_database(session):

    print("Clearing existing data...")

    session.query(Issue).delete()
    session.query(Shipment).delete()
    session.query(OrderItem).delete()
    session.query(Order).delete()
    session.query(Inventory).delete()
    session.query(Product).delete()
    session.query(Customer).delete()
    session.query(Warehouse).delete()

    session.commit()

    print("Old data cleared.")


# ============================================================
# PRODUCTS
# ============================================================

def generate_products(session):

    print(f"Generating {PRODUCT_COUNT:,} products...")

    products = []

    product_names = [
        "Air Max Running Shoe",
        "Classic Sneakers",
        "Wireless Headphones",
        "Bluetooth Speaker",
        "Smart Watch",
        "Cotton T-Shirt",
        "Denim Jeans",
        "Laptop Backpack",
        "Travel Backpack",
        "Coffee Maker",
        "Electric Kettle",
        "Yoga Mat",
        "Football",
        "Cricket Bat",
        "Water Bottle",
        "Desk Lamp",
        "Keyboard",
        "Wireless Mouse",
        "Power Bank",
        "Phone Case",
    ]

    variants = [
        "Black / S",
        "Black / M",
        "Black / L",
        "Black / XL",
        "White / S",
        "White / M",
        "White / L",
        "White / XL",
        "Blue / M",
        "Blue / L",
        "Red / M",
        "Standard",
        "128GB",
        "256GB",
    ]

    for i in range(1, PRODUCT_COUNT + 1):

        product = Product(
            sku=f"SKU-{i:06d}",
            name=random.choice(product_names),
            category=random.choice(CATEGORIES),
            brand=random.choice(BRANDS),
            variant=random.choice(variants),
            price=round(random.uniform(199, 49999), 2),
        )

        products.append(product)

        if len(products) >= BATCH_SIZE:
            session.bulk_save_objects(products)
            session.commit()
            products.clear()

            print(f"  Products: {i:,}/{PRODUCT_COUNT:,}")

    if products:
        session.bulk_save_objects(products)
        session.commit()

    print("Products completed.")


# ============================================================
# CUSTOMERS
# ============================================================

def generate_customers(session):

    print(f"Generating {CUSTOMER_COUNT:,} customers...")

    customers = []

    for i in range(1, CUSTOMER_COUNT + 1):

        customer = Customer(
            name=fake.name(),
            email=fake.unique.email(),
            phone=fake.phone_number(),
            city=fake.city(),
            state=fake.state(),
        )

        customers.append(customer)

        if len(customers) >= BATCH_SIZE:
            session.bulk_save_objects(customers)
            session.commit()
            customers.clear()

            print(f"  Customers: {i:,}/{CUSTOMER_COUNT:,}")

    if customers:
        session.bulk_save_objects(customers)
        session.commit()

    print("Customers completed.")


# ============================================================
# WAREHOUSES
# ============================================================

def generate_warehouses(session):

    print("Creating warehouses...")

    warehouses = [
        Warehouse(
            name="Main Warehouse",
            type="MAIN",
            location="Chennai",
        ),
        Warehouse(
            name="Backup Warehouse",
            type="BACKUP",
            location="Chennai",
        ),
    ]

    session.add_all(warehouses)
    session.commit()

    print("Warehouses created.")


# ============================================================
# INVENTORY
# ============================================================

def generate_inventory(session):

    print("Generating inventory...")

    products = session.query(Product).all()
    warehouses = session.query(Warehouse).all()

    inventory = []

    for product in products:

        # Main warehouse
        main_stock = random.randint(0, 100)

        # Backup warehouse
        backup_stock = random.randint(0, 150)

        # Deliberately create some physical mismatches
        if random.random() < 0.05:
            physical_stock = max(
                0,
                main_stock - random.randint(1, 10)
            )
        else:
            physical_stock = main_stock

        reserved_stock = random.randint(
            0,
            min(main_stock, 20)
        )

        inventory.append(
            Inventory(
                product_id=product.id,
                warehouse_id=warehouses[0].id,
                system_stock=main_stock,
                physical_stock=physical_stock,
                reserved_stock=reserved_stock,
            )
        )

        inventory.append(
            Inventory(
                product_id=product.id,
                warehouse_id=warehouses[1].id,
                system_stock=backup_stock,
                physical_stock=backup_stock,
                reserved_stock=0,
            )
        )

    session.bulk_save_objects(inventory)
    session.commit()

    print(f"Inventory records: {len(inventory):,}")


# ============================================================
# ORDERS
# ============================================================

def generate_orders(session):

    print(f"Generating {ORDER_COUNT:,} orders...")

    customers = session.query(Customer).all()
    warehouses = session.query(Warehouse).all()

    orders = []

    now = datetime.now()

    for i in range(1, ORDER_COUNT + 1):

        created_at = now - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        priority = random.choices(
            PRIORITIES,
            weights=[80, 15, 5],
            k=1,
        )[0]

        # Urgent orders get tighter deadlines
        if priority == "URGENT":
            deadline = now + timedelta(
                minutes=random.randint(-60, 180)
            )

        elif priority == "HIGH":
            deadline = now + timedelta(
                hours=random.randint(-2, 8)
            )

        else:
            deadline = now + timedelta(
                hours=random.randint(-6, 48)
            )

        status = random.choices(
            STATUSES,
            weights=[
                5,
                8,
                12,
                12,
                8,
                20,
                35,
            ],
            k=1,
        )[0]

        orders.append(
            Order(
                customer_id=random.choice(customers).id,
                warehouse_id=warehouses[0].id,
                channel=random.choice(CHANNELS),
                priority=priority,
                status=status,
                created_at=created_at,
                deadline=deadline,
            )
        )

        if len(orders) >= BATCH_SIZE:
            session.bulk_save_objects(orders)
            session.commit()
            orders.clear()

            print(f"  Orders: {i:,}/{ORDER_COUNT:,}")

    if orders:
        session.bulk_save_objects(orders)
        session.commit()

    print("Orders completed.")


# ============================================================
# ORDER ITEMS
# ============================================================

def generate_order_items(session):

    print("Generating order items...")

    orders = session.query(Order).all()
    products = session.query(Product).all()

    items = []

    for order_index, order in enumerate(orders, start=1):

        item_count = random.randint(1, 4)

        selected_products = random.sample(
            products,
            item_count
        )

        for product in selected_products:

            quantity = random.randint(1, 3)

            # Normally picked product = expected product
            picked_product_id = product.id
            picked_variant = product.variant

            # Deliberately create a few mismatches
            if random.random() < 0.01:

                wrong_product = random.choice(products)

                picked_product_id = wrong_product.id
                picked_variant = wrong_product.variant

            items.append(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    picked_product_id=picked_product_id,
                    picked_variant=picked_variant,
                )
            )

        if len(items) >= BATCH_SIZE:

            session.bulk_save_objects(items)
            session.commit()
            items.clear()

        if order_index % 5000 == 0:
            print(
                f"  Order items processed: "
                f"{order_index:,}/{len(orders):,}"
            )

    if items:
        session.bulk_save_objects(items)
        session.commit()

    count = session.query(OrderItem).count()

    print(f"Order items completed: {count:,}")


# ============================================================
# SHIPMENTS
# ============================================================

def generate_shipments(session):

    print("Generating shipments...")

    orders = session.query(Order).all()

    shipments = []

    for order in orders:

        pickup_time = order.deadline + timedelta(
            hours=random.randint(1, 4)
        )

        shipment_status = random.choices(
            [
                "READY",
                "STAGED",
                "PICKED_UP",
                "IN_TRANSIT",
                "DELIVERED",
                "PICKUP_MISSED",
            ],
            weights=[
                8,
                10,
                12,
                20,
                45,
                5,
            ],
            k=1,
        )[0]

        shipments.append(
            Shipment(
                order_id=order.id,
                courier=random.choice(COURIERS),
                tracking_number=f"TRK-{uuid.uuid4().hex[:10].upper()}",
                status=shipment_status,
                pickup_time=pickup_time,
            )
        )

        if len(shipments) >= BATCH_SIZE:

            session.bulk_save_objects(shipments)
            session.commit()
            shipments.clear()

    if shipments:
        session.bulk_save_objects(shipments)
        session.commit()

    print("Shipments completed.")


# ============================================================
# ISSUES
# ============================================================

def generate_issues(session):

    print("Generating issues...")

    orders = session.query(Order).all()

    issues = []

    for _ in range(2000):

        issue_type = random.choice(ISSUE_TYPES)

        if issue_type in [
            "INVENTORY_MISMATCH",
            "PICKING_MISMATCH",
        ]:
            severity = random.choice(
                ["HIGH", "CRITICAL"]
            )

        else:
            severity = random.choice(SEVERITIES)

        status = random.choices(
            [
                "OPEN",
                "IN_PROGRESS",
                "RESOLVED",
            ],
            weights=[20, 20, 60],
            k=1,
        )[0]

        descriptions = {
            "INVENTORY_SHORTAGE":
                "Required stock is not available in the main warehouse.",

            "INVENTORY_MISMATCH":
                "System inventory differs from physical warehouse count.",

            "PICKING_MISMATCH":
                "Picked product or variant does not match the order.",

            "PICKING_DELAY":
                "Order has been waiting in the picking queue.",

            "PACKING_DELAY":
                "Order has been waiting for packing.",

            "COURIER_DELAY":
                "Courier pickup has been delayed.",
        }

        issues.append(
            Issue(
                order_id=random.choice(orders).id,
                type=issue_type,
                severity=severity,
                description=descriptions[issue_type],
                status=status,
                created_at=datetime.now()
                - timedelta(
                    hours=random.randint(0, 72)
                ),
            )
        )

    session.bulk_save_objects(issues)
    session.commit()

    print(f"Issues completed: {len(issues):,}")


# ============================================================
# GUARANTEED DEMO SCENARIOS
# ============================================================

def create_demo_scenarios(session):

    print("Creating demo scenarios...")

    products = session.query(Product).limit(10).all()
    customer = session.query(Customer).first()
    main_warehouse = (
        session.query(Warehouse)
        .filter_by(type="MAIN")
        .first()
    )

    now = datetime.now()

    # --------------------------------------------------------
    # DEMO 1: URGENT ORDER
    # --------------------------------------------------------

    urgent_order = Order(
        customer_id=customer.id,
        warehouse_id=main_warehouse.id,
        channel="Website",
        priority="URGENT",
        status="PICKING",
        created_at=now - timedelta(hours=1),
        deadline=now + timedelta(minutes=20),
    )

    session.add(urgent_order)
    session.flush()

    session.add(
        OrderItem(
            order_id=urgent_order.id,
            product_id=products[0].id,
            quantity=1,
            picked_product_id=products[0].id,
            picked_variant=products[0].variant,
        )
    )

    # --------------------------------------------------------
    # DEMO 2: PRODUCT MISMATCH
    # --------------------------------------------------------

    mismatch_order = Order(
        customer_id=customer.id,
        warehouse_id=main_warehouse.id,
        channel="Amazon",
        priority="HIGH",
        status="PICKING",
        created_at=now - timedelta(hours=2),
        deadline=now + timedelta(hours=1),
    )

    session.add(mismatch_order)
    session.flush()

    session.add(
        OrderItem(
            order_id=mismatch_order.id,
            product_id=products[1].id,
            quantity=1,

            # WRONG PRODUCT DELIBERATELY
            picked_product_id=products[2].id,
            picked_variant=products[2].variant,
        )
    )

    # --------------------------------------------------------
    # DEMO 3: DELAYED ORDER
    # --------------------------------------------------------

    delayed_order = Order(
        customer_id=customer.id,
        warehouse_id=main_warehouse.id,
        channel="Flipkart",
        priority="HIGH",
        status="PROCESSING",
        created_at=now - timedelta(hours=8),
        deadline=now - timedelta(minutes=30),
    )

    session.add(delayed_order)
    session.flush()

    session.add(
        OrderItem(
            order_id=delayed_order.id,
            product_id=products[3].id,
            quantity=2,
            picked_product_id=products[3].id,
            picked_variant=products[3].variant,
        )
    )

    # --------------------------------------------------------
    # DEMO 4: INVENTORY MISMATCH
    # --------------------------------------------------------

    inventory_record = (
        session.query(Inventory)
        .filter(
            Inventory.product_id == products[4].id,
            Inventory.warehouse_id == main_warehouse.id,
        )
        .first()
    )

    if inventory_record:

        inventory_record.system_stock = 25
        inventory_record.physical_stock = 18
        inventory_record.reserved_stock = 5

    session.commit()

    print("Demo scenarios created.")


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("XYZ FULFILLMENT HUB - MOCK DATA GENERATOR")
    print("=" * 60)
    print()

    session = Session()

    try:

        clear_database(session)

        generate_products(session)

        generate_customers(session)

        generate_warehouses(session)

        generate_inventory(session)

        generate_orders(session)

        generate_order_items(session)

        generate_shipments(session)

        generate_issues(session)

        create_demo_scenarios(session)

        print()
        print("=" * 60)
        print("DATA GENERATION COMPLETE")
        print("=" * 60)
        print()

        print(
            f"Products:    {session.query(Product).count():,}"
        )

        print(
            f"Customers:   {session.query(Customer).count():,}"
        )

        print(
            f"Orders:      {session.query(Order).count():,}"
        )

        print(
            f"Order Items: {session.query(OrderItem).count():,}"
        )

        print(
            f"Inventory:   {session.query(Inventory).count():,}"
        )

        print(
            f"Shipments:   {session.query(Shipment).count():,}"
        )

        print(
            f"Issues:      {session.query(Issue).count():,}"
        )

        print()
        print("Database ready for Streamlit.")
        print()

    except Exception as e:

        session.rollback()

        print()
        print("ERROR:")
        print(e)
        print()

        raise

    finally:

        session.close()


if __name__ == "__main__":
    main()
    