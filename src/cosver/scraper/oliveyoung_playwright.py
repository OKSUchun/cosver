# olive_search.py
# Usage: python olive_search.py "키워드"
import sys

from playwright.sync_api import sync_playwright


def search_product(keyword, headful=False):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headful, args=["--start-maximized"])
        # create context with default viewport None to use full window
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # 1) 먼저 검색 메인 페이지로 가서 Cloudflare 검사/세션 쿠키를 통과시킨다
        referer_url = f"https://www.oliveyoung.co.kr/store/search/getSearchMain.do?query={keyword}"
        print(f"Opening referer page: {referer_url}")
        
        # Increase timeout and use 'load' state which is usually more reliable than 'networkidle' on servers
        page.goto(referer_url, wait_until="load", timeout=30000)
        
        # Short wait for any potential redirects/JS execution to settle
        page.wait_for_timeout(2000) 

        # 2) 브라우저 컨텍스트(=JS + 쿠키 포함)에서 fetch로 POST 요청 실행
        print("Posting to API from browser context...")
        response_payload = page.evaluate(
            """async (kw) => {
                const url = 'https://www.oliveyoung.co.kr/store/search/NewMainSearchApi.do';
                const params = new URLSearchParams();
                params.append('query', kw);
                params.append('reQuery', '');
                params.append('rt', '');
                params.append('collection', 'OLIVE_GOODS,OLIVE_PLAN,OLIVE_EVENT,OLIVE_BRAND,OLIVE_QUICK_LINK');
                params.append('listnum', '24');
                params.append('startCount', '0');
                params.append('sort', 'RANK/DESC');
                params.append('goods_sort', 'WEIGHT/DESC,RANK/DESC');
                params.append('typeChk', 'thum');
                params.append('onlyOneBrand', '');
                params.append('quickYn', 'N');
                params.append('displayMediaTypes', '02');

                const resp = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json, text/javascript, */*; q=0.01'
                    },
                    body: params.toString(),
                    credentials: 'same-origin' // 중요: 브라우저 쿠키 전송
                });

                // 일부 경우 200이 아닌 리디렉션/HTML이 올 수 있으니 안전하게 처리
                const text = await resp.text();
                try {
                    return JSON.parse(text);
                } catch (e) {
                    return { __error_parse: true, status: resp.status, body_text: text.slice(0, 500) };
                }
            }""",
            keyword,
        )

        browser.close()

    if not isinstance(response_payload, dict):
        raise ValueError("Unexpected response from OliveYoung API: not a JSON object")

    if response_payload.get("__error_parse"):
        raise RuntimeError(f"Failed to parse OliveYoung API response: {response_payload}")

    goods = []
    for section in response_payload.get("Data", []):
        if section.get("CollName") != "OLIVE_GOODS":
            continue
        for item in section.get("Result", []):
            goods.append(
                {
                    "goods_no": item.get("GOODS_NO"),
                    "name": item.get("GOODS_NM"),
                    "brand": item.get("ONL_BRND_NM"),
                    "price": item.get("SALE_PRC") or item.get("NORM_PRC"),
                    "img": f"https://image.oliveyoung.co.kr/uploads/images/goods/{item.get('IMG_PATH_NM')}" if item.get("IMG_PATH_NM") else None,
                    "url": f"https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo={item.get('GOODS_NO')}&dispCatNo=1000001000200060002&trackingCd=Result_1",
                }
            )

    return goods


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python olive_search.py "키워드"')
        sys.exit(1)

    kw = sys.argv[1]
    try:
        items = search_product(
            kw, headful=True
        )  # headful=True 권장 (Cloudflare 통과 안정적)
    except Exception as exc:
        print(f"❌ Error: {exc}")
        sys.exit(1)

    if not items:
        print("No results found.")
    else:
        for item in items:
            print(item)
