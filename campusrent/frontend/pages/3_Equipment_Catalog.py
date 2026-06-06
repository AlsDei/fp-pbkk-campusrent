"""Equipment catalog page — Shopee/Tokopedia-style product grid."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from api_client import list_equipment
from utils import format_currency, condition_badge
from styles import inject_global_styles, product_card_html, stat_card_html

st.set_page_config(page_title="Equipment Catalog — CampusRent", page_icon="📦", layout="wide")
inject_global_styles()

# ─── Hero Section ─────────────────────────────────────────────────────────────

st.markdown("""
<div style="background: linear-gradient(135deg, #ee4d2d 0%, #ff7043 100%); border-radius: 12px; padding: 24px 28px; margin-bottom: 20px;">
    <h2 style="color: white; margin: 0; font-weight: 700;">📦 Equipment Catalog</h2>
    <p style="color: rgba(255,255,255,0.85); margin: 4px 0 0 0;">Find the perfect equipment for your campus event</p>
</div>
""", unsafe_allow_html=True)

# ─── Search Bar ───────────────────────────────────────────────────────────────

col_search, col_size = st.columns([4, 1])

with col_search:
    search = st.text_input(
        "Search",
        placeholder="🔍 Search equipment by name or description...",
        label_visibility="collapsed",
    )

with col_size:
    page_size = st.selectbox("Show", options=[12, 24, 48], index=0, label_visibility="collapsed")

# ─── Pagination State ─────────────────────────────────────────────────────────

if "catalog_page" not in st.session_state:
    st.session_state["catalog_page"] = 1
if "last_search" not in st.session_state:
    st.session_state["last_search"] = ""

if search != st.session_state["last_search"]:
    st.session_state["catalog_page"] = 1
    st.session_state["last_search"] = search

current_page = st.session_state["catalog_page"]

# ─── Fetch Data ───────────────────────────────────────────────────────────────

with st.spinner("Loading equipment..."):
    result = list_equipment(search=search, page=current_page, page_size=page_size)

if not result:
    st.info("No equipment found. Try a different search term.")
    st.stop()

items = result.get("items", [])
total = result.get("total", 0)
total_pages = max(1, (total + page_size - 1) // page_size)

# ─── Results Summary ──────────────────────────────────────────────────────────

st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
    <span style="color: #666; font-size: 14px;"><strong>{total}</strong> items found</span>
    <span style="color: #666; font-size: 14px;">Page {current_page} of {total_pages}</span>
</div>
""", unsafe_allow_html=True)

if not items:
    st.markdown("""
    <div style="text-align: center; padding: 60px 0; color: #999;">
        <div style="font-size: 48px; margin-bottom: 12px;">🔍</div>
        <p>No equipment found on this page.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ─── Product Grid (4 columns like Shopee) ─────────────────────────────────────

cols_per_row = 4

for i in range(0, len(items), cols_per_row):
    cols = st.columns(cols_per_row)
    for j, col in enumerate(cols):
        idx = i + j
        if idx >= len(items):
            break
        item = items[idx]
        with col:
            # Product card using HTML
            card = product_card_html(
                name=item["name"],
                price=item["price_per_day"],
                condition=item["condition"],
                rating=item.get("avg_rating"),
            )
            st.markdown(card, unsafe_allow_html=True)

            # View detail button
            if st.button("View Details", key=f"detail_{item['id']}", use_container_width=True):
                st.session_state["selected_equipment_id"] = item["id"]
                st.switch_page("pages/4_Equipment_Detail.py")

# ─── Pagination Controls ──────────────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)

col_prev, col_pages, col_next = st.columns([1, 3, 1])

with col_prev:
    if st.button("← Previous", disabled=(current_page <= 1), use_container_width=True):
        st.session_state["catalog_page"] -= 1
        st.rerun()

with col_pages:
    # Page number buttons
    page_cols = st.columns(min(total_pages, 5))
    start_page = max(1, current_page - 2)
    end_page = min(total_pages, start_page + 4)

    for i, p in enumerate(range(start_page, end_page + 1)):
        with page_cols[i]:
            if p == current_page:
                st.markdown(
                    f"<div style='text-align: center; background: #ee4d2d; color: white; border-radius: 6px; padding: 6px; font-weight: 600;'>{p}</div>",
                    unsafe_allow_html=True,
                )
            else:
                if st.button(str(p), key=f"page_{p}", use_container_width=True):
                    st.session_state["catalog_page"] = p
                    st.rerun()

with col_next:
    if st.button("Next →", disabled=(current_page >= total_pages), use_container_width=True):
        st.session_state["catalog_page"] += 1
        st.rerun()
