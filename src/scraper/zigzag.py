import requests
import json


def search_product(keyword: str):
    """Zigzag 상품 검색 API"""
    url = "https://api.zigzag.kr/api/2/graphql/GetSearchResult"

    # 🧩 GraphQL Query Payload 구성
    payload = {
        "query": """
        query GetSearchResult($input: SearchResultInput!) {
          search_result(input: $input) {
            total_count
            searched_keyword
            ui_item_list {
              __typename
              ... on UxGoodsCardItem {
                title
                product_url
                final_price
                max_price
                shop_name
                image_url
              }
            }
          }
        }
        """,
        "variables": {
            "input": {
                "enable_guided_keyword_search": True,
                "initial": True,
                "page_id": "srp_item",
                "q": keyword,
                "filter_id_list": ["205"],
                "filter_list": [],
                "sub_filter_id_list": [],
                "after": None,
            }
        },
    }

    # 🧾 Headers
    headers = {
        "accept": "*/*",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/json",
        "origin": "https://zigzag.kr",
        "priority": "u=1, i",
        "referer": "https://zigzag.kr/",
        "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/141.0.0.0 Safari/537.36"
        ),
    }

    # 🧁 쿠키 (optional: 로그인이 필요한 데이터일 경우)
    cookies = {
        # connect.sid 등은 로그인 세션 기반이라 변경될 수 있음.
        # 필요 시 브라우저에서 복사한 값으로 교체하세요.
        "ZIGZAGUUID": "a2755029-99db-4202-afd8-3516b63fe23b.RujtZM9r%2Bz1lWs9qg9L6ic7LiANJDM3zYdyuolSqWZY",
    }

    # 🚀 요청
    response = requests.post(
        url, headers=headers, cookies=cookies, json=payload, timeout=15
    )
    print(f"Response Status: {response.status_code}")

    if response.status_code != 200:
        raise Exception(f"❌ Request failed ({response.status_code})")

    data = response.json()
    # print(json.dumps(data, indent=2, ensure_ascii=False))  # 응답 구조 확인용

    # 📦 상품 정보 파싱
    items = []
    ui_items = data.get("data", {}).get("search_result", {}).get("ui_item_list", [])

    for item in ui_items:
        if item.get("__typename") == "UxGoodsCardItem":
            items.append(
                {
                    "platform": "Zigzag",
                    "name": item.get("title"),
                    "shop": item.get("shop_name"),
                    "price": item.get("final_price"),
                    "original_price": item.get("max_price"),
                    "url": item.get("product_url"),
                    "img": item.get("image_url"),
                }
            )

    return items


if __name__ == "__main__":
    keyword = "헤라 센슈얼 누드 글로스"
    results = search_product(keyword)

    print(f"🔍 Found {len(results)} items")
    for r in results[:5]:
        print(r)
