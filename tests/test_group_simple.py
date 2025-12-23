"""
간단한 테스트 스크립트 - pytest 없이도 실행 가능
"""
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from cosver.frontend.utils import group_similar_products


def test_basic():
    """기본 그룹핑 테스트"""
    print("🧪 테스트 1: 기본 그룹핑")
    products = [
        {"name": "헤라 센슈얼 누드 글로스", "price": 35000, "source": "OliveYoung"},
        {"name": "헤라 센슈얼 누드 글로스 3.5g", "price": 35000, "source": "Ably"},
        {"name": "완전히 다른 제품", "price": 20000, "source": "Zigzag"},
    ]
    
    groups = group_similar_products(products, threshold=0.7)
    
    print(f"  입력: {len(products)}개 제품")
    print(f"  출력: {len(groups)}개 그룹")
    for i, group in enumerate(groups, 1):
        print(f"    그룹 {i}: {len(group)}개 제품")
        for item in group:
            print(f"      - {item['name']} ({item['source']})")
    
    assert len(groups) == 2, f"예상: 2개 그룹, 실제: {len(groups)}개"
    print("  ✅ 통과\n")


def test_exact_match():
    """정확히 일치하는 제품 테스트"""
    print("🧪 테스트 2: 정확히 일치하는 제품")
    products = [
        {"name": "헤라 센슈얼 누드 글로스", "price": 35000, "source": "OliveYoung"},
        {"name": "헤라 센슈얼 누드 글로스", "price": 35000, "source": "Ably"},
        {"name": "헤라 센슈얼 누드 글로스", "price": 35000, "source": "Zigzag"},
    ]
    
    groups = group_similar_products(products, threshold=0.7)
    
    print(f"  입력: {len(products)}개 제품 (모두 동일한 이름)")
    print(f"  출력: {len(groups)}개 그룹")
    
    assert len(groups) == 1, f"예상: 1개 그룹, 실제: {len(groups)}개"
    assert len(groups[0]) == 3, f"예상: 그룹에 3개 제품, 실제: {len(groups[0])}개"
    print("  ✅ 통과\n")


def test_empty():
    """빈 리스트 테스트"""
    print("🧪 테스트 3: 빈 리스트")
    products = []
    
    groups = group_similar_products(products)
    
    print(f"  입력: {len(products)}개 제품")
    print(f"  출력: {len(groups)}개 그룹")
    
    assert len(groups) == 0, f"예상: 0개 그룹, 실제: {len(groups)}개"
    print("  ✅ 통과\n")


def test_single_item():
    """단일 아이템 테스트"""
    print("🧪 테스트 4: 단일 아이템")
    products = [
        {"name": "헤라 센슈얼 누드 글로스", "price": 35000, "source": "OliveYoung"},
    ]
    
    groups = group_similar_products(products)
    
    print(f"  입력: {len(products)}개 제품")
    print(f"  출력: {len(groups)}개 그룹")
    
    assert len(groups) == 1, f"예상: 1개 그룹, 실제: {len(groups)}개"
    assert len(groups[0]) == 1, f"예상: 그룹에 1개 제품, 실제: {len(groups[0])}개"
    print("  ✅ 통과\n")


def main():
    """모든 테스트 실행"""
    print("=" * 50)
    print("group_similar_products 함수 테스트 시작")
    print("=" * 50 + "\n")
    
    try:
        test_basic()
        test_exact_match()
        test_empty()
        test_single_item()
        
        print("=" * 50)
        print("✅ 모든 테스트 통과!")
        print("=" * 50)
        return 0
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

