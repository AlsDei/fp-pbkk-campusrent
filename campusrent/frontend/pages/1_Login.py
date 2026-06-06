"""Login page for CampusRent — marketplace style."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from api_client import login
from utils import is_logged_in
from styles import inject_global_styles

st.set_page_config(page_title="Login — CampusRent", page_icon="🔑", layout="centered")
inject_global_styles()

# Redirect if already logged in
if is_logged_in():
    st.switch_page("app.py")

# ─── Login UI ────────────────────────────────────────────────────────────────

st.markdown("""
<div class="auth-header">
    <span style="font-size: 48px;">🎓</span>
    <h2>Welcome Back</h2>
    <p style="color: #666;">Log in to CampusRent</p>
</div>
""", unsafe_allow_html=True)

with st.form("login_form"):
    email = st.text_input("📧 Email", placeholder="you@example.com")
    password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")

    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button("Login", use_container_width=True, type="primary")

    if submitted:
        if not email or not password:
            st.error("Please fill in both email and password.")
        else:
            with st.spinner("Logging in..."):
                result = login(email, password)

            if result:
                import base64
                import json

                token = result["access_token"]

                try:
                    payload_b64 = token.split(".")[1]
                    padding = 4 - len(payload_b64) % 4
                    if padding != 4:
                        payload_b64 += "=" * padding
                    payload = json.loads(base64.urlsafe_b64decode(payload_b64))

                    st.session_state["token"] = token
                    st.session_state["role"] = payload.get("role")
                    st.session_state["user_id"] = int(payload.get("sub"))
                    st.session_state["email"] = email.lower()

                    st.success("✅ Login successful! Redirecting...")
                    st.rerun()
                except Exception:
                    st.error("Failed to decode token. Please try again.")

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.markdown("<p style='color: #666; font-size: 14px;'>Don't have an account?</p>", unsafe_allow_html=True)
with col2:
    if st.button("📝 Register here", use_container_width=True):
        st.switch_page("pages/2_Register.py")
