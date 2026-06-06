"""My Orders page."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from api_client import get_my_orders, pay_order, cancel_order
from utils import require_auth, require_role, format_currency, status_badge

st.set_page_config(page_title="My Orders — CampusRent", page_icon="🛒", layout="wide")

require_auth()
require_role(["penyewa"])

st.title("🛒 My Orders")

with st.spinner("Loading orders..."):
    orders = get_my_orders(page=1, page_size=50)

if not orders:
    st.info("No orders yet. Browse the catalog to start renting!")
    st.stop()

for order in orders:
    with st.container(border=True):
        col_id, col_status, col_amount, col_date = st.columns([1, 2, 2, 2])
        with col_id:
            st.write(f"**#{order['id']}**")
        with col_status:
            st.write(status_badge(order["status"]))
        with col_amount:
            st.write(f"**{format_currency(order['total_amount'])}**")
        with col_date:
            st.caption(order["created_at"][:10])

        if order.get("items"):
            with st.expander(f"📦 {len(order['items'])} item(s)"):
                for item in order["items"]:
                    st.write(
                        f"Equipment `{item['equipment_id']}` | "
                        f"Qty: {item['quantity']} | "
                        f"{item['start_date']} → {item['end_date']} | "
                        f"{format_currency(item['subtotal'])}"
                    )

        col_a, col_b, col_c = st.columns(3)
        if order["status"] == "pending_payment":
            with col_a:
                if st.button("💳 Pay", key=f"pay_{order['id']}", use_container_width=True):
                    with st.spinner("Paying..."):
                        pay_order(order["id"], order["total_amount"])
                    st.rerun()
            with col_b:
                if st.button("❌ Cancel", key=f"cancel_{order['id']}", use_container_width=True):
                    with st.spinner("Cancelling..."):
                        cancel_order(order["id"])
                    st.rerun()
        elif order["status"] == "paid_escrow":
            with col_a:
                if st.button("❌ Cancel", key=f"cancel_{order['id']}", use_container_width=True):
                    with st.spinner("Cancelling..."):
                        cancel_order(order["id"])
                    st.rerun()
        elif order["status"] == "completed":
            with col_a:
                if st.button("⭐ Review", key=f"review_{order['id']}", use_container_width=True):
                    st.session_state["review_order_id"] = order["id"]
                    st.session_state["review_items"] = order.get("items", [])
                    st.switch_page("pages/10_Reviews.py")
