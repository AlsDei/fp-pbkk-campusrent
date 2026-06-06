"""
CampusRent — Streamlit Frontend
Main entry point: handles navigation sidebar and session state initialization.

Run with: streamlit run campusrent/frontend/app.py
"""

import streamlit as st

# ─── Page Config ─────────────────────────────────────────────────────────────

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

# ─── Styles ──────────────────────────────────────────────────────────────────

from styles import inject_global_styles
inject_global_styles()

# ─── Sidebar Navigation ─────────────────────────────────────────────────────

from utils import is_logged_in, get_role, logout

st.sidebar.markdown("""
<div style="text-align: center; padding: 16px 0;">
    <span style="font-size: 36px;">🎓</span>
    <h2 style="margin: 4px 0 0 0; color: #ee4d2d; font-weight: 700;">CampusRent</h2>
    <p style="margin: 0; font-size: 12px; color: #999;">Campus Equipment Marketplace</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()

if is_logged_in():
    st.sidebar.markdown(f"""
    <div style="background: rgba(255,255,255,0.05); border-radius: 8px; padding: 12px; margin-bottom: 8px;">
        <p style="margin: 0; font-size: 13px; color: #aaa;">Logged in as</p>
        <p style="margin: 2px 0 0 0; font-weight: 600; color: #fff;">{st.session_state['email']}</p>
        <p style="margin: 2px 0 0 0; font-size: 12px; color: #ee4d2d; text-transform: uppercase;">{st.session_state['role']}</p>
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()
        st.rerun()
else:
    st.sidebar.info("Log in or register to get started.")

# ─── Main Content — Home Page ────────────────────────────────────────────────

# Hero Banner
st.markdown("""
<div class="hero-banner">
    <h1>🎓 CampusRent</h1>
    <p>Rent campus equipment easily and securely. Projectors, cameras, speakers — all in one place.</p>
</div>
""", unsafe_allow_html=True)

# Feature cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="detail-section" style="text-align: center;">
        <div style="font-size: 36px; margin-bottom: 8px;">📦</div>
        <h4 style="margin: 0; color: #fff;">Browse & Rent</h4>
        <p style="color: #bbb; font-size: 13px;">Find equipment from verified campus vendors. Pay securely with escrow.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="detail-section" style="text-align: center;">
        <div style="font-size: 36px; margin-bottom: 8px;">🏪</div>
        <h4 style="margin: 0; color: #fff;">List Equipment</h4>
        <p style="color: #bbb; font-size: 13px;">Vendors can list equipment, manage availability, and earn from rentals.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="detail-section" style="text-align: center;">
        <div style="font-size: 36px; margin-bottom: 8px;">🔒</div>
        <h4 style="margin: 0; color: #fff;">Secure & Trusted</h4>
        <p style="color: #bbb; font-size: 13px;">Permit verification, escrow payments, and admin oversight keep everyone safe.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Role-specific quick links
if not is_logged_in():
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <p style="color: #666; font-size: 16px;">Get started by logging in or creating an account.</p>
    </div>
    """, unsafe_allow_html=True)

    col_login, col_register = st.columns(2)
    with col_login:
        if st.button("🔑 Login", use_container_width=True):
            st.switch_page("pages/1_Login.py")
    with col_register:
        if st.button("📝 Register", use_container_width=True):
            st.switch_page("pages/2_Register.py")
else:
    role = get_role()

    if role == "penyewa":
        st.subheader("Quick Actions")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("📦 Browse Equipment", use_container_width=True):
                st.switch_page("pages/3_Equipment_Catalog.py")
        with col_b:
            if st.button("📄 My Permits", use_container_width=True):
                st.switch_page("pages/6_My_Permits.py")
        with col_c:
            if st.button("🛒 My Orders", use_container_width=True):
                st.switch_page("pages/5_My_Orders.py")

    elif role == "pemilik_toko":
        st.subheader("Quick Actions")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("🏪 My Equipment", use_container_width=True):
                st.switch_page("pages/8_Vendor_Equipment.py")
        with col_b:
            if st.button("📋 Incoming Orders", use_container_width=True):
                st.switch_page("pages/7_Vendor_Dashboard.py")
        with col_c:
            if st.button("📦 Browse Catalog", use_container_width=True):
                st.switch_page("pages/3_Equipment_Catalog.py")

    elif role == "admin":
        st.subheader("Quick Actions")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📄 Review Permits", use_container_width=True):
                st.switch_page("pages/9_Admin_Panel.py")
        with col_b:
            if st.button("📦 Browse Catalog", use_container_width=True):
                st.switch_page("pages/3_Equipment_Catalog.py")
