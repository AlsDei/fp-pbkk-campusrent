"""Shared utility helpers for the Streamlit frontend."""

import streamlit as st


def is_logged_in() -> bool:
    """Check if a user is currently authenticated."""
    return st.session_state.get("token") is not None


def get_role() -> str | None:
    """Get the current user's role from session state."""
    return st.session_state.get("role")


def get_user_id() -> int | None:
    """Get the current user's ID from session state."""
    return st.session_state.get("user_id")


def require_auth():
    """
    Guard that stops page execution if user is not authenticated.
    Displays a warning and stops the script.
    """
    if not is_logged_in():
        st.warning("Please log in to access this page.")
        st.stop()


def require_role(allowed_roles: list[str]):
    """
    Guard that stops page execution if user doesn't have the required role.
    Must be called after require_auth().
    """
    role = get_role()
    if role not in allowed_roles:
        st.error("You do not have permission to access this page.")
        st.stop()


def logout():
    """Clear all authentication state."""
    for key in ["token", "role", "user_id", "email"]:
        st.session_state.pop(key, None)


def format_currency(amount: float) -> str:
    """Format a number as Indonesian Rupiah."""
    return f"Rp {amount:,.0f}"


def status_badge(status: str) -> str:
    """Return a colored emoji + label for order/permit statuses."""
    badges = {
        "pending_payment": "🟡 Pending Payment",
        "paid_escrow": "🔵 Paid (Escrow)",
        "completed": "🟢 Completed",
        "cancelled": "⚫ Cancelled",
        "cancelled_pending_fine": "🟠 Cancelled (Pending Fine)",
        "cancelled_fined": "🔴 Cancelled (Fined)",
        "pending": "🟡 Pending",
        "approved": "🟢 Approved",
        "rejected": "🔴 Rejected",
        "active": "🟢 Active",
        "suspended": "🟠 Suspended",
        "blacklisted": "🔴 Blacklisted",
    }
    return badges.get(status, status)


def condition_badge(condition: str) -> str:
    """Return a label for equipment condition."""
    labels = {
        "new": "✨ New",
        "good": "👍 Good",
        "fair": "👌 Fair",
    }
    return labels.get(condition, condition)
