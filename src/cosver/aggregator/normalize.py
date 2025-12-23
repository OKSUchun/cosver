import re
from typing import Optional, Tuple


# 1. 브랜드 정규화
BRAND_ALIAS = {
    "헤라": "HERA",
    "HERA": "HERA",
    "hera": "HERA",
    # 필요하면 계속 추가
}


def normalize_brand(raw_brand: str) -> str:
    """
    브랜드명을 통일한다.
    - 공백 제거, 대소문자 정리
    - alias 매핑 테이블을 통해 대표 브랜드명으로 변환
    """
    if raw_brand is None:
        return ""

    s = raw_brand.strip()
    # 괄호 안 영문이 있는 경우: "헤라(HERA)" -> "헤라"
    s = re.sub(r"\(.*?\)", "", s).strip()

    # alias 매핑
    if s in BRAND_ALIAS:
        return BRAND_ALIAS[s]

    # alias에 없으면 대문자로 통일
    return s.upper()


# 2. 상품 타입(단품/리필/미니/세트) 판별
def detect_product_type(name: str) -> str:
    """
    상품명에서 리필/미니/세트 여부를 간단히 판별한다.
    - 리필: REFILL
    - 미니/미니어처: MINI
    - 기획세트: SPECIAL_SET (다른 상품으로 구분)
    - 세트/2개입/x2 등: SET{n} (기본은 SET2)
    - 아무것도 아니면 BASE
    """
    lower = name.lower()

    # 리필
    if "리필" in name:
        return "REFILL"

    # 미니/미니어처
    if "미니어처" in name or "미니" in name:
        return "MINI"

    # 기획세트는 별도 상품으로 구분
    if "기획" in name or "기획세트" in name:
        return "SPECIAL_SET"

    # 일반 세트
    if "세트" in name:
        # 2개입, 3개입, x2, x3 등에서 개수 추출
        m = re.search(r"(\d+)\s*(개|개입|ea|EA|X|x|\*)", name)
        if m:
            n = m.group(1)
            return f"SET{n}"
        return "SET2"  # 기본 세트는 2개 세트라고 가정(초안)

    return "BASE"


# 3. 용량 추출 (30ml, 15 g, 0.5g, 2개입 등)
VOLUME_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(ml|mL|ML|g|G|개입|EA|ea)")


def parse_volume(raw_name: str) -> Tuple[str, Optional[float], Optional[str]]:
    """
    상품명에서 용량 정보를 추출하고, 나머지 텍스트를 반환한다.
    - 예: "헤라 블랙쿠션 15g 리필" ->
        clean_name="헤라 블랙쿠션 리필", volume=15.0, unit="g"
    - 못 찾으면 volume=None, unit=None
    """
    if raw_name is None:
        return "", None, None

    name = raw_name

    m = VOLUME_PATTERN.search(name)
    if not m:
        return name.strip(), None, None

    vol = float(m.group(1))
    unit = m.group(2).lower()

    # 텍스트에서 이 부분 제거
    start, end = m.span()
    cleaned = (name[:start] + name[end:]).strip()

    return cleaned, vol, unit


# 4. 불필요 태그/수식어 제거 (상품명 정규화)
REMOVE_TAGS = [
    r"\[기획\]",
    r"\[공식몰\]",
    r"\[단독\]",
    r"\[한정\]",
    r"\[온라인단독\]",
]

REMOVE_WORDS = [
    "정품",
    "본품",
    "미니어처",
    "미니",
    "증정",
    "사은품",
    "공식몰",
]


def normalize_product_name(raw_name: str) -> str:
    """
    상품명에서:
    - [기획], [공식몰], [단독] 등 태그 제거
    - 정품, 본품, 미니어처 등 불필요 수식어 제거
    - 공백 정리
    """
    if raw_name is None:
        return ""

    name = raw_name

    # 태그 제거
    for pattern in REMOVE_TAGS:
        name = re.sub(pattern, "", name)

    # 괄호 안에 들어간 '기획세트' 같은 태그 제거(너무 공격적이면 나중에 완화)
    name = re.sub(r"\((기획세트|단독|온라인단독|한정)\)", "", name)

    # 불필요 단어 제거
    for w in REMOVE_WORDS:
        name = name.replace(w, "")

    # 다중 공백 정리
    name = re.sub(r"\s+", " ", name).strip()

    return name


# 5. 최종 SKU 키 생성
def make_sku_key(
    raw_brand: str,
    raw_name: str,
    volume_tolerance: float = 0.05,  # ±5%
) -> str:
    """
    1. 브랜드 정규화
    2. 상품명에서 용량 추출 + 정규화
    3. 상품 타입(단품/리필/세트/미니) 판별
    4. 기획세트는 별도 상품으로 구분
    5. SKU 키 문자열 생성

    volume_tolerance는 지금은 크게 쓰지 않고,
    나중에 '비슷한 용량끼리 묶기' 로직에 활용 가능.
    """
    brand = normalize_brand(raw_brand)

    # 용량 먼저 뽑고, 남은 텍스트를 상품명으로 사용
    name_without_vol, volume, unit = parse_volume(raw_name)

    # 상품명 정규화
    normalized_name = normalize_product_name(name_without_vol)

    # 타입 판별 (기획세트는 이미 SPECIAL_SET으로 구분됨)
    p_type = detect_product_type(raw_name)

    # 볼륨이 없는 경우 fallback
    vol_str = (
        "" if volume is None else str(int(volume) if volume.is_integer() else volume)
    )
    unit_str = "" if unit is None else unit

    key_parts = [brand, normalized_name]

    if vol_str:
        key_parts.append(vol_str)
    if unit_str:
        key_parts.append(unit_str)

    key_parts.append(p_type)

    # 빈 값은 제거하고 '|'로 join
    key = "|".join([p for p in key_parts if p])

    return key
