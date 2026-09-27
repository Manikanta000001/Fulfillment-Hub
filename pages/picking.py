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


st.title("🛒 Picking")
st.caption("Pick the correct products for each order before packing.")


# =========================================================
# PICKING ORDERS
# =========================================================

orders_query = """
SELECT
    o.id,
    o.priority,
    o.status,
    o.deadline,
    o.channel,

    CASE
        WHEN o.deadline < CURRENT_TIMESTAMP
            THEN 'Delayed'
        WHEN o.deadline <= datetime('now', '+2 hours')
            THEN 'Due Soon'
        ELSE 'On Track'
    END AS timing

FROM orders o

WHERE o.status = 'PICKING'

ORDER BY
    CASE
        WHEN o.priority = 'URGENT' THEN 1
        WHEN o.priority = 'HIGH' THEN 2
        ELSE 3
    END,
    o.deadline
LIMIT 200
"""

orders_df = get_dataframe(orders_query)


# =========================================================
# SUMMARY
# =========================================================

total_picking = len(orders_df)

urgent_count = len(
    orders_df[orders_df["priority"] == "URGENT"]
) if not orders_df.empty else 0

delayed_count = len(
    orders_df[orders_df["timing"] == "Delayed"]
) if not orders_df.empty else 0

due_soon_count = len(
    orders_df[orders_df["timing"] == "Due Soon"]
) if not orders_df.empty else 0


c1, c2, c3, c4 = st.columns(4)

c1.metric("Orders to Pick", total_picking)
c2.metric("Urgent", urgent_count)
c3.metric("Delayed", delayed_count)
c4.metric("Due Soon", due_soon_count)


st.divider()


# =========================================================
# ORDER SELECTION
# =========================================================

if orders_df.empty:

    st.success("🎉 No orders are currently waiting for picking.")

else:

    st.subheader("Orders Waiting for Picking")

    display_orders = orders_df[
        [
            "id",
            "priority",
            "channel",
            "deadline",
            "timing"
        ]
    ].copy()

    display_orders.columns = [
        "Order ID",
        "Priority",
        "Channel",
        "Deadline",
        "Timing"
    ]

    st.dataframe(
        display_orders,
        use_container_width=True,
        hide_index=True
    )

    order_ids = orders_df["id"].tolist()

    selected_order = st.selectbox(
        "Select an order to pick",
        order_ids
    )


    # =====================================================
    # ORDER DETAILS
    # =====================================================

    order = orders_df[
        orders_df["id"] == selected_order
    ].iloc[0]

    st.divider()

    st.subheader(
        f"Order #{selected_order}"
    )

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "Priority",
        order["priority"]
    )

    m2.metric(
        "Channel",
        order["channel"]
    )

    m3.metric(
        "Status",
        order["status"]
    )

    m4.metric(
        "Timing",
        order["timing"]
    )


    if order["timing"] == "Delayed":
        st.error(
            "🚨 This order is past its deadline."
        )

    elif order["timing"] == "Due Soon":
        st.warning(
            "⚠️ This order is approaching its deadline."
        )


    # =====================================================
    # ORDER ITEMS
    # =====================================================

    items_query = """
    SELECT
        oi.id AS item_id,

        p.id AS expected_product_id,
        p.sku AS expected_sku,
        p.name AS expected_product,
        p.variant AS expected_variant,

        oi.quantity,

        picked.id AS picked_product_id,
        picked.sku AS picked_sku,
        picked.name AS picked_product,
        oi.picked_variant,

        CASE
            WHEN oi.picked_product_id IS NULL
                THEN 'Not Picked'

            WHEN oi.picked_product_id != oi.product_id
                THEN 'Mismatch'

            WHEN oi.picked_variant IS NOT NULL
                 AND oi.picked_variant != p.variant
                THEN 'Mismatch'

            ELSE 'Correct'
        END AS pick_status

    FROM order_items oi

    JOIN products p
        ON p.id = oi.product_id

    LEFT JOIN products picked
        ON picked.id = oi.picked_product_id

    WHERE oi.order_id = :order_id

    ORDER BY oi.id
    """

    items_df = get_dataframe(
        items_query,
        {"order_id": int(selected_order)}
    )


    st.subheader("Items to Pick")


    # =====================================================
    # PICKING TABLE
    # =====================================================

    for _, item in items_df.iterrows():

        item_id = int(item["item_id"])

        st.markdown("---")

        col1, col2 = st.columns([1, 2])

        with col1:

            st.markdown(
                f"### {item['expected_sku']}"
            )

            st.write(
                f"**Expected:** {item['expected_product']}"
            )

            st.write(
                f"**Variant:** {item['expected_variant']}"
            )

            st.write(
                f"**Quantity:** {int(item['quantity'])}"
            )


        with col2:

            st.markdown("**Picking Check**")

            # ---------------------------------------------
            # Product selection
            # ---------------------------------------------

            product_options_query = """
            SELECT
                id,
                sku,
                name,
                variant
            FROM products
            ORDER BY sku
            LIMIT 2000
            """

            products_df = get_dataframe(
                product_options_query
            )

            product_labels = [
                f"{row.sku} | {row.name} | {row.variant}"
                for _, row in products_df.iterrows()
            ]

            expected_label = (
                f"{item['expected_sku']} | "
                f"{item['expected_product']} | "
                f"{item['expected_variant']}"
            )

            if expected_label in product_labels:
                default_index = product_labels.index(
                    expected_label
                )
            else:
                default_index = 0


            selected_label = st.selectbox(
                "Picked product",
                product_labels,
                index=default_index,
                key=f"product_{item_id}"
            )


            selected_product = products_df.iloc[
                product_labels.index(selected_label)
            ]


            # ---------------------------------------------
            # Picked variant
            # ---------------------------------------------

            picked_variant = st.text_input(
                "Picked variant",
                value=(
                    item["picked_variant"]
                    if pd.notna(item["picked_variant"])
                    else str(item["expected_variant"])
                ),
                key=f"variant_{item_id}"
            )


            # ---------------------------------------------
            # Check mismatch
            # ---------------------------------------------

            product_matches = (
                int(selected_product["id"])
                == int(item["expected_product_id"])
            )

            variant_matches = (
                picked_variant.strip().lower()
                == str(item["expected_variant"]).strip().lower()
            )


            if not product_matches or not variant_matches:

                st.error(
                    "⚠️ PICKING MISMATCH"
                )

                st.write(
                    f"Expected: "
                    f"**{item['expected_sku']} / "
                    f"{item['expected_variant']}**"
                )

                st.write(
                    f"Picked: "
                    f"**{selected_product['sku']} / "
                    f"{picked_variant}**"
                )

            else:

                st.success(
                    "✅ Correct product and variant"
                )


            # ---------------------------------------------
            # Save pick
            # ---------------------------------------------

            if st.button(
                "Save Pick",
                key=f"save_{item_id}"
            ):

                execute_query(
                    """
                    UPDATE order_items
                    SET
                        picked_product_id = :product_id,
                        picked_variant = :variant
                    WHERE id = :item_id
                    """,
                    {
                        "product_id": int(
                            selected_product["id"]
                        ),
                        "variant": picked_variant,
                        "item_id": item_id
                    }
                )

                st.success(
                    "Pick saved successfully."
                )

                st.rerun()


    # =====================================================
    # FINAL PICKING CHECK
    # =====================================================

    st.divider()

    st.subheader("Final Picking Check")


    remaining_query = """
    SELECT COUNT(*)
    FROM order_items oi
    WHERE oi.order_id = :order_id
      AND (
          oi.picked_product_id IS NULL
          OR oi.picked_product_id != oi.product_id
          OR (
              oi.picked_variant IS NOT NULL
              AND oi.picked_variant != (
                  SELECT variant
                  FROM products
                  WHERE id = oi.product_id
              )
          )
      )
    """

    remaining = get_dataframe(
        remaining_query,
        {"order_id": int(selected_order)}
    ).iloc[0, 0]


    if int(remaining) > 0:

        st.warning(
            f"⚠️ {int(remaining)} item(s) still need "
            "attention before this order can be completed."
        )

    else:

        st.success(
            "✅ All items match the expected products."
        )

        if st.button(
            "✅ Mark Picking Complete",
            type="primary"
        ):

            execute_query(
                """
                UPDATE orders
                SET status = 'PACKED'
                WHERE id = :order_id
                """,
                {
                    "order_id": int(selected_order)
                }
            )

            st.success(
                f"Order #{selected_order} moved to PACKED."
            )

            st.rerun()