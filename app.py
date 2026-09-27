import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import text

from database.db import engine


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="XYZ Fulfillment Hub",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #f7f8fa;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }

    .metric-title {
        font-size: 14px;
        color: #6b7280;
        margin-bottom: 5px;
    }

    .metric-value {
        font-size: 30px;
        font-weight: 700;
        color: #111827;
    }

    .section-title {
        font-size: 20px;
        font-weight: 700;
        color: #111827;
        margin-top: 20px;
        margin-bottom: 12px;
    }

    .alert-box {
        background-color: white;
        padding: 16px;
        border-radius: 10px;
        border-left: 5px solid #f59e0b;
        margin-bottom: 10px;
        border-top: 1px solid #e5e7eb;
        border-right: 1px solid #e5e7eb;
        border-bottom: 1px solid #e5e7eb;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_scalar(query, params=None):
    with engine.connect() as connection:
        result = connection.execute(
            text(query),
            params or {},
        )
        return result.scalar()


def get_dataframe(query, params=None):
    with engine.connect() as connection:
        return pd.read_sql(
            text(query),
            connection,
            params=params or {},
        )


# ============================================================
# METRICS
# ============================================================

def get_dashboard_metrics():

    total_orders = get_scalar(
        "SELECT COUNT(*) FROM orders"
    )

    priority_orders = get_scalar(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE priority IN ('HIGH', 'URGENT')
        AND status NOT IN ('SHIPPED', 'DELIVERED')
        """
    )

    delayed_orders = get_scalar(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE deadline < CURRENT_TIMESTAMP
        AND status NOT IN ('SHIPPED', 'DELIVERED')
        """
    )

    open_issues = get_scalar(
        """
        SELECT COUNT(*)
        FROM issues
        WHERE status != 'RESOLVED'
        """
    )

    inventory_mismatches = get_scalar(
        """
        SELECT COUNT(*)
        FROM inventory
        WHERE system_stock != physical_stock
        """
    )

    product_mismatches = get_scalar(
        """
        SELECT COUNT(*)
        FROM order_items
        WHERE product_id != picked_product_id
        """
    )

    return {
        "total_orders": total_orders,
        "priority_orders": priority_orders,
        "delayed_orders": delayed_orders,
        "open_issues": open_issues,
        "inventory_mismatches": inventory_mismatches,
        "product_mismatches": product_mismatches,
    }


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("📦 Fulfillment Hub")

    st.caption("XYZ Operations Dashboard")

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Orders",
            "Inventory",
            "Picking",
            "Shipping",
            "Issues",
        ],
    )

    st.divider()

    st.caption("Operations")
    st.caption("Order → Pick → Pack → Stage → Ship")


# ============================================================
# HEADER
# ============================================================

st.title("XYZ Fulfillment Hub")

st.caption(
    "Operational control center for order fulfillment, "
    "inventory and shipping."
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    metrics = get_dashboard_metrics()

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Today\'s Overview</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Total Orders",
            f"{metrics['total_orders']:,}",
        )

    with col2:
        st.metric(
            "Priority Orders",
            f"{metrics['priority_orders']:,}",
        )

    with col3:
        st.metric(
            "Delayed Orders",
            f"{metrics['delayed_orders']:,}",
        )

    with col4:
        st.metric(
            "Open Issues",
            f"{metrics['open_issues']:,}",
        )

    with col5:
        st.metric(
            "Mismatches",
            f"{metrics['product_mismatches'] + metrics['inventory_mismatches']:,}",
        )

    st.divider()

    # --------------------------------------------------------
    # ACTION REQUIRED
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">⚠️ Action Required</div>',
        unsafe_allow_html=True,
    )

    urgent_count = get_scalar(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE priority = 'URGENT'
        AND status NOT IN ('SHIPPED', 'DELIVERED')
        AND deadline <= datetime('now', '+2 hours')
        """
    )

    shortage_count = get_scalar(
        """
        SELECT COUNT(*)
        FROM order_items oi
        JOIN inventory i
            ON oi.product_id = i.product_id
        WHERE i.warehouse_id = 1
        AND (i.system_stock - i.reserved_stock) < oi.quantity
        """
    )

    open_mismatches = metrics["product_mismatches"]

    pickup_delays = get_scalar(
        """
        SELECT COUNT(*)
        FROM shipments
        WHERE status = 'PICKUP_MISSED'
        """
    )

    action_col1, action_col2 = st.columns(2)

    with action_col1:

        if urgent_count > 0:
            st.warning(
                f"🔴 **{urgent_count:,}** urgent orders "
                f"are approaching their deadline."
            )

        if shortage_count > 0:
            st.warning(
                f"🟠 **{shortage_count:,}** order items "
                f"may have insufficient stock."
            )

    with action_col2:

        if open_mismatches > 0:
            st.warning(
                f"⚠️ **{open_mismatches:,}** picking mismatches "
                f"need verification."
            )

        if pickup_delays > 0:
            st.error(
                f"🚚 **{pickup_delays:,}** courier pickups "
                f"were missed."
            )

    st.divider()

    # --------------------------------------------------------
    # ORDER PIPELINE
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Fulfillment Pipeline</div>',
        unsafe_allow_html=True,
    )

    pipeline = get_dataframe(
        """
        SELECT
            status,
            COUNT(*) AS orders
        FROM orders
        GROUP BY status
        ORDER BY orders DESC
        """
    )

    if not pipeline.empty:

        fig = px.bar(
            pipeline,
            x="status",
            y="orders",
            text="orders",
            title="Orders by Fulfillment Stage",
        )

        fig.update_layout(
            xaxis_title="Status",
            yaxis_title="Orders",
            showlegend=False,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    # --------------------------------------------------------
    # TWO CHARTS
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        channel_data = get_dataframe(
            """
            SELECT
                channel,
                COUNT(*) AS orders
            FROM orders
            GROUP BY channel
            ORDER BY orders DESC
            """
        )

        fig = px.pie(
            channel_data,
            names="channel",
            values="orders",
            title="Orders by Channel",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with col2:

        issue_data = get_dataframe(
            """
            SELECT
                type,
                COUNT(*) AS issues
            FROM issues
            GROUP BY type
            ORDER BY issues DESC
            """
        )

        fig = px.bar(
            issue_data,
            x="type",
            y="issues",
            title="Operational Issues",
        )

        fig.update_layout(
            xaxis_title="Issue Type",
            yaxis_title="Count",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    # --------------------------------------------------------
    # PRIORITY ORDERS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Priority Orders</div>',
        unsafe_allow_html=True,
    )

    priority_orders = get_dataframe(
        """
        SELECT
            id AS order_id,
            channel,
            priority,
            status,
            deadline
        FROM orders
        WHERE priority IN ('HIGH', 'URGENT')
        AND status NOT IN ('SHIPPED', 'DELIVERED')
        ORDER BY deadline
        LIMIT 15
        """
    )

    if not priority_orders.empty:

        st.dataframe(
            priority_orders,
            use_container_width=True,
            hide_index=True,
        )

elif page == "Orders":

    exec(
        open(
            "pages/orders.py",
            encoding="utf-8",
        ).read()
    )
elif page == "Inventory":
    exec(open("pages/inventory.py", encoding="utf-8").read())


elif page == "Picking":
    exec(open("pages/picking.py", encoding="utf-8").read())

elif page == "Shipping":
    exec(open("pages/shipping.py", encoding="utf-8").read())
    
elif page == "Issues":
    exec(open("pages/issues.py", encoding="utf-8").read())