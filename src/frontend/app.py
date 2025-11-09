import streamlit as st
import sys
from pathlib import Path

# Python import 시스템 설명:
# - Python은 sys.path에 있는 디렉토리에서만 모듈을 찾습니다
# - streamlit run src/frontend/app.py 실행 시, Python은 src/frontend/만 경로에 추가합니다
# - 하지만 scraper 모듈은 src/scraper/에 있으므로, src/를 경로에 추가해야 합니다
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from scraper.oliveyoung_playwright import search_product as oy
from scraper.ably import search_product as ab
from scraper.zigzag import search_product as zz
from scraper.musinsa import search_product as ms

st.set_page_config(page_title="Beauty Price Finder", page_icon="💄")

st.title("💄 Multi-Platform Beauty Search")
st.caption("Compare product prices from OliveYoung, Ably, and Zigzag.")

keyword = st.text_input(
    "Enter product keyword", placeholder="e.g. 헤라 센슈얼 누드 글로스"
)

if st.button("Search") and keyword.strip():
    with st.spinner("Searching across platforms..."):
        results = []

        try:
            oy = oy(keyword)
            for r in oy:
                r["source"] = "OliveYoung"
            results += oy
        except Exception as e:
            st.warning(f"OliveYoung error: {e}")

        try:
            ably = ab(keyword)
            for r in ably:
                r["source"] = "Ably"
            results += ably
        except Exception as e:
            st.warning(f"Ably error: {e}")

        try:
            zig = zz(keyword)
            for r in zig:
                r["source"] = "Zigzag"
            results += zig
        except Exception as e:
            st.warning(f"Zigzag error: {e}")

        try: 
            musinsa = ms(keyword)
            for r in musinsa:
                r["source"] = "Musinsa"
            results += musinsa
        except Exception as e:
            st.warning(f"Musinsa error: {e}")

    if not results:
        st.error("No results found.")
    else:
        st.success(f"Found {len(results)} total results!")
        for r in results:
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    if r.get("img"):
                        st.image(r["img"], width=120)
                with cols[1]:
                    st.markdown(f"**{r.get('name')}**")
                    st.markdown(f"🛍️ {r.get('source')} | 💰 {r.get('price')}원")
                    st.markdown(f"[View Product]({r.get('url')})")
                st.divider()
