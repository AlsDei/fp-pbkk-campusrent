"""Equipment detail page with availability calendar."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import date, timedelta
import calendar
from api_client import get_equipment_detail
from utils import format_currency, condition_badge, is_logged_in, get_role

st.set_page_config(page_title="Equipment Detail — CampusRent", page_icon="🔎", layout="wide")

equipment_id = st.session_state.get("selected_equipment_id")
if not equipment_id:
    st.warning("No equipment selected.")
    if st.button("← Back to Catalog"):
        st.switch_page("pages/3_Equipment_Catalog.py")
    st.stop()

with st.spinner("Loading..."):
    data = get_equipment_detail(equipment_id)

if not data:
    st.error("Failed to load equipment.")
    st.stop()

if st.button("← Back to Catalog"):
    st.switch_page("pages/3_Equipment_Catalog.py")

# Build availability map
availability = data.get("availability", [])
avail_map = {entry["date"]: entry["available"] for entry in availability}

# ─── Detail ───────────────────────────────────────────────────────────────────

st.title(data["name"])

col_info, col_rent = st.columns([2, 1])

with col_info:
    st.metric("Price per Day", format_currency(data["price_per_day"]))
    st.write(f"**Condition:** {condition_badge(data['condition'])}")
    if data.get("avg_rating"):
        st.write(f"**Rating:** ⭐ {data['avg_rating']:.1f}")
    else:
        st.write("**Rating:** No reviews yet")
    st.write(f"**Status:** {'🟢 Active' if data.get('is_active') else '🔴 Inactive'}")

    vendor = data.get("vendor")
    if vendor:
        st.write(f"**Vendor:** {vendor.get('name') or 'Unnamed'} ({vendor.get('email', '')})")

    st.divider()
    st.subheader("Description")
    st.write(data.get("description") or "No description.")

with col_rent:
    if is_logged_in() and get_role() == "penyewa":
        st.subheader("🛒 Rent")
        start_date = st.date_input("Start Date", key="cart_start")
        end_date = st.date_input("End Date", key="cart_end")

        quantity = 1
        dates_available = True

        if end_date >= start_date:
            num_days = (end_date - start_date).days + 1
            estimated = data["price_per_day"] * num_days

            # Check availability
            unavailable_dates = []
            check = start_date
            while check <= end_date:
                ds = check.isoformat()
                if ds in avail_map and not avail_map[ds]:
                    unavailable_dates.append(ds)
                check += timedelta(days=1)

            if unavailable_dates:
                dates_available = False
                st.error(f"Not available on: {', '.join(unavailable_dates)}")
            else:
                st.success("✅ Available!")

            st.write(f"**Total:** {format_currency(estimated)}")
        else:
            st.error("End date must be after start date.")
            estimated = 0
            dates_available = False

        col_cart, col_buy = st.columns(2)
        with col_cart:
            if st.button("🛒 Add to Cart", disabled=not dates_available, use_container_width=True):
                if "cart" not in st.session_state:
                    st.session_state["cart"] = []
                st.session_state["cart"].append({
                    "equipment_id": equipment_id,
                    "name": data["name"],
                    "quantity": quantity,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "price_per_day": data["price_per_day"],
                    "subtotal": estimated,
                })
                st.success(f"Added! ({len(st.session_state['cart'])} items)")
        with col_buy:
            if st.button("⚡ Rent Now", disabled=not dates_available, type="primary", use_container_width=True):
                st.session_state["cart"] = [{
                    "equipment_id": equipment_id,
                    "name": data["name"],
                    "quantity": quantity,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "price_per_day": data["price_per_day"],
                    "subtotal": estimated,
                }]
                st.switch_page("pages/5_Cart.py")

        st.caption("You need an approved permit to checkout.")
    elif not is_logged_in():
        st.info("Log in as Penyewa to rent.")
    else:
        st.caption("Vendors cannot rent equipment.")

# ─── Calendar ─────────────────────────────────────────────────────────────────

st.divider()
st.subheader("📅 Availability Calendar")

today = date.today()
if "cal_year" not in st.session_state:
    st.session_state["cal_year"] = today.year
if "cal_month" not in st.session_state:
    st.session_state["cal_month"] = today.month

cal_year = st.session_state["cal_year"]
cal_month = st.session_state["cal_month"]

col_prev, col_label, col_next = st.columns([1, 3, 1])
with col_prev:
    if st.button("◀ Prev", key="cal_prev"):
        if cal_month == 1:
            st.session_state["cal_month"] = 12
            st.session_state["cal_year"] -= 1
        else:
            st.session_state["cal_month"] -= 1
        st.rerun()
with col_label:
    st.subheader(f"{calendar.month_name[cal_month]} {cal_year}")
with col_next:
    if st.button("Next ▶", key="cal_next"):
        if cal_month == 12:
            st.session_state["cal_month"] = 1
            st.session_state["cal_year"] += 1
        else:
            st.session_state["cal_month"] += 1
        st.rerun()

st.caption("🟢 Available | 🔴 Blocked/Booked | ⚪ No data")

day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
header_cols = st.columns(7)
for i, col in enumerate(header_cols):
    col.write(f"**{day_names[i]}**")

cal = calendar.Calendar(firstweekday=0)
for week in cal.monthdayscalendar(cal_year, cal_month):
    week_cols = st.columns(7)
    for i, day_num in enumerate(week):
        with week_cols[i]:
            if day_num == 0:
                st.write("")
            else:
                d = date(cal_year, cal_month, day_num)
                ds = d.isoformat()
                if ds in avail_map:
                    icon = "🟢" if avail_map[ds] else "🔴"
                else:
                    icon = "⚪"
                st.write(f"{icon} {day_num}")
