import streamlit as st

from src.aggregator.search import search_all_platforms
from src.scraper.ably import search_product as ab
from src.scraper.musinsa import search_product as ms
from src.scraper.oliveyoung_playwright import search_product as oy
from src.scraper.zigzag import search_product as zz
from src.frontend.utils import group_similar_products

st.set_page_config(page_title="Beauty Price Finder", page_icon="💄")

st.title("💄 Multi-Platform Beauty Search")
st.caption("Compare product prices from OliveYoung, Ably, and Zigzag.")

keyword = st.text_input(
    "Enter product keyword", placeholder="e.g. 헤라 센슈얼 누드 글로스"
)

results = []

if st.button("Search") and keyword.strip():
    with st.spinner("Searching across platforms..."):
        # Define all scrapers with their platform names
        scrapers = [
            (oy, "OliveYoung"),
            (ab, "Ably"),
            (zz, "Zigzag"),
            (ms, "Musinsa"),
        ]
        
        results = search_all_platforms(keyword, scrapers)

if not results:
    st.error("No results found.")
else:
    grouped = group_similar_products(results)
    st.write(f"🔍 Found {len(results)} results, grouped into {len(grouped)} products.")
    
    for idx, group in enumerate(grouped, start=1):
        # Sort group by price (ascending - cheapest first)
        # Handle None or non-numeric prices by converting to float or using a large number
        def get_price(product):
            price = product.get("price")
            if price is None:
                return float('inf')
            try:
                return float(price)
            except (ValueError, TypeError):
                return float('inf')
        
        sorted_group = sorted(group, key=get_price)
        cheapest_price = get_price(sorted_group[0]) if sorted_group else None
        
        st.markdown(f"### 💄 {sorted_group[0]['name']}")
        
        cols = st.columns(len(sorted_group))
        
        for col_idx, (col, item) in enumerate(zip(cols, sorted_group)):
            with col:
                # Highlight cheapest product with a border and badge
                is_cheapest = get_price(item) == cheapest_price and cheapest_price != float('inf')
                
                # Show badge above the border for cheapest product
                if is_cheapest:
                    st.markdown("🏆 **최저가**")
                    st.markdown(
                        '<div style="border: 3px solid #FF6B6B; border-radius: 10px; padding: 10px; background-color: #FFF5F5; margin-bottom: 10px;">',
                        unsafe_allow_html=True
                    )
                
                if item.get("img"):
                    st.image(item.get("img"), width=120)
                
                st.markdown(f"**{item.get('source')}**")
                
                # Highlight price for cheapest
                price_display = f"💰 {item.get('price')} 원"
                if is_cheapest:
                    st.markdown(f"### {price_display}")
                else:
                    st.markdown(price_display)
                
                if item.get("url"):
                    st.markdown(f"[View Product]({item.get('url')})")
                
                if is_cheapest:
                    st.markdown('</div>', unsafe_allow_html=True)
        
        st.divider()
