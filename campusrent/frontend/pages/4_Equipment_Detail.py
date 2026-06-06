"""Equipment detail page — Shopee/Tokopedia-style product detail with monthly calendar."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import date
import calendar
from api_client import get_equipment_detail
from utils import format_currency, condition_badge, is_logged_in, get_role
from styles import inject_global_styles

st.set_page_config(page_title="Equipment Detail — CampusRent", page_icon="🔎", layout="wide")
inject_global_styles()

# ─── Get Equipment ID ─────────────────────────────────────────────────────────

equipment_id = st.session_state.get("selected_equipment_id")

if not equipment_id:
    st.warning("No equipment selected.")
    if st.button("← Back to Catalog"):
        st.switch_page("pages/3_Equipment_Catalog.py")
    st.stop()

# ─── Fetch Detail ─────────────────────────────────────────────────────────────

with st.spinner("Loading..."):
    data = get_equipment_detail(equipment_id)

if not data:
    st.error("Failed to load equipment details.")
    if st.button("← Back to Catalog"):
        st.switch_page("pages/3_Equipment_Catalog.py")
    st.stop()

# ─── Back Button ──────────────────────────────────────────────────────────────

if st.button("← Back to Catalog"):
    st.switch_page("pages/3_Equipment_Catalog.py")

# ─── Product Detail Layout ────────────────────────────────────────────────────

col_img, col_detail = st.columns([1, 2])

with col_img:
    # Product image
    if data.get("photo") and os.path.exists(data["photo"]):
        st.image(data["photo"], use_container_width=True)
    else:
        st.markdown("""
        <div style="background: #f5f5f5; border-radius: 12px; height: 300px; display: flex; align-items: center; justify-content: center; font-size: 64px;">
            📦
        </div>
        """, unsafe_allow_html=True)

with col_detail:
    # Title
    st.markdown(f"<h2 style='margin-bottom: 8px;'>{data['name']}</h2>", unsafe_allow_html=True)

    # Rating
    if data.get("avg_rating"):
        stars = "★" * round(data["avg_rating"]) + "☆" * (5 - round(data["avg_rating"]))
        st.markdown(
            f"<span style='color: #ffc107; font-size: 18px;'>{stars}</span> "
            f"<span style='color: #666;'>({data['avg_rating']:.1f})</span>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<span style='color: #999;'>No reviews yet</span>", unsafe_allow_html=True)

    # Price
    st.markdown(
        f"<div class='detail-price'>{format_currency(data['price_per_day'])} <span style='font-size: 14px; color: #666; font-weight: 400;'>/ day</span></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Info grid
    col_a, col_b = st.columns(2)
    with col_a:
        condition_class = {"new": "badge-new", "good": "badge-good", "fair": "badge-fair"}.get(data["condition"], "badge-info")
        condition_label = {"new": "✨ New", "good": "👍 Good", "fair": "👌 Fair"}.get(data["condition"], data["condition"])
        st.markdown(f"**Condition:** <span class='badge {condition_class}'>{condition_label}</span>", unsafe_allow_html=True)
    with col_b:
        status_text = "🟢 Available" if data.get("is_active") else "🔴 Inactive"
        st.markdown(f"**Status:** {status_text}")

    # Vendor
    vendor = data.get("vendor")
    if vendor:
        st.markdown(f"""
        <div style="background: #f9f9f9; border-radius: 8px; padding: 12px; margin-top: 12px; display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 28px;">🏪</span>
            <div>
                <div style="font-weight: 600; color: #333;">{vendor.get('name') or 'Unnamed Vendor'}</div>
                <div style="font-size: 12px; color: #666;">{vendor.get('email', '')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Rent button area
    st.markdown("<br>", unsafe_allow_html=True)
    if is_logged_in() and get_role() == "penyewa":
        st.info(f"💡 Use Equipment ID `{equipment_id}` when placing an order from the **My Orders** page. An approved permit is required.")
    elif is_logged_in() and get_role() == "pemilik_toko":
        st.caption("You're a vendor — you cannot rent equipment.")
    elif not is_logged_in():
        st.warning("Log in as a Penyewa to rent this equipment.")

# ─── Description Section ──────────────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div class="detail-section">
    <h4 style="margin-top: 0;">📝 Description</h4>
""", unsafe_allow_html=True)
st.write(data.get("description") or "No description provided.")
st.markdown("</div>", unsafe_allow_html=True)

# ─── Availability Calendar ────────────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<h4>📅 Availability Calendar</h4>", unsafe_allow_html=True)

# Build availability lookup
availability = data.get("availability", [])
avail_map = {}
for entry in availability:
    avail_map[entry["date"]] = entry["available"]

today = date.today()

# Calendar month state
if "cal_year" not in st.session_state:
    st.session_state["cal_year"] = today.year
if "cal_month" not in st.session_state:
    st.session_state["cal_month"] = today.month

cal_year = st.session_state["cal_year"]
cal_month = st.session_state["cal_month"]

# Month navigation
col_prev, col_label, col_next = st.columns([1, 4, 1])

with col_prev:
    if st.button("◀", key="cal_prev", use_container_width=True):
        if cal_month == 1:
            st.session_state["cal_month"] = 12
            st.session_state["cal_year"] = cal_year - 1
        else:
            st.session_state["cal_month"] = cal_month - 1
        st.rerun()

with col_label:
    month_name = calendar.month_name[cal_month]
    st.markdown(
        f"<div class='cal-header' style='border-radius: 8px;'>{month_name} {cal_year}</div>",
        unsafe_allow_html=True,
    )

with col_next:
    if st.button("▶", key="cal_next", use_container_width=True):
        if cal_month == 12:
            st.session_state["cal_month"] = 1
            st.session_state["cal_year"] = cal_year + 1
        else:
            st.session_state["cal_month"] = cal_month + 1
        st.rerun()

# Legend
st.markdown("""
<div style="display: flex; gap: 16px; margin: 12px 0; font-size: 13px;">
    <span><span class="badge badge-success">●</span> Available</span>
    <span><span class="badge badge-danger">●</span> Booked/Blocked</span>
    <span style="color: #999;">● No data</span>
</div>
""", unsafe_allow_html=True)

# Calendar grid
day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
header_cols = st.columns(7)
for i, col in enumerate(header_cols):
    col.markdown(f"<div class='cal-day-header'>{day_names[i]}</div>", unsafe_allow_html=True)

cal = calendar.Calendar(firstweekday=0)
month_days = cal.monthdayscalendar(cal_year, cal_month)

for week in month_days:
    week_cols = st.columns(7)
    for i, day_num in enumerate(week):
        with week_cols[i]:
            if day_num == 0:
                st.markdown("<div class='cal-day-empty'>&nbsp;</div>", unsafe_allow_html=True)
            else:
                current_date = date(cal_year, cal_month, day_num)
                date_str = current_date.isoformat()

                if date_str in avail_map:
                    if avail_map[date_str]:
                        st.markdown(f"<div class='cal-day-available'>{day_num}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='cal-day-blocked'>{day_num}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='cal-day-empty'>{day_num}</div>", unsafe_allow_html=True)
