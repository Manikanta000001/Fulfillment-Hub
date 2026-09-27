import streamlit as st
import pandas as pd
from sqlalchemy import text

from database.db import engine


def get_dataframe(query, params=None):
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn, params=params or {})


def get_scalar(query, params=None):
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        return result.scalar()


st.title("📦 Inventory")
st.caption("Monitor stock availability and identify physical stock mismatches.")

# ---------------------------------------------------------
# FILTERS
# ---------------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    search = st.text_input(
        "Search product",
        placeholder="SKU or product name..."
    )

with col2:
    warehouse = st.selectbox(
        "Warehouse",
        ["All", "Main Warehouse", "Backup Warehouse"]
    )

with col3:
    stock_filter = st.selectbox(
        "Stock condition",
        [
            "All",
            "Low Stock",
            "Out of Stock",
            "Mismatch"
        ]
    )


# ---------------------------------------------------------
# BUILD FILTER
# ---------------------------------------------------------

conditions = []
params = {}

if search:
    conditions.append(
        "(p.sku LIKE :search OR p.name LIKE :search)"
    )
    params["search"] = f"%{search}%"

if warehouse != "All":
    conditions.append("w.name = :warehouse")
    params["warehouse"] = warehouse

if stock_filter == "Low Stock":
    conditions.append(
        "(i.system_stock - i.reserved_stock) > 0 "
        "AND (i.system_stock - i.reserved_stock) <= 10"
    )

elif stock_filter == "Out of Stock":
    conditions.append(
        "(i.system_stock - i.reserved_stock) <= 0"
    )

elif stock_filter == "Mismatch":
    conditions.append(
        "i.system_stock != i.physical_stock"
    )

where_clause = ""

if conditions:
    where_clause = "WHERE " + " AND ".join(conditions)


# ---------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------

total_products = get_scalar("""
    SELECT COUNT(*)
    FROM inventory
""")

low_stock = get_scalar("""
    SELECT COUNT(*)
    FROM inventory
    WHERE (system_stock - reserved_stock) > 0
      AND (system_stock - reserved_stock) <= 10
""")

out_of_stock = get_scalar("""
    SELECT COUNT(*)
    FROM inventory
    WHERE (system_stock - reserved_stock) <= 0
""")

mismatches = get_scalar("""
    SELECT COUNT(*)
    FROM inventory
    WHERE system_stock != physical_stock
""")

k1, k2, k3, k4 = st.columns(4)

k1.metric("Inventory Records", f"{total_products:,}")
k2.metric("Low Stock", f"{low_stock:,}")
k3.metric("Out of Stock", f"{out_of_stock:,}")
k4.metric("Stock Mismatches", f"{mismatches:,}")


st.divider()


# ---------------------------------------------------------
# INVENTORY TABLE
# ---------------------------------------------------------

query = f"""
SELECT
    i.id,
    p.sku,
    p.name AS product,
    p.category,
    w.name AS warehouse,
    i.system_stock,
    i.physical_stock,
    i.reserved_stock,
    (i.system_stock - i.reserved_stock) AS available_stock,

    CASE
        WHEN i.system_stock != i.physical_stock
            THEN 'Mismatch'
        WHEN (i.system_stock - i.reserved_stock) <= 0
            THEN 'Out of Stock'
        WHEN (i.system_stock - i.reserved_stock) <= 10
            THEN 'Low Stock'
        ELSE 'OK'
    END AS stock_status

FROM inventory i

JOIN products p
    ON p.id = i.product_id

JOIN warehouses w
    ON w.id = i.warehouse_id

{where_clause}

ORDER BY
    CASE
        WHEN i.system_stock != i.physical_stock THEN 1
        WHEN (i.system_stock - i.reserved_stock) <= 0 THEN 2
        WHEN (i.system_stock - i.reserved_stock) <= 10 THEN 3
        ELSE 4
    END,
    available_stock ASC

LIMIT 300
"""

df = get_dataframe(query, params)


st.subheader("Inventory Overview")

if df.empty:
    st.info("No inventory records match the selected filters.")
else:

    display_df = df[
        [
            "sku",
            "product",
            "category",
            "warehouse",
            "system_stock",
            "physical_stock",
            "reserved_stock",
            "available_stock",
            "stock_status"
        ]
    ].copy()

    display_df.columns = [
        "SKU",
        "Product",
        "Category",
        "Warehouse",
        "System Stock",
        "Physical Stock",
        "Reserved",
        "Available",
        "Status"
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# ---------------------------------------------------------
# SELECT PRODUCT
# ---------------------------------------------------------

if not df.empty:

    st.divider()

    st.subheader("🔎 Inventory Details")

    options = df["sku"].tolist()

    selected_sku = st.selectbox(
        "Select a product",
        options
    )

    selected = df[df["sku"] == selected_sku].iloc[0]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "System Stock",
        int(selected["system_stock"])
    )

    c2.metric(
        "Physical Stock",
        int(selected["physical_stock"])
    )

    c3.metric(
        "Reserved",
        int(selected["reserved_stock"])
    )

    c4.metric(
        "Available",
        int(selected["available_stock"])
    )

    # -----------------------------------------------------
    # MISMATCH WARNING
    # -----------------------------------------------------

    system_stock = int(selected["system_stock"])
    physical_stock = int(selected["physical_stock"])

    if system_stock != physical_stock:

        difference = physical_stock - system_stock

        st.error(
            f"⚠️ Inventory mismatch detected: "
            f"system shows {system_stock} units, "
            f"but physical stock shows {physical_stock} units."
        )

        if difference < 0:
            st.warning(
                f"Physical stock is {abs(difference)} units lower "
                f"than the system."
            )
        else:
            st.info(
                f"Physical stock is {difference} units higher "
                f"than the system."
            )

    elif int(selected["available_stock"]) <= 0:

        st.error(
            "🚨 This product currently has no available stock."
        )

    elif int(selected["available_stock"]) <= 10:

        st.warning(
            "⚠️ Low available stock. Consider checking replenishment."
        )

    else:

        st.success(
            "✅ Stock levels look healthy."
        )