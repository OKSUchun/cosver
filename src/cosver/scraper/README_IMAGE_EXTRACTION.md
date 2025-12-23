# Musinsa와 OliveYoung 이미지 추출 방법

## 개요

Musinsa와 OliveYoung은 JavaScript로 동적 로딩되는 사이트이기 때문에 일반적인 BeautifulSoup 방식으로는 이미지를 추출하기 어렵습니다. 대신 각 플랫폼의 API를 사용하여 이미지를 추출합니다.

## 구현 방법

### 1. Musinsa 이미지 추출

Musinsa는 상품 상세 정보를 제공하는 API를 사용합니다:

```python
from src.scraper.get_product_images import get_musinsa_product_images

product_url = "https://www.musinsa.com/products/5619064"
images = get_musinsa_product_images(product_url)
print(images)  # 이미지 URL 리스트
```

**API 엔드포인트:**
- `https://api.musinsa.com/api2/dp/v1/goods/{product_id}`

**이미지 URL 위치:**
- `data.goodsImages[].imageUrl`
- `data.thumbnailImageUrl`
- `data.goodsImageUrl`

### 2. OliveYoung 이미지 추출

OliveYoung은 상품 상세 정보를 제공하는 AJAX API를 사용합니다:

```python
from src.scraper.get_product_images import get_oliveyoung_product_images

product_url = "https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000202777"
images = get_oliveyoung_product_images(product_url)
print(images)  # 이미지 URL 리스트
```

**API 엔드포인트:**
- `https://www.oliveyoung.co.kr/store/goods/getGoodsDetailAjax.do`
- POST 요청, `goodsNo` 파라미터 필요

**이미지 URL 위치:**
- API 응답의 JSON 구조에서 `image`, `img`, `photo` 키워드가 포함된 필드
- HTML 응답인 경우 BeautifulSoup으로 파싱

### 3. 자동 플랫폼 감지

URL을 입력하면 자동으로 플랫폼을 감지하여 적절한 함수를 호출합니다:

```python
from src.scraper.get_product_images import get_product_images

# Musinsa URL
images1 = get_product_images("https://www.musinsa.com/products/5619064")

# OliveYoung URL
images2 = get_product_images("https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000202777")
```

## 사용 예시

### CSV 파일에서 이미지 다운로드

기존 `download_images_from_csv.py` 스크립트가 자동으로 Musinsa와 OliveYoung을 감지하여 전용 함수를 사용합니다:

```bash
python3 tests/download_images_from_csv.py \
  --csv tests/scraper_data.csv \
  --output downloaded_images \
  --start-row 2 \
  --end-row 67
```

### 직접 사용

```python
import sys
from pathlib import Path

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'scraper'))

from get_product_images import get_product_images

# Musinsa
musinsa_url = "https://www.musinsa.com/products/5619064"
musinsa_images = get_product_images(musinsa_url)
print(f"Musinsa 이미지: {len(musinsa_images)}개")
for img in musinsa_images:
    print(f"  - {img}")

# OliveYoung
oliveyoung_url = "https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000202777"
oliveyoung_images = get_product_images(oliveyoung_url)
print(f"OliveYoung 이미지: {len(oliveyoung_images)}개")
for img in oliveyoung_images:
    print(f"  - {img}")
```

## 주의사항

1. **API 변경**: 플랫폼의 API 구조가 변경될 수 있으므로 주기적으로 확인이 필요합니다.
2. **Rate Limiting**: 너무 많은 요청을 보내면 차단될 수 있으므로 적절한 지연 시간을 설정하세요.
3. **에러 처리**: 네트워크 오류나 API 변경 시 빈 리스트를 반환하므로 적절한 에러 처리가 필요합니다.

## 문제 해결

### 이미지를 찾을 수 없는 경우

1. **API 응답 구조 확인**: 실제 API 응답을 확인하여 이미지 URL이 포함된 필드를 찾아야 합니다.
2. **인증 필요**: 일부 API는 인증이 필요할 수 있습니다.
3. **User-Agent**: 적절한 User-Agent 헤더가 필요할 수 있습니다.

### API 응답 구조 확인 방법

```python
import requests
import json

# Musinsa
url = "https://api.musinsa.com/api2/dp/v1/goods/5619064"
response = requests.get(url)
print(json.dumps(response.json(), indent=2, ensure_ascii=False))

# OliveYoung
url = "https://www.oliveyoung.co.kr/store/goods/getGoodsDetailAjax.do"
data = {"goodsNo": "A000000202777"}
response = requests.post(url, data=data)
print(response.text)  # JSON 또는 HTML
```

## 향후 개선 사항

1. **캐싱**: 같은 상품의 이미지를 여러 번 요청하지 않도록 캐싱 추가
2. **재시도 로직**: 네트워크 오류 시 자동 재시도
3. **이미지 품질 선택**: 썸네일/원본 이미지 선택 옵션
4. **Playwright 지원**: API가 작동하지 않는 경우 Playwright로 폴백

