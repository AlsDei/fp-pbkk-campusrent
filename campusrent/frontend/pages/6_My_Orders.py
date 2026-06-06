"""My Orders page — view order history, pay, cancel."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from api_client import get_my_orders, pay_order, cancel_order
from utils import require_auth, require_role, format_currency, status_badge
from styles import inject_global_styles

st.set_page_config(page_title="My Orders — CampusRent", page_icon="🛒", layout="wide")
inject_global_styles()

require_auth()
require_role(["penyewa"])

# ─── Header ───────────────────────────────────────────────────────────────────

st.markdown("""
<div style="background: linear-gradient(135deg, #ee4d2d 0%, #ff7043 100%); border-radius: 12px; padding: 24px 28px; margin-bottom: 20px;">
    <h2 style="color: white; margin: 0; font-weight: 700;">🛒 My Orders</h2>
    <p style="color: rgba(255,255,255,0.85); margin: 4px 0 0 0;">View your rental orders, make payments, or cancel</p>
</div>
""", unsafe_allow_html=True)

# ─── Order History ────────────────────────────────────────────────────────────

with st.spinner("Loading orders..."):
    orders = get_my_orders(page=1, page_size=50)

if not orders:
    st.markdown("""
    <div style="text-align: center; padding: 40px; color: #999;">
        <div style="font-size: 48px; margin-bottom: 12px;">📭</div>
        <p>You haven't placed any orders yet.</p>
        <p style="font-size: 13px;">Browse the catalog and add items to your cart to get started.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    for order in orders:
        st.markdown(f"""
        <div style="background: #2d2d3f; border: 1px solid #3d3d52; border-radius: 10px; padding: 16px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: #aaa; font-size: 13px;">Order #{order['id']}</span>
                <span style="font-size: 13px;">{status_badge(order['status'])}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #ee4d2d; font-weight: 700; font-size: 18px;">{format_currency(order['total_amount'])}</span>
                <span style="color: #888; font-size: 12px;">{order['created_at'][:10]}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Items
        if order.get("items"):
            with st.expander(f"📦 {len(order['items'])} item(s) in this order"):
                for item in order["items"]:
                    st.markdown(
                        f"- Equipment ID: `{item['equipment_id']}` | "
                        f"Qty: {item['quantity']} | "
                        f"{item['start_date']} → {item['end_date']} | "
                        f"Subtotal: {format_currency(item['subtotal'])}"
                    )

        # Action buttons
        col_a, col_b, col_c = st.columns(3)

        if order["status"] == "pending_payment":
            with col_a:
                if st.button("💳 Pay Now", key=f"pay_{order['id']}", use_container_width=True):
                    with st.spinner("Processing payment..."):
                        result = pay_order(order["id"], order["total_amount"])
                    if result:
                        st.success("Payment successful!")
                        st.rerun()
            with col_b:
                if st.button("❌ Cancel", key=f"cancel_{order['id']}", use_container_width=True):
                    with st.spinner("Cancelling..."):
                        result = cancel_order(order["id"])
                    if result:
                        st.warning("Order cancelled.")
                        st.rerun()

        elif order["status"] == "paid_escrow":
            with col_a:
                if st.button("❌ Cancel", key=f"cancel_{order['id']}", use_container_width=True):
                    with st.spinner("Cancelling..."):
                        result = cancel_order(order["id"])
                    if result:
                        st.warning("Order cancelled.")
                        st.rerun()

        elif order["status"] == "completed":
            with col_a:
                if st.button("⭐ Write Review", key=f"review_{order['id']}", use_container_width=True):
                    st.session_state["review_order_id"] = order["id"]
                    st.session_state["review_items"] = order.get("items", [])
                    st.switch_page("pages/10_Reviews.py")

        st.markdown("---")
