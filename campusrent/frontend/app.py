"""
CampusRent — Streamlit Frontend
Main entry point with role-based navigation.

Run with: streamlit run campusrent/frontend/app.py
"""

import streamlit as st

st.set_page_config(
    page_title="CampusRent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Session State Initialization ────────────────────────────────────────────

if "token" not in st.session_state:
    st.session_state["token"] = None
if "role" not in st.session_state:
    st.session_state["role"] = None
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "email" not in st.session_state:
    st.session_state["email"] = None

from utils import is_logged_in, get_role, logout

# ─── Sidebar ─────────────────────────────────────────────────────────────────

st.sidebar.title("🎓 CampusRent")

if is_logged_in():
    st.sidebar.write(f"**{st.session_state['email']}**")
    st.sidebar.caption(f"Role: {st.session_state['role']}")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()
        st.rerun()

    cart = st.session_state.get("cart", [])
    if cart:
        st.sidebar.success(f"🛒 Cart: {len(cart)} item(s)")
        if st.sidebar.button("View Cart", use_container_width=True):
            st.switch_page("pages/5_Cart.py")
else:
    st.sidebar.info("Log in or register to get started.")

# ─── Home Page Content ────────────────────────────────────────────────────────

st.title("🎓 CampusRent")
st.subheader("Campus Equipment Rental Marketplace")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("📦 **Browse & Rent**\n\nFind equipment from verified campus vendors. Pay securely with escrow.")

with col2:
    st.info("🏪 **List Equipment**\n\nVendors can list equipment, manage availability, and earn from rentals.")

with col3:
    st.info("🔒 **Secure & Trusted**\n\nPermit verification, escrow payments, and admin oversight.")

st.divider()

if not is_logged_in():
    st.write("Get started by logging in or creating an account.")
    col_login, col_register = st.columns(2)
    with col_login:
        if st.button("🔑 Login", use_container_width=True):
            st.switch_page("pages/1_Login.py")
    with col_register:
        if st.button("📝 Register", use_container_width=True):
            st.switch_page("pages/2_Register.py")
else:
    role = get_role()
    st.success(f"Welcome back, **{st.session_state['email']}**!")

    if role == "penyewa":
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("📦 Browse Equipment", use_container_width=True):
                st.switch_page("pages/3_Equipment_Catalog.py")
        with col_b:
            if st.button("📄 My Permits", use_container_width=True):
                st.switch_page("pages/7_My_Permits.py")
        with col_c:
            if st.button("🛒 My Orders", use_container_width=True):
                st.switch_page("pages/6_My_Orders.py")

    elif role == "pemilik_toko":
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("🏪 My Equipment", use_container_width=True):
                st.switch_page("pages/9_Vendor_Equipment.py")
        with col_b:
            if st.button("📋 Incoming Orders", use_container_width=True):
                st.switch_page("pages/8_Vendor_Dashboard.py")
        with col_c:
            if st.button("📦 Browse Catalog", use_container_width=True):
                st.switch_page("pages/3_Equipment_Catalog.py")

    elif role == "admin":
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📄 Review Permits", use_container_width=True):
                st.switch_page("pages/9_Admin_Panel.py")
        with col_b:
            if st.button("📦 Browse Catalog", use_container_width=True):
                st.switch_page("pages/3_Equipment_Catalog.py")
