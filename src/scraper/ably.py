import requests

import requests
from urllib.parse import quote


def search_product(keyword: str):
    # 1️⃣ 기본 URL & 쿼리
    base_url = "https://api.a-bly.com/api/v2/screens/SEARCH_RESULT/"
    encoded_kw = quote(keyword)

    params = {"query": keyword, "search_type": "DIRECT"}

    # 2️⃣ 헤더 설정
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "origin": "https://m.a-bly.com",
        "priority": "u=1, i",
        "referer": "https://m.a-bly.com/",
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
        "x-anonymous-token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhbm9ueW1vdXNfaWQiOiI2NTQ4NzEwODIiLCJpYXQiOjE3NjI1MDcxMTl9.OedYhgSHrVaXLo5H7yW51gRG3pDFf4rSB63aoJHN4uk",
        "x-app-version": "0.1.0",
        "x-device-id": "85a28751-9c6a-4972-bd12-aab5282ce6ee",
        "x-device-type": "PCWeb",
        "x-web-type": "Web",
    }

    # 3️⃣ 요청 실행
    response = requests.get(base_url, headers=headers, params=params, timeout=10)

    if response.status_code != 200:
        raise Exception(f"❌ Request failed ({response.status_code})")

    res_json = response.json()

    # 4️⃣ 데이터 파싱
    # 구조는 API마다 다르지만, Ably는 대부분 data -> sections[0] -> items 형태
    components = res_json.get('components')
    items = []
    for component in components:
        if component.get('component_id') == 41:
            entities =component.get('entity').get('item_list')
            for entity in entities:
                items.append(
                    {
                        "platform": "Ably",
                        "name": entity.get('item').get('name'),
                        "brand": entity.get('item').get('market_name'),
                        "price": entity.get('item').get('price'),
                        "url": entity.get('item').get('remote_deeplink'),
                    }
                )

    return items


if __name__ == "__main__":
    keyword = "센슈얼 누드 글로스"
    results = search_ably_api(keyword)

    print(f"🔍 Found {len(results)} items")
    for r in results[:5]:
        print(r)
