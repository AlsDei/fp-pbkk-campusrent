"""Cart page."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import date as dt_date
from api_client import place_order
from utils import require_auth, require_role, format_currency

st.set_page_config(page_title="Cart — CampusRent", page_icon="🛒", layout="wide")

require_auth()
require_role(["penyewa"])

st.title("🛒 Shopping Cart")

cart = st.session_state.get("cart", [])

if not cart:
    st.info("Your cart is empty. Browse the catalog to add items.")
    if st.button("📦 Browse Catalog"):
        st.switch_page("pages/3_Equipment_Catalog.py")
    st.stop()

total = 0
items_to_remove = []

for idx, item in enumerate(cart):
    try:
        s = dt_date.fromisoformat(item["start_date"])
        e = dt_date.fromisoformat(item["end_date"])
        num_days = (e - s).days + 1
    except Exception:
        num_days = 1

    total += item["subtotal"]

    with st.container(border=True):
        col_info, col_price, col_del = st.columns([3, 1, 1])
        with col_info:
            st.write(f"**{item['name']}**")
            st.caption(f"Qty: {item['quantity']} • {item['start_date']} → {item['end_date']} ({num_days} days)")
        with col_price:
            st.write(f"**{format_currency(item['subtotal'])}**")
        with col_del:
            if st.button("🗑️", key=f"rm_{idx}"):
                items_to_remove.append(idx)

if items_to_remove:
    for idx in sorted(items_to_remove, reverse=True):
        st.session_state["cart"].pop(idx)
    st.rerun()

st.divider()
st.subheader(f"Total: {format_currency(total)}")

col_clear, col_shop, col_checkout = st.columns(3)
with col_clear:
    if st.button("🗑️ Clear Cart", use_container_width=True):
        st.session_state["cart"] = []
        st.rerun()
with col_shop:
    if st.button("📦 Continue Shopping", use_container_width=True):
        st.switch_page("pages/3_Equipment_Catalog.py")
with col_checkout:
    if st.button("✅ Checkout", type="primary", use_container_width=True):
        order_items = [{
            "equipment_id": item["equipment_id"],
            "quantity": item["quantity"],
            "start_date": item["start_date"],
            "end_date": item["end_date"],
        } for item in cart]

        with st.spinner("Placing order..."):
            result = place_order(order_items)
        if result:
            st.success(f"Order #{result['id']} placed! Total: {format_currency(result['total_amount'])}")
            st.session_state["cart"] = []
            st.balloons()
