"""Admin Panel — review permits, blacklist users, issue fines."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import os
from api_client import list_pending_permits, verify_permit, blacklist_user, issue_fine, download_permit
from utils import require_auth, require_role, format_currency

st.set_page_config(page_title="Admin Panel — CampusRent", page_icon="🛡️", layout="wide")

require_auth()
require_role(["admin"])

st.title("🛡️ Admin Panel")

tab_permits, tab_users, tab_fines = st.tabs(["📄 Pending Permits", "👥 Blacklist User", "💰 Issue Fine"])

# ─── Pending Permits ──────────────────────────────────────────────────────────

with tab_permits:
    st.subheader("Pending Permit Applications")

    with st.spinner("Loading..."):
        result = list_pending_permits(page=1, page_size=50)

    if not result or not result.get("items"):
        st.info("No pending permits to review.")
    else:
        permits = result["items"]
        st.caption(f"{result['total']} pending permit(s)")

        for permit in permits:
            with st.container(border=True):
                col_info, col_action = st.columns([3, 2])

                with col_info:
                    st.write(f"**Permit #{permit['id']}**")
                    st.write(f"Submitter: {permit.get('submitter_name') or 'N/A'} ({permit.get('submitter_email') or 'N/A'})")
                    st.caption(f"User ID: {permit['user_id']} • Submitted: {str(permit.get('created_at', ''))[:10]}")
                    st.caption(f"File: `{permit['file_path']}`")

                    # Download button
                    filename = os.path.basename(permit.get("file_path", "permit"))
                    file_data = download_permit(permit["id"])
                    if file_data:
                        st.download_button(
                            "📥 Download File",
                            data=file_data,
                            file_name=filename,
                            key=f"dl_{permit['id']}",
                        )
                    else:
                        st.caption("⚠️ File not available on server")

                with col_action:
                    col_approve, col_reject = st.columns(2)
                    with col_approve:
                        if st.button("✅ Approve", key=f"approve_{permit['id']}", use_container_width=True):
                            with st.spinner("Approving..."):
                                res = verify_permit(permit["id"], "approve")
                            if res:
                                st.success(f"Permit #{permit['id']} approved!")
                                st.rerun()

                    with col_reject:
                        if st.button("❌ Reject", key=f"reject_btn_{permit['id']}", use_container_width=True):
                            st.session_state[f"show_reject_{permit['id']}"] = True

                    # Rejection reason input
                    if st.session_state.get(f"show_reject_{permit['id']}"):
                        reason = st.text_input("Rejection reason", key=f"reason_{permit['id']}", max_chars=500)
                        if st.button("Confirm Reject", key=f"confirm_reject_{permit['id']}"):
                            if not reason:
                                st.error("Please provide a reason.")
                            else:
                                with st.spinner("Rejecting..."):
                                    res = verify_permit(permit["id"], "reject", reason)
                                if res:
                                    st.warning(f"Permit #{permit['id']} rejected.")
                                    st.session_state.pop(f"show_reject_{permit['id']}", None)
                                    st.rerun()

# ─── Blacklist User ───────────────────────────────────────────────────────────

with tab_users:
    st.subheader("Blacklist a User")
    st.caption("Blacklisted users cannot log in or use the platform.")

    with st.form("blacklist_form"):
        user_id = st.number_input("User ID", min_value=1, step=1)
        reason = st.text_input("Reason", max_chars=500, placeholder="e.g., Repeated policy violations")

        if st.form_submit_button("🚫 Blacklist User", type="primary", use_container_width=True):
            if not reason:
                st.error("Please provide a reason.")
            else:
                with st.spinner("Blacklisting..."):
                    res = blacklist_user(user_id, reason)
                if res:
                    st.success(f"User {res.get('email', user_id)} has been blacklisted.")

# ─── Issue Fine ───────────────────────────────────────────────────────────────

with tab_fines:
    st.subheader("Issue Cancellation Fine")
    st.caption("For orders with status 'cancelled_pending_fine'. Fine amount must be between 0.01 and the order total.")

    with st.form("fine_form"):
        order_id = st.number_input("Order ID", min_value=1, step=1)
        amount = st.number_input("Fine Amount (Rp)", min_value=0.01, step=1000.0)

        if st.form_submit_button("💰 Issue Fine", type="primary", use_container_width=True):
            with st.spinner("Issuing fine..."):
                res = issue_fine(order_id, amount)
            if res:
                st.success(f"Fine of {format_currency(amount)} issued for Order #{order_id}.")
