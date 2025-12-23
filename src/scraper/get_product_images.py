"""
Musinsa와 OliveYoung에서 상품 이미지를 추출하는 모듈
"""
import re
import requests
from typing import List, Optional
from urllib.parse import urlparse, parse_qs


def get_musinsa_product_images(product_url: str) -> List[str]:
    """
    Musinsa 상품 상세 페이지에서 이미지 URL을 추출합니다.
    
    Args:
        product_url: 상품 상세 페이지 URL (예: https://www.musinsa.com/products/5619064)
    
    Returns:
        이미지 URL 리스트
    """
    try:
        from bs4 import BeautifulSoup
        
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/141.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.musinsa.com/",
        }
        
        # 실제 페이지 가져오기
        response = requests.get(product_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"⚠️  Musinsa 페이지 요청 실패: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        image_urls = []
        
        # 1. script 태그에서 이미지 URL 찾기 (JSON 데이터)
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # JSON 데이터에서 이미지 URL 추출
                # image.msscdn.net 또는 image.musinsa.com 패턴
                img_patterns = [
                    r'https?://image\.msscdn\.net/[^\s"\'<>\)]+\.(?:jpg|jpeg|png|webp)',
                    r'https?://image\.musinsa\.com/[^\s"\'<>\)]+\.(?:jpg|jpeg|png|webp)',
                    r'"imageUrl"\s*:\s*"([^"]+)"',
                    r'"goodsImageUrl"\s*:\s*"([^"]+)"',
                    r'"thumbnailImageUrl"\s*:\s*"([^"]+)"',
                ]
                
                for pattern in img_patterns:
                    matches = re.findall(pattern, script.string, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0] if match[0] else match[1] if len(match) > 1 else ''
                        if match and match.startswith('http'):
                            image_urls.append(match)
        
        # 2. img 태그에서 이미지 찾기
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-original') or img.get('data-lazy-src')
            if src:
                if 'product' in src.lower() or 'goods' in src.lower() or 'image.msscdn.net' in src or 'image.musinsa.com' in src:
                    if not src.startswith('http'):
                        src = f"https://www.musinsa.com{src}" if src.startswith('/') else f"https://www.musinsa.com/{src}"
                    if src not in image_urls:
                        image_urls.append(src)
        
        # 3. data 속성에서 이미지 찾기
        for element in soup.find_all(attrs={'data-image': True}):
            img_url = element.get('data-image')
            if img_url and img_url.startswith('http') and img_url not in image_urls:
                image_urls.append(img_url)
        
        # 중복 제거 및 필터링
        image_urls = list(set(image_urls))
        # 상품 이미지로 보이는 것만 필터링
        filtered = []
        for url in image_urls:
            if any(keyword in url.lower() for keyword in ['product', 'goods', 'item', 'detail', 'msscdn', 'musinsa']):
                filtered.append(url)
        
        return filtered if filtered else image_urls[:10]  # 최대 10개
        
    except Exception as e:
        print(f"⚠️  Musinsa 이미지 추출 오류: {e}")
        return []


def get_oliveyoung_product_images(product_url: str) -> List[str]:
    """
    OliveYoung 상품 상세 페이지에서 이미지 URL을 추출합니다.
    
    Args:
        product_url: 상품 상세 페이지 URL
    
    Returns:
        이미지 URL 리스트
    """
    try:
        from bs4 import BeautifulSoup
        
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/141.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.oliveyoung.co.kr/",
        }
        
        # 실제 페이지 가져오기
        response = requests.get(product_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"⚠️  OliveYoung 페이지 요청 실패: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        image_urls = []
        
        # 1. script 태그에서 이미지 URL 찾기 (JSON 데이터)
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # JSON 데이터에서 이미지 URL 추출
                # oliveyoung.co.kr 또는 cdn 패턴
                img_patterns = [
                    r'https?://[^\s"\'<>\)]+oliveyoung[^\s"\'<>\)]+\.(?:jpg|jpeg|png|webp|gif)',
                    r'https?://[^\s"\'<>\)]+cdn[^\s"\'<>\)]+\.(?:jpg|jpeg|png|webp|gif)',
                    r'"goodsImageUrl"\s*:\s*"([^"]+)"',
                    r'"imageUrl"\s*:\s*"([^"]+)"',
                    r'"thumbnailUrl"\s*:\s*"([^"]+)"',
                    r'"goodsImg"\s*:\s*"([^"]+)"',
                ]
                
                for pattern in img_patterns:
                    matches = re.findall(pattern, script.string, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0] if match[0] else match[1] if len(match) > 1 else ''
                        if match and match.startswith('http'):
                            image_urls.append(match)
        
        # 2. img 태그에서 이미지 찾기
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-original') or img.get('data-lazy-src')
            if src:
                if 'goods' in src.lower() or 'product' in src.lower() or 'oliveyoung' in src.lower() or 'cdn' in src.lower():
                    if not src.startswith('http'):
                        src = f"https://www.oliveyoung.co.kr{src}" if src.startswith('/') else f"https://www.oliveyoung.co.kr/{src}"
                    if src not in image_urls:
                        image_urls.append(src)
        
        # 3. 배경 이미지 찾기
        for element in soup.find_all(style=True):
            style = element.get('style', '')
            bg_matches = re.findall(r'url\(["\']?([^"\']+)["\']?\)', style)
            for bg_url in bg_matches:
                if 'goods' in bg_url.lower() or 'product' in bg_url.lower():
                    if not bg_url.startswith('http'):
                        bg_url = f"https://www.oliveyoung.co.kr{bg_url}" if bg_url.startswith('/') else f"https://www.oliveyoung.co.kr/{bg_url}"
                    if bg_url not in image_urls:
                        image_urls.append(bg_url)
        
        # 중복 제거 및 필터링
        image_urls = list(set(image_urls))
        # 상품 이미지로 보이는 것만 필터링
        filtered = []
        for url in image_urls:
            if any(keyword in url.lower() for keyword in ['goods', 'product', 'item', 'detail', 'oliveyoung', 'cdn']):
                filtered.append(url)
        
        return filtered if filtered else image_urls[:10]  # 최대 10개
        
    except Exception as e:
        print(f"⚠️  OliveYoung 이미지 추출 오류: {e}")
        return []


def get_product_images(product_url: str) -> List[str]:
    """
    상품 URL에서 플랫폼을 자동 감지하여 이미지를 추출합니다.
    
    Args:
        product_url: 상품 상세 페이지 URL
    
    Returns:
        이미지 URL 리스트
    """
    if 'musinsa.com' in product_url:
        return get_musinsa_product_images(product_url)
    elif 'oliveyoung.co.kr' in product_url:
        return get_oliveyoung_product_images(product_url)
    else:
        print(f"⚠️  지원하지 않는 플랫폼: {product_url}")
        return []


if __name__ == "__main__":
    # 테스트
    musinsa_url = "https://www.musinsa.com/products/5619064"
    oliveyoung_url = "https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000202777&dispCatNo=1000001000200060002&trackingCd=Result_1"
    
    print("Musinsa 이미지 추출 테스트:")
    musinsa_images = get_musinsa_product_images(musinsa_url)
    print(f"  발견된 이미지: {len(musinsa_images)}개")
    for img in musinsa_images[:3]:
        print(f"    - {img}")
    
    print("\nOliveYoung 이미지 추출 테스트:")
    oliveyoung_images = get_oliveyoung_product_images(oliveyoung_url)
    print(f"  발견된 이미지: {len(oliveyoung_images)}개")
    for img in oliveyoung_images[:3]:
        print(f"    - {img}")

