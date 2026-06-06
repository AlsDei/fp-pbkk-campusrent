"""Cart page — review items, adjust, and checkout."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import date as dt_date
from api_client import place_order
from utils import require_auth, require_role, format_currency
from styles import inject_global_styles

st.set_page_config(page_title="Cart — CampusRent", page_icon="🛒", layout="wide")
inject_global_styles()

require_auth()
require_role(["penyewa"])

# ─── Header ───────────────────────────────────────────────────────────────────

cart = st.session_state.get("cart", [])

st.markdown(f"""
<div style="background: linear-gradient(135deg, #ee4d2d 0%, #ff7043 100%); border-radius: 12px; padding: 24px 28px; margin-bottom: 20px;">
    <h2 style="color: white; margin: 0; font-weight: 700;">🛒 Shopping Cart</h2>
    <p style="color: rgba(255,255,255,0.85); margin: 4px 0 0 0;">{len(cart)} item(s) in your cart</p>
</div>
""", unsafe_allow_html=True)

# ─── Empty State ──────────────────────────────────────────────────────────────

if not cart:
    st.markdown("""
    <div style="text-align: center; padding: 60px; color: #999;">
        <div style="font-size: 64px; margin-bottom: 16px;">🛒</div>
        <h3 style="color: #e0e0e0;">Your cart is empty</h3>
        <p>Browse the catalog and add items to your cart.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("📦 Browse Catalog", use_container_width=True):
        st.switch_page("pages/3_Equipment_Catalog.py")
    st.stop()

# ─── Cart Items ───────────────────────────────────────────────────────────────

total = 0
items_to_remove = []

for idx, item in enumerate(cart):
    num_days = 1
    try:
        s = dt_date.fromisoformat(item["start_date"])
        e = dt_date.fromisoformat(item["end_date"])
        num_days = (e - s).days + 1
    except Exception:
        pass

    total += item["subtotal"]

    col_info, col_action = st.columns([4, 1])

    with col_info:
        st.markdown(f"""
        <div style="background: #2d2d3f; border: 1px solid #3d3d52; border-radius: 10px; padding: 16px; margin-bottom: 4px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <p style="color: #e0e0e0; font-weight: 600; font-size: 15px; margin: 0;">📦 {item['name']}</p>
                    <p style="color: #888; font-size: 13px; margin: 6px 0 0 0;">
                        Qty: {item['quantity']} &nbsp;•&nbsp; {item['start_date']} → {item['end_date']} &nbsp;•&nbsp; {num_days} day(s)
                    </p>
                    <p style="color: #aaa; font-size: 12px; margin: 4px 0 0 0;">
                        {format_currency(item['price_per_day'])} × {num_days} × {item['quantity']}
                    </p>
                </div>
                <span style="color: #ee4d2d; font-weight: 700; font-size: 16px;">{format_currency(item['subtotal'])}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_action:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️", key=f"remove_{idx}", use_container_width=True):
            items_to_remove.append(idx)

# Remove items
if items_to_remove:
    for idx in sorted(items_to_remove, reverse=True):
        st.session_state["cart"].pop(idx)
    st.rerun()

# ─── Order Summary ────────────────────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"""
<div style="background: #1a1a2e; border: 2px solid #ee4d2d; border-radius: 12px; padding: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <p style="color: #aaa; margin: 0; font-size: 13px;">Order Total ({len(cart)} item(s))</p>
            <p style="color: #ee4d2d; font-weight: 700; font-size: 26px; margin: 4px 0 0 0;">{format_currency(total)}</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Actions ──────────────────────────────────────────────────────────────────

col_browse, col_clear, col_checkout = st.columns([1, 1, 2])

with col_browse:
    if st.button("📦 Continue Shopping", use_container_width=True):
        st.switch_page("pages/3_Equipment_Catalog.py")

with col_clear:
    if st.button("🗑️ Clear Cart", use_container_width=True):
        st.session_state["cart"] = []
        st.rerun()

with col_checkout:
    if st.button("✅ Checkout & Place Order", type="primary", use_container_width=True):
        # Convert cart to order items format
        order_items = []
        for item in cart:
            order_items.append({
                "equipment_id": item["equipment_id"],
                "quantity": item["quantity"],
                "start_date": item["start_date"],
                "end_date": item["end_date"],
            })

        with st.spinner("Placing order..."):
            result = place_order(order_items)

        if result:
            st.success(f"✅ Order #{result['id']} placed successfully! Total: {format_currency(result['total_amount'])}")
            st.session_state["cart"] = []
            st.balloons()

# ─── Notes ────────────────────────────────────────────────────────────────────

st.divider()
st.caption("💡 You need an approved permit before checking out. The order will be in 'pending payment' status after checkout.")
