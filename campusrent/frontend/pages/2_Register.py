"""Registration page for CampusRent."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from api_client import register
from utils import is_logged_in

st.set_page_config(page_title="Register — CampusRent", page_icon="📝")

st.title("📝 Register")

# Redirect if already logged in
if is_logged_in():
    st.success(f"You're already logged in as **{st.session_state['email']}**.")
    st.info("Use the sidebar to navigate.")
    st.stop()

# Registration form
with st.form("register_form"):
    st.subheader("Create a new account")

    email = st.text_input("Email", placeholder="you@example.com")
    password = st.text_input(
        "Password",
        type="password",
        placeholder="Minimum 8 characters",
    )
    password_confirm = st.text_input(
        "Confirm Password",
        type="password",
        placeholder="Re-enter your password",
    )

    role = st.selectbox(
        "I want to register as",
        options=["penyewa", "pemilik_toko"],
        format_func=lambda x: "Penyewa (Renter)" if x == "penyewa" else "Pemilik Toko (Vendor)",
    )

    st.caption(
        "**Penyewa**: Rent equipment from vendors. "
        "**Pemilik Toko**: List and rent out your equipment."
    )

    submitted = st.form_submit_button("Register", use_container_width=True)

    if submitted:
        # Validation
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
                st.success(
                    f"Account created successfully! "
                    f"Your ID is **{result['id']}**. "
                    f"You can now log in."
                )
                st.balloons()

st.divider()
st.markdown("Already have an account? Go to the **Login** page from the sidebar.")
