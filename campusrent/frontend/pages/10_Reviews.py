"""Reviews page — submit ratings for completed orders."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from api_client import create_review
from utils import require_auth, require_role
from styles import inject_global_styles

st.set_page_config(page_title="Write Review — CampusRent", page_icon="⭐", layout="wide")
inject_global_styles()

require_auth()
require_role(["penyewa"])

# ─── Header ───────────────────────────────────────────────────────────────────

st.markdown("""
<div style="background: linear-gradient(135deg, #ee4d2d 0%, #ff7043 100%); border-radius: 12px; padding: 24px 28px; margin-bottom: 20px;">
    <h2 style="color: white; margin: 0; font-weight: 700;">⭐ Write a Review</h2>
    <p style="color: rgba(255,255,255,0.85); margin: 4px 0 0 0;">Rate equipment from your completed orders</p>
</div>
""", unsafe_allow_html=True)

# ─── Review Form ──────────────────────────────────────────────────────────────

# Check if coming from My Orders page
review_order_id = st.session_state.get("review_order_id")
review_items = st.session_state.get("review_items", [])

if review_order_id:
    st.markdown(f"""
    <div style="background: #2d2d3f; border: 1px solid #3d3d52; border-radius: 10px; padding: 16px; margin-bottom: 16px;">
        <p style="color: #e0e0e0; margin: 0;">Reviewing Order <strong>#{review_order_id}</strong></p>
        <p style="color: #888; margin: 4px 0 0 0; font-size: 13px;">Items in this order: {len(review_items)}</p>
    </div>
    """, unsafe_allow_html=True)

st.subheader("Submit Review")

with st.form("review_form"):
    col1, col2 = st.columns(2)

    with col1:
        order_id = st.number_input(
            "Order ID",
            min_value=1,
            value=review_order_id if review_order_id else 1,
            step=1,
            help="The ID of your completed order",
        )

    with col2:
        # If we have items from the order, show them as options
        if review_items:
            equipment_ids = [item["equipment_id"] for item in review_items]
            equipment_id = st.selectbox(
                "Equipment ID",
                options=equipment_ids,
                help="Select which equipment to review",
            )
        else:
            equipment_id = st.number_input(
                "Equipment ID",
                min_value=1,
                step=1,
                help="The ID of the equipment you want to review",
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Star rating
    st.markdown("**Rating**")
    rating = st.slider(
        "Rate from 1 to 5 stars",
        min_value=1,
        max_value=5,
        value=5,
        help="1 = Poor, 5 = Excellent",
        label_visibility="collapsed",
    )

    # Visual stars
    stars_display = "⭐" * rating + "☆" * (5 - rating)
    rating_labels = {1: "Poor", 2: "Fair", 3: "Good", 4: "Very Good", 5: "Excellent"}
    st.markdown(f"<span style='font-size: 24px;'>{stars_display}</span> <span style='color: #bbb;'>— {rating_labels[rating]}</span>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    comment = st.text_area(
        "Comment (optional)",
        placeholder="Share your experience with this equipment...",
        max_chars=1000,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button("📝 Submit Review", type="primary", use_container_width=True)

    if submitted:
        with st.spinner("Submitting review..."):
            result = create_review(
                order_id=order_id,
                equipment_id=equipment_id,
                rating=rating,
                comment=comment,
            )
        if result:
            st.success("✅ Review submitted! Thank you for your feedback.")
            # Clear review state
            st.session_state.pop("review_order_id", None)
            st.session_state.pop("review_items", None)
            st.balloons()

st.divider()

if st.button("← Back to My Orders", use_container_width=True):
    st.switch_page("pages/6_My_Orders.py")
