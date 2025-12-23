"""
CSV 파일의 shop URL을 방문하여 이미지를 다운로드하는 스크립트

scraper_data.csv의 2행부터 67행까지의 shop URL을 방문하여 이미지를 다운로드하고,
search_keyword 별로 디렉토리를 생성합니다.
"""
import csv
import os
import re
import time
import sys
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from typing import Optional, List

# 상품 이미지 추출 모듈 import
sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'scraper'))
try:
    from get_product_images import get_product_images, get_musinsa_product_images, get_oliveyoung_product_images
    PRODUCT_IMAGE_MODULE_AVAILABLE = True
except ImportError:
    PRODUCT_IMAGE_MODULE_AVAILABLE = False
    print("⚠️  get_product_images 모듈을 찾을 수 없습니다. 기본 방법으로 진행합니다.")


def sanitize_filename(filename: str) -> str:
    """파일명에 사용할 수 없는 문자를 제거합니다."""
    # 파일명에 사용할 수 없는 문자 제거
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 공백을 언더스코어로 변경
    filename = re.sub(r'\s+', '_', filename)
    return filename


def sanitize_directory_name(name: str) -> str:
    """디렉토리명에 사용할 수 없는 문자를 제거합니다."""
    return sanitize_filename(name)


def get_image_urls_from_page(url: str, timeout: int = 10) -> List[str]:
    """
    웹 페이지에서 이미지 URL을 추출합니다.
    
    Args:
        url: 웹 페이지 URL
        timeout: 요청 타임아웃 (초)
    
    Returns:
        이미지 URL 리스트
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        image_urls = []
        
        # img 태그에서 이미지 URL 추출
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src:
                # 상대 경로를 절대 경로로 변환
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    parsed_url = urlparse(url)
                    src = f"{parsed_url.scheme}://{parsed_url.netloc}{src}"
                elif not src.startswith('http'):
                    parsed_url = urlparse(url)
                    src = f"{parsed_url.scheme}://{parsed_url.netloc}/{src}"
                
                image_urls.append(src)
        
        # 배경 이미지로 사용된 경우도 찾기
        for element in soup.find_all(style=True):
            style = element.get('style', '')
            bg_image_match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
            if bg_image_match:
                src = bg_image_match.group(1)
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    parsed_url = urlparse(url)
                    src = f"{parsed_url.scheme}://{parsed_url.netloc}{src}"
                image_urls.append(src)
        
        return list(set(image_urls))  # 중복 제거
    except Exception as e:
        print(f"⚠️  페이지에서 이미지 추출 실패 {url}: {e}")
        return []


def download_image(image_url: str, output_path: Path, timeout: int = 30) -> bool:
    """
    이미지를 다운로드합니다.
    
    Args:
        image_url: 이미지 URL
        output_path: 저장할 경로
        timeout: 요청 타임아웃 (초)
    
    Returns:
        성공 여부
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': image_url
        }
        response = requests.get(image_url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Content-Type 확인
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            print(f"⚠️  이미지가 아닌 파일: {image_url} (Content-Type: {content_type})")
            return False
        
        # 파일 확장자 결정
        ext = '.jpg'
        if 'jpeg' in content_type:
            ext = '.jpg'
        elif 'png' in content_type:
            ext = '.png'
        elif 'gif' in content_type:
            ext = '.gif'
        elif 'webp' in content_type:
            ext = '.webp'
        else:
            # URL에서 확장자 추출
            parsed = urlparse(image_url)
            path_ext = Path(parsed.path).suffix.lower()
            if path_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                ext = path_ext
        
        # 파일명 생성
        if not output_path.suffix:
            output_path = output_path.with_suffix(ext)
        
        # 디렉토리 생성
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 이미지 다운로드
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except Exception as e:
        print(f"⚠️  이미지 다운로드 실패 {image_url}: {e}")
        return False


def download_images_from_csv(
    csv_path: str,
    output_base_dir: str = "downloaded_images",
    start_row: int = 2,
    end_row: int = 67,
    delay: float = 1.0
):
    """
    CSV 파일의 shop URL을 방문하여 이미지를 다운로드합니다.
    
    Args:
        csv_path: CSV 파일 경로
        output_base_dir: 이미지를 저장할 기본 디렉토리
        start_row: 시작 행 (1-based, 헤더 포함)
        end_row: 끝 행 (1-based, 헤더 포함)
        delay: 요청 간 지연 시간 (초)
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        print(f"❌ CSV 파일을 찾을 수 없습니다: {csv_path}")
        return
    
    output_base = Path(output_base_dir)
    output_base.mkdir(parents=True, exist_ok=True)
    
    print(f"📂 CSV 파일 읽기: {csv_path}")
    print(f"📥 이미지 저장 위치: {output_base}")
    print(f"📊 처리 범위: {start_row}행 ~ {end_row}행\n")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    total_rows = len(rows)
    if end_row > total_rows:
        end_row = total_rows
        print(f"⚠️  끝 행이 파일 크기를 초과하여 {total_rows}행으로 조정했습니다.\n")
    
    # 처리할 행 범위 (0-based 인덱스)
    start_idx = start_row - 2  # 헤더 제외하고 0-based로 변환
    end_idx = end_row - 1  # 헤더 제외하고 0-based로 변환
    
    success_count = 0
    fail_count = 0
    
    for idx in range(start_idx, end_idx + 1):
        if idx >= len(rows):
            break
        
        row = rows[idx]
        # url 컬럼을 우선 사용, 없으면 shop 컬럼 확인
        shop_url = row.get('url', '').strip() or row.get('shop', '').strip()
        search_keyword = row.get('search_keyword', '').strip()
        name = row.get('name', '').strip()
        img_url = row.get('img', '').strip()
        
        if not shop_url:
            print(f"⏭️  [{idx + 2}행] URL이 없어 건너뜁니다.")
            continue
        
        if not search_keyword:
            search_keyword = "unknown"
        
        # 디렉토리 생성
        keyword_dir = sanitize_directory_name(search_keyword)
        output_dir = output_base / keyword_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n[{idx + 2}행] {name[:50]}...")
        print(f"  🔍 검색어: {search_keyword}")
        print(f"  🌐 URL: {shop_url}")
        
        # 1. img 컬럼에 이미지 URL이 있으면 우선 사용
        if img_url and img_url.startswith('http'):
            print(f"  📷 img 컬럼에서 이미지 URL 발견")
            filename = sanitize_filename(name) if name else f"image_{idx + 2}"
            output_path = output_dir / f"{filename}_{idx + 2}.jpg"
            
            if download_image(img_url, output_path):
                print(f"  ✅ 다운로드 완료: {output_path.name}")
                success_count += 1
            else:
                print(f"  ❌ 다운로드 실패")
                fail_count += 1
        else:
            # 2. shop URL을 방문하여 이미지 찾기
            print(f"  🔍 페이지에서 이미지 찾는 중...")
            
            # Musinsa나 OliveYoung인 경우 전용 함수 사용
            if PRODUCT_IMAGE_MODULE_AVAILABLE:
                if 'musinsa.com' in shop_url:
                    print(f"  🏪 Musinsa 전용 API 사용")
                    image_urls = get_musinsa_product_images(shop_url)
                elif 'oliveyoung.co.kr' in shop_url:
                    print(f"  🏪 OliveYoung 전용 API 사용")
                    image_urls = get_oliveyoung_product_images(shop_url)
                else:
                    image_urls = get_image_urls_from_page(shop_url)
            else:
                image_urls = get_image_urls_from_page(shop_url)
            
            if not image_urls:
                print(f"  ⚠️  이미지를 찾을 수 없습니다.")
                fail_count += 1
            else:
                # 상품 이미지로 보이는 것들 필터링 (큰 이미지 우선)
                # 일반적으로 상품 이미지는 특정 패턴을 가짐
                product_images = []
                for img_url in image_urls:
                    # 상품 이미지로 보이는 URL 필터링
                    if any(keyword in img_url.lower() for keyword in ['product', 'goods', 'item', 'detail', 'main', 'cover']):
                        product_images.append(img_url)
                    elif 'jpg' in img_url.lower() or 'jpeg' in img_url.lower() or 'png' in img_url.lower():
                        # 큰 이미지일 가능성이 높음 (파일명에 숫자가 많은 경우)
                        if len(re.findall(r'\d+', img_url)) > 2:
                            product_images.append(img_url)
                
                # 필터링된 이미지가 없으면 모든 이미지 사용
                if not product_images:
                    product_images = image_urls[:5]  # 최대 5개만
                else:
                    product_images = product_images[:5]  # 최대 5개만
                
                print(f"  📷 {len(product_images)}개의 이미지 발견")
                
                downloaded = False
                for img_idx, img_url in enumerate(product_images):
                    filename = sanitize_filename(name) if name else f"image_{idx + 2}"
                    if len(product_images) > 1:
                        filename = f"{filename}_{img_idx + 1}"
                    output_path = output_dir / f"{filename}_{idx + 2}.jpg"
                    
                    if download_image(img_url, output_path):
                        print(f"  ✅ 다운로드 완료 [{img_idx + 1}/{len(product_images)}]: {output_path.name}")
                        downloaded = True
                        success_count += 1
                        break  # 첫 번째 성공한 이미지만 저장
                
                if not downloaded:
                    print(f"  ❌ 이미지 다운로드 실패")
                    fail_count += 1
        
        # 요청 간 지연
        if idx < end_idx:
            time.sleep(delay)
    
    print("\n" + "=" * 70)
    print("다운로드 완료")
    print("=" * 70)
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {fail_count}개")
    print(f"📂 저장 위치: {output_base}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CSV 파일의 shop URL에서 이미지를 다운로드합니다.")
    parser.add_argument(
        "--csv",
        type=str,
        default="tests/scraper_data.csv",
        help="CSV 파일 경로",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="downloaded_images",
        help="이미지를 저장할 기본 디렉토리",
    )
    parser.add_argument(
        "--start-row",
        type=int,
        default=2,
        help="시작 행 (1-based, 헤더 포함)",
    )
    parser.add_argument(
        "--end-row",
        type=int,
        default=67,
        help="끝 행 (1-based, 헤더 포함)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="요청 간 지연 시간 (초)",
    )
    
    args = parser.parse_args()
    
    download_images_from_csv(
        csv_path=args.csv,
        output_base_dir=args.output,
        start_row=args.start_row,
        end_row=args.end_row,
        delay=args.delay,
    )

