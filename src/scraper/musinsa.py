import requests


def search_product(keyword: str, category: int = 104, limit: int = 10):
    """
    무신사 상품 검색 (공식 API 기반)
    :param keyword: 검색어 (예: '헤라 란제리')
    :param category: 카테고리 코드 (기본 104 = 여성의류)
    :param limit: 최대 출력 상품 수
    :return: [{name, price, brand, url}, ...]
    """
    url = "https://api.musinsa.com/api2/dp/v1/plp/goods"

    params = {
        "gf": "A",
        "category": category,
        "keyword": keyword,
        "caller": "CATEGORY",
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/141.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Origin": "https://www.musinsa.com",
        "Referer": "https://www.musinsa.com/",
    }

    response = requests.get(url, headers=headers, params=params, timeout=10)
    if response.status_code != 200:
        print(f"❌ HTTP Error {response.status_code}")
        return []

    res_json = response.json()
    goods_list = res_json.get("data", {}).get("list", [])
    # print(goods_list)
    results = []

    results = [
        {
            "platform": "musinsa",
            "name": g.get("goodsName"),
            "brand": g.get("brandName"),
            "price": g.get("price") or g.get("couponPrice"),
            "url": g.get("goodsLinkUrl"),
        }
        for g in goods_list[:limit]
    ]

    return results


if __name__ == "__main__":
    keyword = "헤라 란제리"
    data = search_product(keyword)
    print(data)
    for item in data[:5]:
        print(item)
