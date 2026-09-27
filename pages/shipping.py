import streamlit as st
import pandas as pd
from sqlalchemy import text

from database.db import engine


def get_dataframe(query, params=None):
    with engine.connect() as conn:
        return pd.read_sql(
            text(query),
            conn,
            params=params or {}
        )


def execute_query(query, params=None):
    with engine.begin() as conn:
        conn.execute(
            text(query),
            params or {}
        )


# =========================================================
# PAGE HEADER
# =========================================================

st.title("🚚 Shipping")
st.caption(
    "Track packed orders, staging, courier pickup, and delivery."
)


# =========================================================
# KPI SUMMARY
# =========================================================

packed = get_dataframe("""
    SELECT COUNT(*)
    FROM orders
    WHERE status = 'PACKED'
""").iloc[0, 0]

ready = get_dataframe("""
    SELECT COUNT(*)
    FROM shipments
    WHERE status = 'READY'
""").iloc[0, 0]

staged = get_dataframe("""
    SELECT COUNT(*)
    FROM shipments
    WHERE status = 'STAGED'
""").iloc[0, 0]

picked_up = get_dataframe("""
    SELECT COUNT(*)
    FROM shipments
    WHERE status = 'PICKED_UP'
""").iloc[0, 0]

missed_pickups = get_dataframe("""
    SELECT COUNT(*)
    FROM shipments
    WHERE status = 'PICKUP_MISSED'
""").iloc[0, 0]


c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Packed Orders", f"{int(packed):,}")
c2.metric("Ready", f"{int(ready):,}")
c3.metric("Staged", f"{int(staged):,}")
c4.metric("Picked Up", f"{int(picked_up):,}")
c5.metric("⚠️ Missed", f"{int(missed_pickups):,}")


st.divider()


# =========================================================
# FILTERS
# =========================================================

col1, col2, col3 = st.columns(3)

with col1:

    status_filter = st.selectbox(
        "Shipment Status",
        [
            "All",
            "READY",
            "STAGED",
            "PICKED_UP",
            "IN_TRANSIT",
            "DELIVERED",
            "PICKUP_MISSED"
        ]
    )


# Get courier list first
couriers_df = get_dataframe("""
    SELECT DISTINCT courier
    FROM shipments
    WHERE courier IS NOT NULL
    ORDER BY courier
""")

couriers = ["All"] + couriers_df["courier"].tolist()


with col2:

    courier_filter = st.selectbox(
        "Courier",
        couriers
    )


with col3:

    search = st.text_input(
        "Search Order / Tracking",
        placeholder="Order ID or tracking number..."
    )


# =========================================================
# BUILD FILTER
# =========================================================

conditions = []
params = {}


if status_filter != "All":

    conditions.append(
        "s.status = :status"
    )

    params["status"] = status_filter


if courier_filter != "All":

    conditions.append(
        "s.courier = :courier"
    )

    params["courier"] = courier_filter


if search:

    conditions.append("""
        (
            CAST(o.id AS TEXT) LIKE :search
            OR s.tracking_number LIKE :search
        )
    """)

    params["search"] = f"%{search}%"


where_clause = ""

if conditions:

    where_clause = "WHERE " + " AND ".join(conditions)


# =========================================================
# SHIPMENT QUERY
# =========================================================

query = f"""
SELECT

    s.id AS shipment_id,

    o.id AS order_id,

    o.priority,

    o.status AS order_status,

    s.courier,

    s.tracking_number,

    s.status AS shipment_status,

    s.pickup_time,

    CASE

        WHEN s.status = 'PICKUP_MISSED'
            THEN 'Action Required'

        WHEN s.status = 'READY'
            THEN 'Ready for Staging'

        WHEN s.status = 'STAGED'
            THEN 'Waiting for Pickup'

        WHEN s.status = 'PICKED_UP'
            THEN 'Picked Up'

        WHEN s.status = 'IN_TRANSIT'
            THEN 'In Transit'

        WHEN s.status = 'DELIVERED'
            THEN 'Complete'

        ELSE 'Pending'

    END AS action_status

FROM shipments s

JOIN orders o
    ON o.id = s.order_id

{where_clause}

ORDER BY

    CASE

        WHEN s.status = 'PICKUP_MISSED'
            THEN 1

        WHEN o.priority = 'URGENT'
            THEN 2

        WHEN o.priority = 'HIGH'
            THEN 3

        WHEN s.status = 'READY'
            THEN 4

        WHEN s.status = 'STAGED'
            THEN 5

        ELSE 6

    END,

    s.pickup_time

LIMIT 300
"""


shipments_df = get_dataframe(
    query,
    params
)


# =========================================================
# SHIPMENT TABLE
# =========================================================

st.subheader("Shipment Queue")


if shipments_df.empty:

    st.info(
        "No shipments match the selected filters."
    )

else:

    display_df = shipments_df[
        [
            "order_id",
            "priority",
            "courier",
            "tracking_number",
            "shipment_status",
            "pickup_time",
            "action_status"
        ]
    ].copy()

    display_df.columns = [
        "Order ID",
        "Priority",
        "Courier",
        "Tracking Number",
        "Shipment Status",
        "Pickup Time",
        "Action"
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# SELECT SHIPMENT
# =========================================================

if not shipments_df.empty:

    st.divider()

    st.subheader("📦 Shipment Details")


    shipment_options = shipments_df[
        "shipment_id"
    ].tolist()

    selected_shipment = st.selectbox(
        "Select shipment",
        shipment_options
    )

    shipment = shipments_df[
        shipments_df["shipment_id"] == selected_shipment
    ].iloc[0]

    # =====================================================
    # DETAILS
    # =====================================================

    d1, d2, d3, d4 = st.columns(4)


    d1.metric(
        "Order",
        f"#{int(shipment['order_id'])}"
    )


    d2.metric(
        "Priority",
        shipment["priority"]
    )


    d3.metric(
        "Courier",
        shipment["courier"]
    )


    d4.metric(
        "Status",
        shipment["shipment_status"]
    )


    st.write(
        f"**Tracking:** `{shipment['tracking_number']}`"
    )


    if pd.notna(shipment["pickup_time"]):

        st.write(
            f"**Pickup Time:** {shipment['pickup_time']}"
        )


    # =====================================================
    # STATUS MESSAGE
    # =====================================================

    current_status = shipment["shipment_status"]


    if current_status == "PICKUP_MISSED":

        st.error(
            "🚨 Courier pickup was missed. "
            "This shipment needs attention."
        )


    elif current_status == "READY":

        st.info(
            "📦 Package is ready to be moved to staging."
        )


    elif current_status == "STAGED":

        st.warning(
            "📍 Package is staged and waiting for courier pickup."
        )


    elif current_status == "PICKED_UP":

        st.info(
            "🚚 Courier has picked up the package."
        )


    elif current_status == "IN_TRANSIT":

        st.info(
            "🚛 Package is currently in transit."
        )


    elif current_status == "DELIVERED":

        st.success(
            "✅ Package has been delivered."
        )


    # =====================================================
    # ACTIONS
    # =====================================================

    st.divider()

    st.subheader("Shipment Actions")


    # -----------------------------------------------------
    # READY → STAGED
    # -----------------------------------------------------

    if current_status == "READY":

        if st.button(
            "📍 Move to Staging",
            type="primary"
        ):

            execute_query(
                """
                UPDATE shipments
                SET status = 'STAGED'
                WHERE id = :shipment_id
                """,
                {
                    "shipment_id": int(
                        selected_shipment
                    )
                }
            )

            st.success(
                "Package moved to staging."
            )

            st.rerun()


    # -----------------------------------------------------
    # STAGED → PICKED_UP
    # -----------------------------------------------------

    elif current_status == "STAGED":

        if st.button(
            "🚚 Mark Courier Pickup",
            type="primary"
        ):

            execute_query(
                """
                UPDATE shipments
                SET status = 'PICKED_UP'
                WHERE id = :shipment_id
                """,
                {
                    "shipment_id": int(
                        selected_shipment
                    )
                }
            )

            st.success(
                "Courier pickup recorded."
            )

            st.rerun()


    # -----------------------------------------------------
    # PICKUP MISSED → PICKED_UP
    # -----------------------------------------------------

    elif current_status == "PICKUP_MISSED":

        st.warning(
            "The courier missed this pickup."
        )


        if st.button(
            "🚚 Record Successful Pickup",
            type="primary"
        ):

            execute_query(
                """
                UPDATE shipments
                SET status = 'PICKED_UP'
                WHERE id = :shipment_id
                """,
                {
                    "shipment_id": int(
                        selected_shipment
                    )
                }
            )

            st.success(
                "Pickup recorded successfully."
            )

            st.rerun()


    # -----------------------------------------------------
    # PICKED_UP → IN_TRANSIT
    # -----------------------------------------------------

    elif current_status == "PICKED_UP":

        if st.button(
            "🚛 Mark In Transit",
            type="primary"
        ):

            execute_query(
                """
                UPDATE shipments
                SET status = 'IN_TRANSIT'
                WHERE id = :shipment_id
                """,
                {
                    "shipment_id": int(
                        selected_shipment
                    )
                }
            )


            execute_query(
                """
                UPDATE orders
                SET status = 'SHIPPED'
                WHERE id = :order_id
                """,
                {
                    "order_id": int(
                        shipment["order_id"]
                    )
                }
            )


            st.success(
                "Shipment is now in transit."
            )

            st.rerun()


    # -----------------------------------------------------
    # IN_TRANSIT → DELIVERED
    # -----------------------------------------------------

    elif current_status == "IN_TRANSIT":

        if st.button(
            "✅ Mark Delivered",
            type="primary"
        ):

            execute_query(
                """
                UPDATE shipments
                SET status = 'DELIVERED'
                WHERE id = :shipment_id
                """,
                {
                    "shipment_id": int(
                        selected_shipment
                    )
                }
            )


            execute_query(
                """
                UPDATE orders
                SET status = 'DELIVERED'
                WHERE id = :order_id
                """,
                {
                    "order_id": int(
                        shipment["order_id"]
                    )
                }
            )


            st.success(
                "Shipment delivered successfully."
            )

            st.rerun()


    # -----------------------------------------------------
    # DELIVERED
    # -----------------------------------------------------

    elif current_status == "DELIVERED":

        st.success(
            "🎉 This fulfillment is complete."
        )