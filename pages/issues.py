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

st.title("🚨 Issues")
st.caption(
    "Track operational problems that need attention."
)


# =========================================================
# KPI CARDS
# =========================================================

open_issues = get_dataframe("""
    SELECT COUNT(*)
    FROM issues
    WHERE status != 'RESOLVED'
""").iloc[0, 0]

critical_issues = get_dataframe("""
    SELECT COUNT(*)
    FROM issues
    WHERE severity = 'CRITICAL'
      AND status != 'RESOLVED'
""").iloc[0, 0]

high_issues = get_dataframe("""
    SELECT COUNT(*)
    FROM issues
    WHERE severity = 'HIGH'
      AND status != 'RESOLVED'
""").iloc[0, 0]

resolved_issues = get_dataframe("""
    SELECT COUNT(*)
    FROM issues
    WHERE status = 'RESOLVED'
""").iloc[0, 0]


c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Open Issues",
    f"{int(open_issues):,}"
)

c2.metric(
    "Critical",
    f"{int(critical_issues):,}"
)

c3.metric(
    "High",
    f"{int(high_issues):,}"
)

c4.metric(
    "Resolved",
    f"{int(resolved_issues):,}"
)


st.divider()


# =========================================================
# FILTERS
# =========================================================

col1, col2, col3 = st.columns(3)


with col1:

    status_filter = st.selectbox(
        "Status",
        [
            "All",
            "OPEN",
            "IN_PROGRESS",
            "RESOLVED"
        ]
    )


with col2:

    severity_filter = st.selectbox(
        "Severity",
        [
            "All",
            "CRITICAL",
            "HIGH",
            "MEDIUM",
            "LOW"
        ]
    )


with col3:

    type_filter = st.selectbox(
        "Issue Type",
        [
            "All",
            "INVENTORY_SHORTAGE",
            "INVENTORY_MISMATCH",
            "PICKING_MISMATCH",
            "PICKING_DELAY",
            "PACKING_DELAY",
            "COURIER_DELAY"
        ]
    )


# =========================================================
# BUILD FILTER
# =========================================================

conditions = []
params = {}


if status_filter != "All":

    conditions.append(
        "i.status = :status"
    )

    params["status"] = status_filter


if severity_filter != "All":

    conditions.append(
        "i.severity = :severity"
    )

    params["severity"] = severity_filter


if type_filter != "All":

    conditions.append(
        "i.type = :issue_type"
    )

    params["issue_type"] = type_filter


where_clause = ""

if conditions:

    where_clause = (
        "WHERE " + " AND ".join(conditions)
    )


# =========================================================
# ISSUE LIST
# =========================================================

query = f"""
SELECT

    i.id AS issue_id,

    i.order_id,

    i.type,

    i.severity,

    i.description,

    i.status,

    i.created_at

FROM issues i

{where_clause}

ORDER BY

    CASE
        WHEN i.status != 'RESOLVED'
             AND i.severity = 'CRITICAL'
            THEN 1

        WHEN i.status != 'RESOLVED'
             AND i.severity = 'HIGH'
            THEN 2

        WHEN i.status != 'RESOLVED'
             AND i.severity = 'MEDIUM'
            THEN 3

        ELSE 4
    END,

    i.created_at DESC

LIMIT 300
"""


issues_df = get_dataframe(
    query,
    params
)


# =========================================================
# TABLE
# =========================================================

st.subheader("Issue Queue")


if issues_df.empty:

    st.success(
        "✅ No issues match the selected filters."
    )

else:

    display_df = issues_df[
        [
            "issue_id",
            "order_id",
            "type",
            "severity",
            "description",
            "status",
            "created_at"
        ]
    ].copy()

    display_df.columns = [
        "Issue ID",
        "Order ID",
        "Type",
        "Severity",
        "Description",
        "Status",
        "Created At"
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# ISSUE DETAILS
# =========================================================

if not issues_df.empty:

    st.divider()

    st.subheader("🔎 Issue Details")

    issue_options = issues_df[
        "issue_id"
    ].tolist()


    selected_issue = st.selectbox(
        "Select an issue",
        issue_options
    )


    issue = issues_df[
        issues_df["issue_id"] == selected_issue
    ].iloc[0]


    # =====================================================
    # DETAILS
    # =====================================================

    d1, d2, d3, d4 = st.columns(4)


    d1.metric(
        "Issue ID",
        f"#{int(issue['issue_id'])}"
    )


    d2.metric(
        "Order",
        (
            f"#{int(issue['order_id'])}"
            if pd.notna(issue["order_id"])
            else "N/A"
        )
    )


    d3.metric(
        "Severity",
        issue["severity"]
    )


    d4.metric(
        "Status",
        issue["status"]
    )


    st.write(
        f"**Type:** {issue['type']}"
    )

    st.write(
        f"**Created:** {issue['created_at']}"
    )


    st.markdown("### Description")

    st.info(
        issue["description"]
    )


    # =====================================================
    # STATUS MESSAGE
    # =====================================================

    if issue["severity"] == "CRITICAL":

        st.error(
            "🚨 Critical issue requires immediate attention."
        )

    elif issue["severity"] == "HIGH":

        st.warning(
            "⚠️ High-priority issue requires attention."
        )


    # =====================================================
    # ACTIONS
    # =====================================================

    st.divider()

    st.subheader("Issue Actions")


    current_status = issue["status"]


    if current_status == "OPEN":

        if st.button(
            "🔄 Mark In Progress",
            type="primary"
        ):

            execute_query(
                """
                UPDATE issues
                SET status = 'IN_PROGRESS'
                WHERE id = :issue_id
                """,
                {
                    "issue_id": int(
                        selected_issue
                    )
                }
            )

            st.success(
                "Issue moved to In Progress."
            )

            st.rerun()


    elif current_status == "IN_PROGRESS":

        if st.button(
            "✅ Resolve Issue",
            type="primary"
        ):

            execute_query(
                """
                UPDATE issues
                SET status = 'RESOLVED'
                WHERE id = :issue_id
                """,
                {
                    "issue_id": int(
                        selected_issue
                    )
                }
            )

            st.success(
                "Issue resolved successfully."
            )

            st.rerun()


    else:

        st.success(
            "✅ This issue has already been resolved."
        )