import streamlit as st
import sqlite3
import pandas as pd
import time
import os
import sys
import subprocess

# --- Path Injection (Fix for Streamlit Cloud ModuleNotFoundError) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
# app.py is in src/cosver, so we need the parent of cosver (which is src)
src_path = os.path.abspath(os.path.join(current_dir, ".."))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from cosver.aggregator.search import search_all_platforms
from cosver.scraper.ably import search_product as ab
from cosver.scraper.musinsa import search_product as ms
from cosver.scraper.oliveyoung_playwright import search_product as oy
from cosver.scraper.zigzag import search_product as zz
from cosver.frontend.utils import group_similar_products

# --- Playwright Install (for Streamlit Cloud) ---
@st.cache_resource
def install_playwright():
    """Install Playwright browsers if not already present."""
    import sys
    import subprocess
    
    # We force this on Linux (typical for cloud envs) if we aren't in a local known env
    # Or just check for a common Streamlit Cloud env var
    is_streamlit_cloud = os.getenv("STREAMLIT_RUNTIME_ENV") == "cloud" or os.path.exists("/home/appuser")
    
    if is_streamlit_cloud or sys.platform.startswith("linux"):
        try:
            # First check if we already have chromium
            import playwright
            print("🚀 Checking Playwright browsers...")
            # We use --with-deps to be safe, though packages.txt should handle most
            result = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                st.info("Playwright browsers initialized.")
                print("✅ Playwright chromium installed")
            else:
                print(f"⚠️ Playwright install output: {result.stdout} {result.stderr}")
        except Exception as e:
            print(f"❌ Playwright install failed: {e}")
            st.error(f"Playwright Browser Installation Failed: {e}")

# Run installation
install_playwright()

# --- Page Config ---
st.set_page_config(page_title="올최맞", page_icon="💄", layout="centered")

# --- UI Rules & CSS (Follows cosver.md) ---
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    :root {
        --primary-color: #96b82d;
        --accent-color: #FF4B4B;
        --text-main: #222222;
        --text-sub: #666666;
        --border-color: #EEEEEE;
        --safe-margin: 16px;
    }

    * {
        font-family: 'Pretendard', -apple-system, system-ui, sans-serif;
        box-sizing: border-box;
    }

    .main-container {
        padding: 0 var(--safe-margin);
    }

    /* Skeleton Loader */
    @keyframes shimmer {
        100% { transform: translateX(100%); }
    }
    .skeleton-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
        gap: 12px;
    }
    .skeleton-card {
        background: #f8f8f8;
        border-radius: 12px;
        height: 280px;
        position: relative;
        overflow: hidden;
    }
    .skeleton-card::after {
        content: "";
        position: absolute;
        top: 0; right: 0; bottom: 0; left: 0;
        transform: translateX(-100%);
        background-image: linear-gradient(90deg, rgba(255,255,255,0) 0, rgba(255,255,255,0.2) 20%, rgba(255,255,255,0.5) 60%, rgba(255,255,255,0));
        animation: shimmer 1.5s infinite;
    }

    /* Product Grid */
    .product-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
        gap: 12px;
        margin-bottom: 24px;
    }

    /* Product Card */
    .product-card {
        display: flex;
        flex-direction: column;
        border: 1px solid var(--border-color);
        border-radius: 12px;
        overflow: hidden;
        background: white;
        text-decoration: none;
        color: inherit;
        transition: transform 0.1s ease-in-out;
        height: 100%;
        position: relative;
    }

    .product-card:active {
        transform: scale(0.95);
    }

    .image-container {
        width: 100%;
        aspect-ratio: 1 / 1;
        background: #f8f8f8;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 8px;
    }

    .product-image {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }

    .info-container {
        padding: 10px;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
    }

    .platform-name {
        font-size: 10px;
        font-weight: 700;
        color: var(--text-sub);
        margin-bottom: 2px;
        text-transform: uppercase;
    }

    .product-title {
        font-size: 13px;
        line-height: 1.4;
        font-weight: 500;
        color: var(--text-main);
        margin-bottom: 8px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        min-height: 36px;
    }

    .price-row {
        margin-top: auto;
        display: flex;
        align-items: baseline;
        gap: 1px;
    }

    .price-val {
        font-size: 15px;
        font-weight: 800;
        color: var(--text-main);
    }

    .price-currency {
        font-size: 11px;
        font-weight: 500;
        color: var(--text-main);
    }

    .lowest-price .price-val, .lowest-price .price-currency {
        color: var(--accent-color);
    }

    .lowest-badge {
        position: absolute;
        top: 6px;
        left: 6px;
        background: var(--accent-color);
        color: white;
        font-size: 9px;
        font-weight: 700;
        padding: 2px 5px;
        border-radius: 3px;
        z-index: 5;
    }

    .cheapest-card {
        border: 2px solid var(--accent-color) !important;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.2);
    }

    .cheapest-card .platform-name {
        color: var(--accent-color) !important;
        font-weight: 900;
    }

    /* Price Difference Badge */
    .price-diff-badge {
        font-size: 9px;
        padding: 2px 5px;
        border-radius: 3px;
        background: #f5f5f5;
        color: #999;
        margin-top: 4px;
        display: inline-block;
        font-weight: 600;
    }
    
    .price-diff-badge.cheapest {
        background: var(--accent-color);
        color: white;
    }

    .view-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 44px;
        background: #222;
        color: white;
        font-size: 13px;
        font-weight: 700;
        text-decoration: none;
        margin: 0 10px 10px 10px;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

def format_price(price):
    try:
        if price is None: return "N/A"
        return f"{int(float(price)):,}"
    except:
        return str(price)

def render_card_html(item, is_cheapest=False, price_diff=0):
    img_src = item.get("img", "")
    source_name = item.get("source", item.get("platform", "Unknown"))
    price_val = format_price(item.get("price"))
    product_url = item.get("url", "#")
    name = item.get("name", "Product")
    
    badge_html = '<div class="lowest-badge">🏆 최저가</div>' if is_cheapest else ''
    lowest_class = "lowest-price" if is_cheapest else ""
    card_class = "cheapest-card" if is_cheapest else ""
    
    # Price difference badge
    diff_badge = ""
    if is_cheapest:
        diff_badge = '<div class="price-diff-badge cheapest">최저가</div>'
    elif price_diff > 0:
        diff_badge = f'<div class="price-diff-badge">+{format_price(price_diff)}원</div>'
    
    return f"""<a href="{product_url}" target="_blank" class="product-card {card_class}">
{badge_html}
<div class="image-container">
<img src="{img_src}" class="product-image" loading="lazy">
</div>
<div class="info-container">
<div class="platform-name">{source_name}</div>
<div class="product-title">{name}</div>
<div class="price-row {lowest_class}">
<span class="price-val">{price_val}</span>
<span class="price-currency">원</span>
</div>
{diff_badge}
</div>
<div class="view-btn">보러가기</div>
</a>"""

# --- Custom Header ---
st.markdown('<div class="header-container"><h1>💄 올최맞</h1><p style="color: #666;">OliveYoung, Ably, Zigzag, Musinsa 최저가 검색</p></div>', unsafe_allow_html=True)

# --- Main App Logic ---
keyword = st.text_input("Product Search", placeholder="e.g. 헤라 센슈얼 누드 글로스", label_visibility="collapsed")

results = []
if st.button("Search") and keyword.strip():
    # Simulation of Skeleton Loaders
    skeleton_placeholder = st.empty()
    with skeleton_placeholder:
        skel_html = '<div class="skeleton-grid">' + '<div class="skeleton-card"></div>' * 4 + '</div>'
        st.markdown(skel_html, unsafe_allow_html=True)
    
    scrapers = [
        (oy, "OliveYoung"),
        (ab, "Ably"),
        (zz, "Zigzag"),
        (ms, "Musinsa"),
    ]
    
    with st.spinner("Searching across platforms..."):
        results = search_all_platforms(keyword, scrapers)
    
    skeleton_placeholder.empty()

if results:
    grouped = group_similar_products(results)
    st.write(f"🔍 Found {len(results)} results, grouped into {len(grouped)} products.")
    
    for group in grouped:
        def get_price_val(p):
            p_val = p.get("price")
            try: return float(p_val) if p_val else float('inf')
            except: return float('inf')
            
        sorted_group = sorted(group, key=get_price_val)
        cheapest_price = get_price_val(sorted_group[0])
        
        st.markdown(f"### 💄 {sorted_group[0].get('name', 'Product Group')}")
        
        # --- Unified Grid View with Price Info ---
        grid_html = '<div class="product-grid">'
        for item in sorted_group:
            p_val = get_price_val(item)
            is_cheapest = p_val == cheapest_price and cheapest_price != float('inf')
            price_diff = p_val - cheapest_price if cheapest_price != float('inf') else 0
            grid_html += render_card_html(item, is_cheapest=is_cheapest, price_diff=price_diff)
        grid_html += '</div>'
        
        st.markdown(grid_html, unsafe_allow_html=True)
        st.divider()
elif not results:
    st.info("Enter a product to start searching.")
