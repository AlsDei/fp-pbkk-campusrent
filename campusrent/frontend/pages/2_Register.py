"""Registration page for CampusRent — marketplace style."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from api_client import register
from utils import is_logged_in
from styles import inject_global_styles

st.set_page_config(page_title="Register — CampusRent", page_icon="📝", layout="centered")
inject_global_styles()

# Redirect if already logged in
if is_logged_in():
    st.switch_page("app.py")

# ─── Register UI ─────────────────────────────────────────────────────────────

st.markdown("""
<div class="auth-header">
    <span style="font-size: 48px;">🎓</span>
    <h2>Create Account</h2>
    <p style="color: #666;">Join CampusRent today</p>
</div>
""", unsafe_allow_html=True)

with st.form("register_form"):
    email = st.text_input("📧 Email", placeholder="you@example.com")
    password = st.text_input("🔒 Password", type="password", placeholder="Minimum 8 characters")
    password_confirm = st.text_input("🔒 Confirm Password", type="password", placeholder="Re-enter your password")

    st.markdown("<br>", unsafe_allow_html=True)

    role = st.radio(
        "I want to register as:",
        options=["penyewa", "pemilik_toko"],
        format_func=lambda x: "🛒 Penyewa (Renter) — Rent equipment" if x == "penyewa" else "🏪 Pemilik Toko (Vendor) — List equipment for rent",
        horizontal=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")

    if submitted:
        if not email or not password or not password_confirm:
            st.error("Please fill in all fields.")
        elif len(password) < 8:
            st.error("Password must be at least 8 characters.")
        elif password != password_confirm:
            st.error("Passwords do not match.")
        else:
            with st.spinner("Creating your account..."):
                result = register(email, password, role)

            if result:
                st.success(f"✅ Account created! Your ID is **{result['id']}**. You can now log in.")
                st.balloons()

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.markdown("<p style='color: #666; font-size: 14px;'>Already have an account?</p>", unsafe_allow_html=True)
with col2:
    if st.button("🔑 Login here", use_container_width=True):
        st.switch_page("pages/1_Login.py")
