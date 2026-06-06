"""Reviews page."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from api_client import create_review
from utils import require_auth, require_role

st.set_page_config(page_title="Write Review — CampusRent", page_icon="⭐")

require_auth()
require_role(["penyewa"])

st.title("⭐ Write a Review")

review_order_id = st.session_state.get("review_order_id")
review_items = st.session_state.get("review_items", [])

with st.form("review_form"):
    order_id = st.number_input("Order ID", min_value=1, value=review_order_id or 1, step=1)

    if review_items:
        equipment_id = st.selectbox("Equipment ID", [i["equipment_id"] for i in review_items])
    else:
        equipment_id = st.number_input("Equipment ID", min_value=1, step=1)

    rating = st.slider("Rating", 1, 5, 5)
    st.write("⭐" * rating + "☆" * (5 - rating))

    comment = st.text_area("Comment (optional)", max_chars=1000)

    if st.form_submit_button("Submit Review", type="primary", use_container_width=True):
        with st.spinner("Submitting..."):
            result = create_review(order_id, equipment_id, rating, comment)
        if result:
            st.success("Review submitted!")
            st.session_state.pop("review_order_id", None)
            st.session_state.pop("review_items", None)
            st.balloons()

st.divider()
if st.button("← Back to Orders"):
    st.switch_page("pages/6_My_Orders.py")
