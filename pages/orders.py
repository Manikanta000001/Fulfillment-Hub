import streamlit as st
import pandas as pd
from sqlalchemy import text

from database.db import engine


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_dataframe(query, params=None):

    with engine.connect() as connection:

        return pd.read_sql(
            text(query),
            connection,
            params=params or {},
        )


def get_scalar(query, params=None):

    with engine.connect() as connection:

        return connection.execute(
            text(query),
            params or {},
        ).scalar()


# ============================================================
# PAGE HEADER
# ============================================================

st.title("📦 Orders")

st.caption(
    "Monitor orders, priorities, deadlines and fulfillment status."
)

st.divider()


# ============================================================
# FILTERS
# ============================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    search = st.text_input(
        "Search Order ID",
        placeholder="Example: 10452",
    )


with col2:

    status_filter = st.selectbox(
        "Status",
        [
            "ALL",
            "RECEIVED",
            "PROCESSING",
            "PICKING",
            "PACKED",
            "STAGED",
            "SHIPPED",
            "DELIVERED",
        ],
    )


with col3:

    priority_filter = st.selectbox(
        "Priority",
        [
            "ALL",
            "URGENT",
            "HIGH",
            "NORMAL",
        ],
    )


with col4:

    show_mismatch = st.checkbox(
        "Only mismatches"
    )


# ============================================================
# BUILD QUERY
# ============================================================

query = """
SELECT
    o.id AS order_id,
    o.channel,
    o.priority,
    o.status,
    o.created_at,
    o.deadline,

    CASE
        WHEN o.deadline < CURRENT_TIMESTAMP
        AND o.status NOT IN ('SHIPPED', 'DELIVERED')
        THEN 1
        ELSE 0
    END AS delayed,

    CASE
        WHEN EXISTS (
            SELECT 1
            FROM order_items oi
            WHERE oi.order_id = o.id
            AND oi.product_id != oi.picked_product_id
        )
        THEN 1
        ELSE 0
    END AS mismatch

FROM orders o
WHERE 1 = 1
"""

params = {}


# ============================================================
# APPLY FILTERS
# ============================================================

if search:

    query += """
    AND CAST(o.id AS TEXT) LIKE :search
    """

    params["search"] = f"%{search}%"


if status_filter != "ALL":

    query += """
    AND o.status = :status
    """

    params["status"] = status_filter


if priority_filter != "ALL":

    query += """
    AND o.priority = :priority
    """

    params["priority"] = priority_filter


if show_mismatch:

    query += """
    AND EXISTS (
        SELECT 1
        FROM order_items oi
        WHERE oi.order_id = o.id
        AND oi.product_id != oi.picked_product_id
    )
    """


query += """
ORDER BY
    CASE
        WHEN o.priority = 'URGENT' THEN 1
        WHEN o.priority = 'HIGH' THEN 2
        ELSE 3
    END,
    o.deadline
LIMIT 200
"""


orders = get_dataframe(
    query,
    params,
)


# ============================================================
# SUMMARY
# ============================================================

total = len(orders)

urgent = len(
    orders[
        orders["priority"] == "URGENT"
    ]
)

delayed = len(
    orders[
        orders["delayed"] == 1
    ]
)

mismatches = len(
    orders[
        orders["mismatch"] == 1
    ]
)


col1, col2, col3, col4 = st.columns(4)


with col1:
    st.metric(
        "Orders Found",
        f"{total:,}",
    )


with col2:
    st.metric(
        "Urgent",
        f"{urgent:,}",
    )


with col3:
    st.metric(
        "Delayed",
        f"{delayed:,}",
    )


with col4:
    st.metric(
        "Mismatches",
        f"{mismatches:,}",
    )


st.divider()


# ============================================================
# ORDER TABLE
# ============================================================

if orders.empty:

    st.info(
        "No orders match the selected filters."
    )

else:

    display_orders = orders.copy()

    display_orders["priority"] = (
        display_orders["priority"]
        .map(
            {
                "URGENT": "🔴 URGENT",
                "HIGH": "🟠 HIGH",
                "NORMAL": "🟢 NORMAL",
            }
        )
    )

    display_orders["status"] = (
        display_orders["status"]
        .str.replace("_", " ")
        .str.title()
    )

    display_orders["deadline"] = pd.to_datetime(
        display_orders["deadline"]
    ).dt.strftime(
        "%d %b %H:%M"
    )

    display_orders["delayed"] = (
        display_orders["delayed"]
        .map(
            {
                1: "🔴 Delayed",
                0: "✓",
            }
        )
    )

    display_orders["mismatch"] = (
        display_orders["mismatch"]
        .map(
            {
                1: "⚠️ Mismatch",
                0: "✓",
            }
        )
    )

    display_orders = display_orders[
        [
            "order_id",
            "channel",
            "priority",
            "status",
            "deadline",
            "delayed",
            "mismatch",
        ]
    ]

    display_orders.columns = [
        "Order ID",
        "Channel",
        "Priority",
        "Status",
        "Deadline",
        "Delay",
        "Check",
    ]

    st.dataframe(
        display_orders,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# SELECT ORDER
# ============================================================

st.divider()

st.subheader("Order Details")

order_ids = orders["order_id"].tolist()

if order_ids:

    selected_order = st.selectbox(
        "Select an order",
        order_ids,
    )

    # --------------------------------------------------------
    # ORDER INFORMATION
    # --------------------------------------------------------

    order = get_dataframe(
        """
        SELECT
            o.id AS order_id,
            o.channel,
            o.priority,
            o.status,
            o.created_at,
            o.deadline
        FROM orders o
        WHERE o.id = :order_id
        """,
        {
            "order_id": selected_order
        },
    )

    if not order.empty:

        order = order.iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Order",
                f"#{int(order['order_id'])}",
            )

        with col2:

            st.metric(
                "Channel",
                order["channel"],
            )

        with col3:

            st.metric(
                "Priority",
                order["priority"],
            )

        with col4:

            st.metric(
                "Status",
                order["status"],
            )

        # ----------------------------------------------------
        # DEADLINE
        # ----------------------------------------------------

        deadline = pd.to_datetime(
            order["deadline"]
        )

        now = pd.Timestamp.now()

        if (
            deadline < now
            and order["status"]
            not in ["SHIPPED", "DELIVERED"]
        ):

            st.error(
                f"🔴 Order deadline passed: "
                f"{deadline.strftime('%d %b %Y, %H:%M')}"
            )

        else:

            st.info(
                f"⏱ Deadline: "
                f"{deadline.strftime('%d %b %Y, %H:%M')}"
            )

        # ----------------------------------------------------
        # ITEMS
        # ----------------------------------------------------

        st.subheader("Order Items")

        items = get_dataframe(
            """
            SELECT
                oi.id,
                p.sku,
                p.name,
                p.variant AS expected_variant,
                oi.quantity,
                picked.sku AS picked_sku,
                oi.picked_variant

            FROM order_items oi

            JOIN products p
                ON oi.product_id = p.id

            LEFT JOIN products picked
                ON oi.picked_product_id = picked.id

            WHERE oi.order_id = :order_id
            """,
            {
                "order_id": selected_order
            },
        )

        if not items.empty:

            items["check"] = items.apply(
                lambda row:
                "⚠️ MISMATCH"
                if row["sku"] != row["picked_sku"]
                else "✓ MATCH",
                axis=1,
            )

            display_items = items[
                [
                    "sku",
                    "name",
                    "expected_variant",
                    "quantity",
                    "picked_sku",
                    "picked_variant",
                    "check",
                ]
            ].copy()

            display_items.columns = [
                "Expected SKU",
                "Product",
                "Expected Variant",
                "Qty",
                "Picked SKU",
                "Picked Variant",
                "Check",
            ]

            st.dataframe(
                display_items,
                use_container_width=True,
                hide_index=True,
            )

            # ------------------------------------------------
            # MISMATCH ALERT
            # ------------------------------------------------

            mismatch_items = items[
                items["sku"] != items["picked_sku"]
            ]

            if not mismatch_items.empty:

                st.warning(
                    "⚠️ One or more items do not match "
                    "the expected product."
                )

                for _, item in mismatch_items.iterrows():

                    st.error(
                        f"""
                        **Product mismatch detected**

                        Expected: `{item['sku']}` — "
                        f"{item['expected_variant']}`

                        Picked: `{item['picked_sku']}` — "
                        f"{item['picked_variant']}`
                        """
                    )

        # ----------------------------------------------------
        # FULFILLMENT TIMELINE
        # ----------------------------------------------------

        st.subheader("Fulfillment Progress")

        statuses = [
            "RECEIVED",
            "PROCESSING",
            "PICKING",
            "PACKED",
            "STAGED",
            "SHIPPED",
            "DELIVERED",
        ]

        current_status = order["status"]

        if current_status in statuses:

            current_index = statuses.index(
                current_status
            )

            timeline = []

            for index, status in enumerate(statuses):

                if index < current_index:

                    icon = "✓"

                elif index == current_index:

                    icon = "●"

                else:

                    icon = "○"

                timeline.append(
                    f"{icon} {status.title()}"
                )

            st.write(
                "  →  ".join(timeline)
            )
            