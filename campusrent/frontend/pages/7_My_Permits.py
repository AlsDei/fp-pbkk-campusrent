"""My Permits page — upload permit letters and check status."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from api_client import upload_permit
from utils import require_auth, require_role, status_badge
from styles import inject_global_styles

st.set_page_config(page_title="My Permits — CampusRent", page_icon="📄", layout="wide")
inject_global_styles()

require_auth()
require_role(["penyewa"])

# ─── Header ───────────────────────────────────────────────────────────────────

st.markdown("""
<div style="background: linear-gradient(135deg, #ee4d2d 0%, #ff7043 100%); border-radius: 12px; padding: 24px 28px; margin-bottom: 20px;">
    <h2 style="color: white; margin: 0; font-weight: 700;">📄 My Permits</h2>
    <p style="color: rgba(255,255,255,0.85); margin: 4px 0 0 0;">Upload your event permit letter for admin approval</p>
</div>
""", unsafe_allow_html=True)

# ─── Info Section ─────────────────────────────────────────────────────────────

st.markdown("""
<div style="background: #2d2d3f; border: 1px solid #3d3d52; border-radius: 10px; padding: 16px; margin-bottom: 20px;">
    <h4 style="color: #fff; margin: 0 0 8px 0;">ℹ️ About Permits</h4>
    <p style="color: #bbb; font-size: 14px; margin: 0;">
        Before you can rent equipment, you need to upload a <strong>permit letter</strong> 
        (Surat Izin Kegiatan) from your campus organization. An admin will review and approve it.
        Once approved, you can place orders.
    </p>
</div>
""", unsafe_allow_html=True)

# ─── Requirements ─────────────────────────────────────────────────────────────

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background: #2d2d3f; border: 1px solid #3d3d52; border-radius: 10px; padding: 14px; text-align: center;">
        <div style="font-size: 24px;">📎</div>
        <p style="color: #bbb; font-size: 12px; margin: 4px 0 0 0;"><strong>Format:</strong> PDF, JPG, PNG</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background: #2d2d3f; border: 1px solid #3d3d52; border-radius: 10px; padding: 14px; text-align: center;">
        <div style="font-size: 24px;">📏</div>
        <p style="color: #bbb; font-size: 12px; margin: 4px 0 0 0;"><strong>Max Size:</strong> 5 MB</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="background: #2d2d3f; border: 1px solid #3d3d52; border-radius: 10px; padding: 14px; text-align: center;">
        <div style="font-size: 24px;">⏱️</div>
        <p style="color: #bbb; font-size: 12px; margin: 4px 0 0 0;"><strong>Review:</strong> 1-2 days</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Upload Section ───────────────────────────────────────────────────────────

st.subheader("Upload Permit")

uploaded_file = st.file_uploader(
    "Choose your permit file",
    type=["pdf", "jpg", "jpeg", "png"],
    help="Upload your campus event permit letter. Max 5MB.",
)

if uploaded_file:
    # Show file preview
    file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)

    st.markdown(f"""
    <div style="background: #2d2d3f; border: 1px solid #3d3d52; border-radius: 10px; padding: 16px; margin: 12px 0;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 28px;">📎</span>
            <div>
                <p style="color: #e0e0e0; margin: 0; font-weight: 500;">{uploaded_file.name}</p>
                <p style="color: #888; margin: 0; font-size: 12px;">{file_size_mb:.2f} MB • {uploaded_file.type}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if file_size_mb > 5:
        st.error("File is too large. Maximum size is 5 MB.")
    else:
        if st.button("📤 Upload Permit", type="primary", use_container_width=True):
            with st.spinner("Uploading..."):
                result = upload_permit(uploaded_file)
            if result:
                st.success("✅ Permit uploaded successfully! Waiting for admin approval.")
                st.balloons()

st.divider()

# ─── Status Section ───────────────────────────────────────────────────────────

st.subheader("Permit Status")
st.caption("Your most recent permit submission:")

# We don't have a dedicated endpoint to get user's own permit status,
# so we show a general status guide
st.markdown("""
<div style="background: #2d2d3f; border: 1px solid #3d3d52; border-radius: 10px; padding: 16px;">
    <table style="width: 100%; color: #e0e0e0;">
        <tr>
            <td style="padding: 8px;">🟡 <strong>Pending</strong></td>
            <td style="padding: 8px; color: #bbb;">Your permit is waiting for admin review.</td>
        </tr>
        <tr>
            <td style="padding: 8px;">🟢 <strong>Approved</strong></td>
            <td style="padding: 8px; color: #bbb;">You can now place orders!</td>
        </tr>
        <tr>
            <td style="padding: 8px;">🔴 <strong>Rejected</strong></td>
            <td style="padding: 8px; color: #bbb;">Please upload a new permit with corrections.</td>
        </tr>
    </table>
</div>
""", unsafe_allow_html=True)

st.caption("💡 Tip: If your permit was rejected, simply upload a new one above. It will replace the previous submission.")
