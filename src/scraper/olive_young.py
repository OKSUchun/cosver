from urllib.parse import quote

import requests


def search_product(keyword: str):
    url = "https://www.oliveyoung.co.kr/store/search/NewMainSearchApi.do"

    encoded_kw = quote(keyword)
    print(encoded_kw)

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/141.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Origin": "https://www.oliveyoung.co.kr",
        "Referer": f"https://www.oliveyoung.co.kr/store/search/getSearchMain.do?query={encoded_kw}",
    }

    data = {
        "query": keyword,
        "reQuery": "",
        "rt": "",
        "collection": "OLIVE_GOODS,OLIVE_PLAN,OLIVE_EVENT,OLIVE_BRAND,OLIVE_QUICK_LINK",
        "listnum": "24",
        "startCount": "0",
        "sort": "RANK/DESC",
        "goods_sort": "WEIGHT/DESC,RANK/DESC",
        "typeChk": "thum",
        "onlyOneBrand": "",
        "quickYn": "N",
        "displayMediaTypes": "02",
    }

    response = requests.post(url, headers=headers, data=data, timeout=10)
    print(response)

    if response.status_code != 200:
        raise Exception(f"❌ Request failed ({response.status_code})")

    res_json = response.json()

    # 주요 상품 리스트는 res_json["result"]["goods_list"] 에 있음
    items = res_json.get("result", {}).get("goods_list", [])
    results = []

    for item in items:
        results.append(
            {
                "platform": "OliveYoung",
                "name": item.get("goodsNm"),
                "price": item.get("salePrc"),
                "original_price": item.get("dispPrc"),
                "brand": item.get("brandNm"),
                "url": f"https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo={item.get('goodsNo')}",
            }
        )

    return results


if __name__ == "__main__":
    keyword = "헤라 란제리"
    data = search_product(keyword)
    print(data)
    for d in data[:5]:
        print(d)
