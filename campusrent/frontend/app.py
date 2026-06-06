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

# ─── Sidebar Navigation ─────────────────────────────────────────────────────

from utils import is_logged_in, get_role, logout

st.sidebar.title("🎓 CampusRent")
st.sidebar.divider()

if is_logged_in():
    st.sidebar.write(f"Logged in as: **{st.session_state['email']}**")
    st.sidebar.write(f"Role: `{st.session_state['role']}`")
    st.sidebar.divider()

    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()
        st.rerun()
else:
    st.sidebar.info("Please log in or register to get started.")

# ─── Main Content ────────────────────────────────────────────────────────────

st.title("🎓 CampusRent")
st.subheader("Campus Equipment Rental Marketplace")

st.markdown("""
Welcome to **CampusRent** — rent campus equipment easily and securely.

### How it works

1. **Renters (Penyewa)**: Browse equipment, upload a permit letter for approval, 
   then place orders and pay through our escrow system.

2. **Vendors (Pemilik Toko)**: List your equipment with photos, manage availability, 
   and confirm deliveries to release payments.

3. **Admins**: Review permit applications, manage users, and handle cancellation fines.

---

👈 Use the sidebar to navigate between pages.
""")

if not is_logged_in():
    st.info("Navigate to the **Login** or **Register** page from the sidebar to get started.")
else:
    role = get_role()
    st.success(f"You're logged in as **{st.session_state['email']}** ({role})")

    if role == "penyewa":
        st.markdown("""
        **Quick links for renters:**
        - 📦 Browse equipment catalog
        - 📄 Upload/check permit status
        - 🛒 View your orders
        - ⭐ Leave reviews
        """)
    elif role == "pemilik_toko":
        st.markdown("""
        **Quick links for vendors:**
        - 🏪 Manage your equipment listings
        - 📋 View incoming orders
        - ✅ Confirm deliveries
        """)
    elif role == "admin":
        st.markdown("""
        **Quick links for admins:**
        - 📄 Review pending permits
        - 👥 Manage users
        - 💰 Issue fines
        """)
