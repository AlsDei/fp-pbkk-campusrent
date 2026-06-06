"""My Permits page."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from api_client import upload_permit
from utils import require_auth, require_role

st.set_page_config(page_title="My Permits — CampusRent", page_icon="📄")

require_auth()
require_role(["penyewa"])

st.title("📄 My Permits")
st.write("Upload your event permit letter for admin approval before placing orders.")

st.info("**Requirements:** PDF, JPG, or PNG • Max 5 MB")

uploaded_file = st.file_uploader("Upload permit file", type=["pdf", "jpg", "jpeg", "png"])

if uploaded_file:
    file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
    st.write(f"📎 **{uploaded_file.name}** ({file_size_mb:.2f} MB)")

    if file_size_mb > 5:
        st.error("File too large. Max 5 MB.")
    else:
        if st.button("📤 Upload Permit", type="primary", use_container_width=True):
            with st.spinner("Uploading..."):
                result = upload_permit(uploaded_file)
            if result:
                st.success("Permit uploaded! Waiting for admin approval.")
                st.balloons()

st.divider()
st.subheader("Status Guide")
st.write("🟡 **Pending** — Waiting for admin review")
st.write("🟢 **Approved** — You can place orders")
st.write("🔴 **Rejected** — Upload a new permit with corrections")
