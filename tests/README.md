# 테스트 실행 방법

## `group_similar_products` 함수 테스트

`group_similar_products` 함수를 독립적으로 테스트할 수 있습니다.

### 방법 1: pytest 사용 (권장)

```bash
# pytest 설치 (아직 설치되지 않은 경우)
pip install pytest

# 테스트 실행
pytest tests/test_group_similar_products.py -v

# 또는 프로젝트 루트에서
python -m pytest tests/test_group_similar_products.py -v
```

### 방법 2: Python으로 직접 실행

```bash
# 테스트 파일을 직접 실행
python tests/test_group_similar_products.py
```

### 방법 3: Python 인터랙티브 모드에서 테스트

```python
from src.frontend.utils import group_similar_products

# 테스트 데이터
products = [
    {"name": "헤라 센슈얼 누드 글로스", "price": 35000, "source": "OliveYoung"},
    {"name": "헤라 센슈얼 누드 글로스 3.5g", "price": 35000, "source": "Ably"},
    {"name": "[OY단독컬러/NEW 홀리데이] 헤라 센슈얼 누드 글로스", "price": 20000, "source": "Zigzag"},
]

# 함수 실행
groups = group_similar_products(products, threshold=0.7)

# 결과 확인
print(f"총 {len(products)}개 제품이 {len(groups)}개 그룹으로 분류되었습니다.")
for i, group in enumerate(groups, 1):
    print(f"\n그룹 {i}:")
    for item in group:
        print(f"  - {item['name']} ({item['source']})")
```

## 테스트 케이스

현재 포함된 테스트:
- ✅ 기본 그룹핑 기능
- ✅ 정확히 일치하는 제품 그룹핑
- ✅ 유사도가 낮은 제품 분리
- ✅ 빈 리스트 처리
- ✅ 단일 아이템 처리
- ✅ threshold 조정 효과
- ✅ 여러 그룹 동시 처리

