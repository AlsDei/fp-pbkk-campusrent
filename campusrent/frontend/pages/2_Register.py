"""Registration page for CampusRent."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from api_client import register
from utils import is_logged_in

st.set_page_config(page_title="Register — CampusRent", page_icon="📝")

st.title("📝 Register")

if is_logged_in():
    st.success(f"You're already logged in as **{st.session_state['email']}**.")
    st.stop()

with st.form("register_form"):
    email = st.text_input("Email", placeholder="you@example.com")
    password = st.text_input("Password", type="password", help="Minimum 8 characters")
    password_confirm = st.text_input("Confirm Password", type="password")
    role = st.selectbox(
        "Register as",
        options=["penyewa", "pemilik_toko"],
        format_func=lambda x: "🛒 Penyewa (Renter)" if x == "penyewa" else "🏪 Pemilik Toko (Vendor)",
    )
    submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")

    if submitted:
        if not email or not password or not password_confirm:
            st.error("Please fill in all fields.")
        elif len(password) < 8:
            st.error("Password must be at least 8 characters.")
        elif password != password_confirm:
            st.error("Passwords do not match.")
        else:
            with st.spinner("Creating account..."):
                result = register(email, password, role)
            if result:
                st.success(f"Account created! ID: {result['id']}. You can now log in.")
                st.balloons()

st.divider()
st.caption("Already have an account? Go to the Login page.")
