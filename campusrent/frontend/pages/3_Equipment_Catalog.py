"""Equipment catalog page."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from api_client import list_equipment
from utils import format_currency, condition_badge

st.set_page_config(page_title="Equipment Catalog — CampusRent", page_icon="📦", layout="wide")

st.title("📦 Equipment Catalog")

# Search
search = st.text_input("🔍 Search", placeholder="Search by name or description...")

# Pagination
if "catalog_page" not in st.session_state:
    st.session_state["catalog_page"] = 1
if "last_search" not in st.session_state:
    st.session_state["last_search"] = ""
if search != st.session_state["last_search"]:
    st.session_state["catalog_page"] = 1
    st.session_state["last_search"] = search

page_size = 12
current_page = st.session_state["catalog_page"]

with st.spinner("Loading..."):
    result = list_equipment(search=search, page=current_page, page_size=page_size)

if not result or not result.get("items"):
    st.info("No equipment found.")
    st.stop()

items = result["items"]
total = result["total"]
total_pages = max(1, (total + page_size - 1) // page_size)

st.caption(f"**{total}** items found — Page {current_page} of {total_pages}")

# Grid display
cols_per_row = 4
for i in range(0, len(items), cols_per_row):
    cols = st.columns(cols_per_row)
    for j, col in enumerate(cols):
        idx = i + j
        if idx >= len(items):
            break
        item = items[idx]
        with col:
            with st.container(border=True):
                st.markdown(f"**{item['name']}**")
                st.write(f"💰 {format_currency(item['price_per_day'])}/day")
                st.write(f"📋 {condition_badge(item['condition'])}")
                if item.get("avg_rating"):
                    st.write(f"⭐ {item['avg_rating']:.1f}")
                else:
                    st.caption("No reviews")
                if st.button("View Details", key=f"detail_{item['id']}"):
                    st.session_state["selected_equipment_id"] = item["id"]
                    st.switch_page("pages/4_Equipment_Detail.py")

# Pagination
st.divider()
col_prev, col_info, col_next = st.columns([1, 2, 1])
with col_prev:
    if st.button("← Previous", disabled=(current_page <= 1), use_container_width=True):
        st.session_state["catalog_page"] -= 1
        st.rerun()
with col_info:
    st.write(f"Page {current_page} of {total_pages}")
with col_next:
    if st.button("Next →", disabled=(current_page >= total_pages), use_container_width=True):
        st.session_state["catalog_page"] += 1
        st.rerun()
