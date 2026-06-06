"""HTTP client wrapper for the CampusRent FastAPI backend."""

import streamlit as st
import requests
from typing import Any, Optional


BASE_URL = "http://localhost:8000"


def _get_headers() -> dict[str, str]:
    """Build request headers, including auth token if available."""
    headers = {"Accept": "application/json"}
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _handle_response(response: requests.Response) -> dict | list | None:
    """
    Parse API response. Returns JSON on success, None on error
    (and shows error via st.error).
    """
    if response.status_code == 401:
        # Token expired or invalid — clear session
        for key in ["token", "role", "user_id", "email"]:
            st.session_state.pop(key, None)
        st.error("Session expired. Please log in again.")
        return None

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", "Unknown error")
        except Exception:
            detail = response.text or f"Error {response.status_code}"
        st.error(f"Error: {detail}")
        return None

    if response.status_code == 204:
        return {}

    return response.json()


# ─── Auth Endpoints ──────────────────────────────────────────────────────────


def register(email: str, password: str, role: str) -> Optional[dict]:
    """Register a new user."""
    resp = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "password": password, "role": role},
        headers={"Accept": "application/json"},
    )
    return _handle_response(resp)


def login(email: str, password: str) -> Optional[dict]:
    """Login and return token response."""
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password},
        headers={"Accept": "application/json"},
    )
    return _handle_response(resp)


# ─── Equipment Endpoints ─────────────────────────────────────────────────────


def list_equipment(search: str = "", page: int = 1, page_size: int = 20) -> Optional[dict]:
    """Get paginated equipment catalog."""
    params = {"page": page, "page_size": page_size}
    if search:
        params["search"] = search
    resp = requests.get(
        f"{BASE_URL}/equipment",
        params=params,
        headers=_get_headers(),
    )
    return _handle_response(resp)


def get_equipment_detail(equipment_id: int) -> Optional[dict]:
    """Get full equipment detail with availability."""
    resp = requests.get(
        f"{BASE_URL}/equipment/{equipment_id}",
        headers=_get_headers(),
    )
    return _handle_response(resp)


def create_equipment(
    name: str, description: str, price_per_day: float, condition: str, photo_file
) -> Optional[dict]:
    """Create new equipment listing with photo."""
    headers = {}
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    files = {"photo": (photo_file.name, photo_file.getvalue(), photo_file.type)}
    data = {
        "name": name,
        "description": description,
        "price_per_day": str(price_per_day),
        "condition": condition,
    }
    resp = requests.post(
        f"{BASE_URL}/equipment/equipment",
        data=data,
        files=files,
        headers=headers,
    )
    return _handle_response(resp)


def update_equipment(equipment_id: int, **fields) -> Optional[dict]:
    """Update equipment fields."""
    # Remove None values
    payload = {k: v for k, v in fields.items() if v is not None}
    resp = requests.put(
        f"{BASE_URL}/equipment/equipment/{equipment_id}",
        json=payload,
        headers=_get_headers(),
    )
    return _handle_response(resp)


def delete_equipment(equipment_id: int) -> Optional[dict]:
    """Delete an equipment listing."""
    resp = requests.delete(
        f"{BASE_URL}/equipment/equipment/{equipment_id}",
        headers=_get_headers(),
    )
    return _handle_response(resp)


def manage_availability(equipment_id: int, dates: list[dict]) -> Optional[dict]:
    """Block/unblock dates for equipment."""
    resp = requests.post(
        f"{BASE_URL}/equipment/equipment/{equipment_id}/availability",
        json={"dates": dates},
        headers=_get_headers(),
    )
    return _handle_response(resp)


# ─── Order Endpoints ─────────────────────────────────────────────────────────


def place_order(items: list[dict]) -> Optional[dict]:
    """Place a new rental order."""
    resp = requests.post(
        f"{BASE_URL}/orders/",
        json={"items": items},
        headers=_get_headers(),
    )
    return _handle_response(resp)


def pay_order(order_id: int, amount: float) -> Optional[dict]:
    """Pay for an order."""
    resp = requests.post(
        f"{BASE_URL}/orders/{order_id}/pay",
        json={"amount": amount},
        headers=_get_headers(),
    )
    return _handle_response(resp)


def get_my_orders(page: int = 1, page_size: int = 20) -> Optional[list]:
    """Get current user's order history."""
    resp = requests.get(
        f"{BASE_URL}/orders/",
        params={"page": page, "page_size": page_size},
        headers=_get_headers(),
    )
    return _handle_response(resp)


def cancel_order(order_id: int) -> Optional[dict]:
    """Cancel an order."""
    resp = requests.post(
        f"{BASE_URL}/orders/{order_id}/cancel",
        headers=_get_headers(),
    )
    return _handle_response(resp)


def get_vendor_orders(page: int = 1, page_size: int = 20) -> Optional[dict]:
    """Get vendor's incoming orders."""
    resp = requests.get(
        f"{BASE_URL}/vendor/orders",
        params={"page": page, "page_size": page_size},
        headers=_get_headers(),
    )
    return _handle_response(resp)


def deliver_order(order_id: int) -> Optional[dict]:
    """Vendor confirms delivery."""
    resp = requests.post(
        f"{BASE_URL}/vendor/orders/{order_id}/deliver",
        headers=_get_headers(),
    )
    return _handle_response(resp)


# ─── Permit Endpoints ────────────────────────────────────────────────────────


def upload_permit(file) -> Optional[dict]:
    """Upload a permit file."""
    headers = {}
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    files = {"file": (file.name, file.getvalue(), file.type)}
    resp = requests.post(
        f"{BASE_URL}/permits/",
        files=files,
        headers=headers,
    )
    return _handle_response(resp)


def list_pending_permits(page: int = 1, page_size: int = 20) -> Optional[dict]:
    """Admin: list pending permits."""
    resp = requests.get(
        f"{BASE_URL}/permits/pending",
        params={"page": page, "page_size": page_size},
        headers=_get_headers(),
    )
    return _handle_response(resp)


def verify_permit(permit_id: int, action: str, rejection_reason: str = "") -> Optional[dict]:
    """Admin: approve or reject a permit."""
    payload: dict[str, Any] = {"action": action}
    if action == "reject":
        payload["rejection_reason"] = rejection_reason
    resp = requests.post(
        f"{BASE_URL}/permits/{permit_id}/verify",
        json=payload,
        headers=_get_headers(),
    )
    return _handle_response(resp)


# ─── Review Endpoints ────────────────────────────────────────────────────────


def create_review(
    order_id: int, equipment_id: int, rating: int, comment: str = ""
) -> Optional[dict]:
    """Submit a review for a completed order item."""
    payload: dict[str, Any] = {
        "order_id": order_id,
        "equipment_id": equipment_id,
        "rating": rating,
    }
    if comment:
        payload["comment"] = comment
    resp = requests.post(
        f"{BASE_URL}/reviews/",
        json=payload,
        headers=_get_headers(),
    )
    return _handle_response(resp)


# ─── Admin Endpoints ─────────────────────────────────────────────────────────


def blacklist_user(user_id: int, reason: str) -> Optional[dict]:
    """Admin: blacklist a user."""
    resp = requests.post(
        f"{BASE_URL}/admin/users/{user_id}/blacklist",
        json={"reason": reason},
        headers=_get_headers(),
    )
    return _handle_response(resp)


def issue_fine(order_id: int, amount: float) -> Optional[dict]:
    """Admin: issue a cancellation fine."""
    resp = requests.post(
        f"{BASE_URL}/admin/orders/{order_id}/fine",
        json={"amount": amount},
        headers=_get_headers(),
    )
    return _handle_response(resp)
