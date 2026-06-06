"""Vendor Equipment Management."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import timedelta
from api_client import list_equipment, create_equipment, update_equipment, delete_equipment, manage_availability
from utils import require_auth, require_role, format_currency, condition_badge

st.set_page_config(page_title="My Equipment — CampusRent", page_icon="🏪", layout="wide")

require_auth()
require_role(["pemilik_toko"])

st.title("🏪 My Equipment")

tab_list, tab_add, tab_avail = st.tabs(["📋 My Listings", "➕ Add New", "📅 Availability"])

# ─── Listings ─────────────────────────────────────────────────────────────────

with tab_list:
    with st.spinner("Loading..."):
        result = list_equipment(page=1, page_size=50)

    user_id = st.session_state.get("user_id")
    items = [i for i in (result.get("items", []) if result else []) if i.get("vendor_id") == user_id]

    if not items:
        st.info("No listings yet. Go to 'Add New' tab.")
    else:
        for item in items:
            with st.container(border=True):
                col_name, col_price, col_cond, col_status = st.columns([3, 1, 1, 1])
                with col_name:
                    st.write(f"**{item['name']}** (ID: {item['id']})")
                with col_price:
                    st.write(format_currency(item["price_per_day"]))
                with col_cond:
                    st.write(condition_badge(item["condition"]))
                with col_status:
                    st.write("🟢" if item["is_active"] else "🔴")

                col_edit, col_toggle, col_del = st.columns(3)
                with col_edit:
                    with st.expander("✏️ Edit"):
                        new_name = st.text_input("Name", value=item["name"], key=f"n_{item['id']}")
                        new_price = st.number_input("Price", value=item["price_per_day"], key=f"p_{item['id']}")
                        new_cond = st.selectbox("Condition", ["new", "good", "fair"],
                                               index=["new", "good", "fair"].index(item["condition"]), key=f"c_{item['id']}")
                        if st.button("Save", key=f"save_{item['id']}"):
                            update_equipment(item["id"], name=new_name, price_per_day=new_price, condition=new_cond)
                            st.rerun()
                with col_toggle:
                    label = "Deactivate" if item["is_active"] else "Activate"
                    if st.button(label, key=f"tog_{item['id']}", use_container_width=True):
                        update_equipment(item["id"], is_active=not item["is_active"])
                        st.rerun()
                with col_del:
                    if st.button("🗑️ Delete", key=f"del_{item['id']}", use_container_width=True):
                        delete_equipment(item["id"])
                        st.rerun()

# ─── Add New ──────────────────────────────────────────────────────────────────

with tab_add:
    with st.form("add_form"):
        name = st.text_input("Name", max_chars=100)
        description = st.text_area("Description", max_chars=1000)
        col1, col2 = st.columns(2)
        with col1:
            price = st.number_input("Price/day (Rp)", min_value=1.0, value=50000.0, step=1000.0)
        with col2:
            condition = st.selectbox("Condition", ["new", "good", "fair"])
        photo = st.file_uploader("Photo (JPG/PNG)", type=["jpg", "jpeg", "png"])

        if st.form_submit_button("Create", type="primary", use_container_width=True):
            if not name or not description or not photo:
                st.error("All fields and photo are required.")
            else:
                with st.spinner("Creating..."):
                    res = create_equipment(name, description, price, condition, photo)
                if res:
                    st.success(f"Created! ID: {res['id']}")
                    st.balloons()

# ─── Availability ─────────────────────────────────────────────────────────────

with tab_avail:
    eq_id = st.number_input("Equipment ID", min_value=1, step=1)
    col_from, col_to = st.columns(2)
    with col_from:
        date_from = st.date_input("From")
    with col_to:
        date_to = st.date_input("To")
    action = st.radio("Action", ["Block", "Unblock"], horizontal=True)

    if st.button("Apply", type="primary"):
        if date_to < date_from:
            st.error("'To' must be after 'From'.")
        else:
            dates = []
            cur = date_from
            while cur <= date_to:
                dates.append({"date": cur.isoformat(), "is_blocked": action == "Block"})
                cur += timedelta(days=1)
            with st.spinner("Updating..."):
                res = manage_availability(eq_id, dates)
            if res:
                st.success(f"{len(dates)} date(s) {'blocked' if action == 'Block' else 'unblocked'}!")
