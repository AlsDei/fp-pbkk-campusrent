"""Vendor Dashboard."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from api_client import get_vendor_orders, deliver_order
from utils import require_auth, require_role, format_currency, status_badge

st.set_page_config(page_title="Vendor Dashboard — CampusRent", page_icon="📋", layout="wide")

require_auth()
require_role(["pemilik_toko"])

st.title("📋 Vendor Dashboard")

with st.spinner("Loading orders..."):
    result = get_vendor_orders(page=1, page_size=50)

if not result or not result.get("items"):
    st.info("No incoming orders yet.")
    st.stop()

orders = result["items"]

# Stats
paid_count = sum(1 for o in orders if o["status"] == "paid_escrow")
completed_count = sum(1 for o in orders if o["status"] == "completed")
revenue = sum(o["total_amount"] for o in orders if o["status"] == "completed")

col1, col2, col3 = st.columns(3)
col1.metric("Awaiting Delivery", paid_count)
col2.metric("Completed", completed_count)
col3.metric("Revenue", format_currency(revenue))

st.divider()

for order in orders:
    with st.container(border=True):
        col_id, col_status, col_amount = st.columns([1, 2, 2])
        with col_id:
            st.write(f"**Order #{order['id']}**")
        with col_status:
            st.write(status_badge(order["status"]))
        with col_amount:
            st.write(f"**{format_currency(order['total_amount'])}**")

        if order.get("renter_name") or order.get("renter_email"):
            st.caption(f"Renter: {order.get('renter_name', 'N/A')} • {order.get('renter_email', '')} • {order.get('renter_phone', '')}")

        if order.get("items"):
            with st.expander(f"📦 {len(order['items'])} item(s)"):
                for item in order["items"]:
                    st.write(f"Equipment `{item['equipment_id']}` | Qty: {item['quantity']} | {item['start_date']} → {item['end_date']}")

        if order["status"] == "paid_escrow":
            if st.button("✅ Confirm Delivery", key=f"deliver_{order['id']}", use_container_width=True):
                with st.spinner("Confirming..."):
                    deliver_order(order["id"])
                st.rerun()
