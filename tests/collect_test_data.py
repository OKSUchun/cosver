"""
Scraper에서 실제 데이터를 수집하여 CSV 파일로 저장하는 스크립트
"""
import csv
import sys
from datetime import datetime
from pathlib import Path

from src.scraper.ably import search_product as ab
from src.scraper.musinsa import search_product as ms
from src.scraper.oliveyoung_playwright import search_product as oy
from src.scraper.zigzag import search_product as zz


def collect_products_to_csv(keywords: list[str], output_file: str = "tests/scraper_data.csv"):
    """
    여러 키워드로 scraper를 실행하고 결과를 CSV 파일로 저장
    
    Args:
        keywords: 검색할 키워드 리스트
        output_file: 저장할 CSV 파일 경로
    """
    # CSV 파일 경로 설정
    csv_path = Path(output_file)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Scraper 설정
    scrapers = [
        (oy, "OliveYoung"),
        (ab, "Ably"),
        (zz, "Zigzag"),
        (ms, "Musinsa"),
    ]
    
    all_products = []
    
    print(f"🔍 {len(keywords)}개 키워드로 데이터 수집 시작...")
    
    for keyword in keywords:
        print(f"\n📝 검색어: {keyword}")
        
        for scraper_func, platform_name in scrapers:
            try:
                print(f"  - {platform_name} 검색 중...", end=" ")
                results = scraper_func(keyword)
                
                # source 필드 추가
                for result in results:
                    result["source"] = platform_name
                    result["search_keyword"] = keyword  # 검색 키워드도 저장
                
                all_products.extend(results)
                print(f"✅ {len(results)}개 상품 발견")
                
            except Exception as e:
                print(f"❌ 오류: {e}")
                continue
    
    # CSV로 저장
    if not all_products:
        print("\n❌ 수집된 데이터가 없습니다.")
        return
    
    # CSV 필드명 결정 (모든 상품에 공통으로 있는 필드 + 선택적 필드)
    fieldnames = set()
    for product in all_products:
        fieldnames.update(product.keys())
    
    # 필드 순서 정렬 (중요한 필드 먼저)
    priority_fields = ["name", "brand", "price", "source", "url", "search_keyword"]
    ordered_fields = [f for f in priority_fields if f in fieldnames]
    ordered_fields.extend(sorted(fieldnames - set(priority_fields)))
    
    print(f"\n💾 {len(all_products)}개 상품을 CSV 파일로 저장 중...")
    print(f"   파일 경로: {csv_path.absolute()}")
    
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=ordered_fields)
        writer.writeheader()
        writer.writerows(all_products)
    
    print(f"✅ 저장 완료!")
    print(f"   총 {len(all_products)}개 상품")
    print(f"   플랫폼별: {', '.join(set(p['source'] for p in all_products))}")
    
    return csv_path


def main():
    """메인 함수"""
    # 기본 검색 키워드 (화장품 관련)
    default_keywords = [
        "헤라 블랙쿠션",
        "헤라 센슈얼 누드 글로스",
        "헤라 센슈얼 파우더매트 리퀴드",
        "라네즈 워터뱅크 하이드로 크림",
        "설화수 자음생크림",
    ]
    
    # 커맨드라인 인자로 키워드 받기
    if len(sys.argv) > 1:
        keywords = sys.argv[1:]
    else:
        keywords = default_keywords
        print("💡 사용법: python collect_test_data.py [키워드1] [키워드2] ...")
        print(f"💡 기본 키워드로 실행: {', '.join(keywords)}\n")
    
    output_file = "tests/scraper_data.csv"
    
    try:
        collect_products_to_csv(keywords, output_file)
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

