"""Custom CSS styles for CampusRent — marketplace-inspired design."""

import streamlit as st


def inject_global_styles():
    """Inject global CSS to make the app look like a modern marketplace."""
    st.markdown("""
    <style>
    /* ─── Global ──────────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* ─── Remove Streamlit default white boxes / containers ───────────── */
    .stMainBlockContainer {
        padding-top: 1rem;
    }

    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
        padding: 0 !important;
    }

    div[data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
        padding: 0 !important;
    }

    /* Remove borders from column containers */
    div[data-testid="stColumn"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }

    /* Kill ALL white background containers */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }

    /* Force stColumn backgrounds transparent */
    .stColumn {
        background: transparent !important;
    }

    .stColumn > div {
        background: transparent !important;
    }

    /* Kill emotion-cache white backgrounds */
    [class*="st-emotion-cache"] {
        background-color: transparent !important;
    }

    /* But keep our custom styled elements */
    .product-card, .product-card-body, .product-card-img,
    .detail-section, .stat-card, .cal-header, .order-row,
    .cal-day-available, .cal-day-blocked,
    .hero-banner, [class*="badge"] {
        background-color: revert !important;
    }

    /* Re-apply our card colors after the override */
    .product-card { background: #2d2d3f !important; }
    .product-card-body { background: #2d2d3f !important; }
    .product-card-img { background: #1e1e2e !important; }
    .detail-section { background: #2d2d3f !important; }
    .stat-card { background: #2d2d3f !important; }
    .order-row { background: #2d2d3f !important; }
    .cal-header { background: #ee4d2d !important; }
    .cal-day-available { background: #1b5e20 !important; }
    .cal-day-blocked { background: #b71c1c !important; }

    /* ─── Sidebar ─────────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background-color: #1a1a2e;
    }

    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #ffffff;
    }

    /* ─── Product Cards ───────────────────────────────────────────────── */
    .product-card {
        background: #2d2d3f;
        border: 1px solid #3d3d52;
        border-radius: 12px;
        padding: 0;
        overflow: hidden;
        transition: all 0.2s ease;
        box-shadow: 0 1px 4px rgba(0,0,0,0.2);
        height: 100%;
    }

    .product-card:hover {
        box-shadow: 0 4px 16px rgba(238,77,45,0.2);
        transform: translateY(-2px);
        border-color: #ee4d2d;
    }

    .product-card-img {
        width: 100%;
        height: 180px;
        object-fit: cover;
        background: #1e1e2e;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 48px;
    }

    .product-card-body {
        padding: 12px 14px;
        background: #2d2d3f;
    }

    .product-card-title {
        font-size: 14px;
        font-weight: 500;
        color: #e0e0e0;
        margin-bottom: 6px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        line-height: 1.4;
    }

    .product-card-price {
        font-size: 16px;
        font-weight: 700;
        color: #ee4d2d;
        margin-bottom: 4px;
    }

    .product-card-meta {
        font-size: 12px;
        color: #aaa;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .product-card-rating {
        color: #ffc107;
        font-size: 12px;
    }

    /* ─── Hero / Banner ───────────────────────────────────────────────── */
    .hero-banner {
        background: linear-gradient(135deg, #ee4d2d 0%, #ff7043 100%);
        border-radius: 16px;
        padding: 40px 32px;
        color: white;
        margin-bottom: 24px;
    }

    .hero-banner h1 {
        color: white;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .hero-banner p {
        color: rgba(255,255,255,0.9);
        font-size: 16px;
        margin: 0;
    }

    /* ─── Search Bar ──────────────────────────────────────────────────── */
    .search-container {
        background: #ffffff;
        border: 2px solid #ee4d2d;
        border-radius: 8px;
        padding: 2px;
        margin-bottom: 20px;
    }

    /* ─── Status Badges ───────────────────────────────────────────────── */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
    }

    .badge-success { background: #e8f5e9; color: #2e7d32; }
    .badge-warning { background: #fff3e0; color: #ef6c00; }
    .badge-danger { background: #fce4ec; color: #c62828; }
    .badge-info { background: #e3f2fd; color: #1565c0; }
    .badge-new { background: #e8f5e9; color: #2e7d32; }
    .badge-good { background: #e3f2fd; color: #1565c0; }
    .badge-fair { background: #fff3e0; color: #ef6c00; }

    /* ─── Stats Cards ─────────────────────────────────────────────────── */
    .stat-card {
        background: #2d2d3f;
        border: 1px solid #3d3d52;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.2);
    }

    .stat-card-value {
        font-size: 28px;
        font-weight: 700;
        color: #ee4d2d;
    }

    .stat-card-label {
        font-size: 13px;
        color: #aaa;
        margin-top: 4px;
    }

    /* ─── Calendar ────────────────────────────────────────────────────── */
    .cal-header {
        background: #ee4d2d;
        color: white;
        border-radius: 12px 12px 0 0;
        padding: 16px;
        text-align: center;
        font-size: 18px;
        font-weight: 600;
    }

    .cal-grid {
        border: 1px solid #3d3d52;
        border-top: none;
        border-radius: 0 0 12px 12px;
        padding: 12px;
        background: #2d2d3f;
    }

    .cal-day-available {
        background: #1b5e20;
        color: #a5d6a7;
        border-radius: 6px;
        padding: 4px;
        text-align: center;
        font-weight: 500;
        font-size: 13px;
    }

    .cal-day-blocked {
        background: #b71c1c;
        color: #ef9a9a;
        border-radius: 6px;
        padding: 4px;
        text-align: center;
        font-weight: 500;
        font-size: 13px;
    }

    .cal-day-empty {
        color: #666;
        text-align: center;
        padding: 4px;
        font-size: 13px;
    }

    .cal-day-header {
        text-align: center;
        font-weight: 600;
        font-size: 12px;
        color: #aaa;
        padding: 4px;
    }

    /* ─── Detail Page ─────────────────────────────────────────────────── */
    .detail-price {
        font-size: 24px;
        font-weight: 700;
        color: #ee4d2d;
    }

    .detail-section {
        background: #2d2d3f;
        border: 1px solid #3d3d52;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        color: #e0e0e0;
    }

    .detail-section h4 {
        color: #ffffff;
    }

    .detail-section p {
        color: #bbb;
    }

    /* ─── Auth Pages ──────────────────────────────────────────────────── */
    .auth-container {
        max-width: 420px;
        margin: 0 auto;
        background: #2d2d3f;
        border: 1px solid #3d3d52;
        border-radius: 16px;
        padding: 32px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }

    .auth-header {
        text-align: center;
        margin-bottom: 24px;
    }

    .auth-header h2 {
        color: #ffffff;
        font-weight: 700;
    }

    /* ─── Buttons ─────────────────────────────────────────────────────── */
    .stButton > button[kind="primary"] {
        background-color: #ee4d2d;
        border-color: #ee4d2d;
    }

    .stButton > button[kind="primary"]:hover {
        background-color: #d73c1e;
        border-color: #d73c1e;
    }

    /* ─── Order Table ─────────────────────────────────────────────────── */
    .order-row {
        background: #2d2d3f;
        border: 1px solid #3d3d52;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        color: #e0e0e0;
    }

    </style>
    """, unsafe_allow_html=True)


def product_card_html(name: str, price: float, condition: str, rating: float = None, img_placeholder: str = "📦") -> str:
    """Generate HTML for a product card."""
    price_str = f"Rp {price:,.0f}"
    
    rating_html = ""
    if rating:
        stars = "★" * round(rating) + "☆" * (5 - round(rating))
        rating_html = f'<span class="product-card-rating">{stars} {rating:.1f}</span>'
    else:
        rating_html = '<span class="product-card-rating">No reviews</span>'

    condition_class = {"new": "badge-new", "good": "badge-good", "fair": "badge-fair"}.get(condition, "badge-info")
    condition_label = {"new": "New", "good": "Good", "fair": "Fair"}.get(condition, condition)

    return f"""
    <div class="product-card">
        <div class="product-card-img">{img_placeholder}</div>
        <div class="product-card-body">
            <div class="product-card-title">{name}</div>
            <div class="product-card-price">{price_str}/day</div>
            <div class="product-card-meta">
                <span class="badge {condition_class}">{condition_label}</span>
                {rating_html}
            </div>
        </div>
    </div>
    """


def stat_card_html(value: str, label: str) -> str:
    """Generate HTML for a stat card."""
    return f"""
    <div class="stat-card">
        <div class="stat-card-value">{value}</div>
        <div class="stat-card-label">{label}</div>
    </div>
    """
