"""Login page for CampusRent."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from api_client import login
from utils import is_logged_in

st.set_page_config(page_title="Login — CampusRent", page_icon="🔑")

st.title("🔑 Login")

if is_logged_in():
    st.success(f"You're already logged in as **{st.session_state['email']}**.")
    st.stop()

with st.form("login_form"):
    email = st.text_input("Email", placeholder="you@example.com")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login", use_container_width=True, type="primary")

    if submitted:
        if not email or not password:
            st.error("Please fill in both fields.")
        else:
            with st.spinner("Logging in..."):
                result = login(email, password)
            if result:
                import base64, json
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
                    st.success("Login successful!")
                    st.rerun()
                except Exception:
                    st.error("Failed to decode token.")

st.divider()
st.caption("Don't have an account? Go to the Register page.")
