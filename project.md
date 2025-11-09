# OliveYoung Tracker

## 1. 프로젝트 개요
올리브영 세일을 항상 하지만, 막상 실제로 최저가인지가 너무 궁금할때가 많다. 네이버에서 노출되지 않는 경우가 많아 실제 최저가인지 각각의 사이트를 접속해서 검색해야만 실시간 최저가를 확인할 수 있다. 

### 목표:
네이버에서 노출되지 않는 플랫폼을 중심으로 실시간 최저가 한눈에 비교하는 서비스 개발.

### 핵심기능:
- 제품명 검색 -> 플랫폼별 가격 스크래핑
- 최저가 비교 및 링크 제공
- (Phase 2) 주기적 데이터 수집
- (Phase 2) 가격 추이 및 알림

## 2. 전체 구조 

[User Browser]
      │
      ▼
[Frontend: Streamlit UI]
  - Product search input
  - Price table & charts
      │
      ▼
[Backend: Scraper API (FastAPI)]
  - Scraping modules:
       ├─ oliveyoung_scraper.py
       ├─ musinsa_scraper.py
       └─ zigzag_scraper.py
  - Aggregator:
       combines and normalizes data
      │
      ▼
[Database: PostgreSQL]
  - Tables:
       products, prices, logs


## 3. 데이터 플로우 
1. 사용자가 "닥터지 크림" 입력
2. Streamlit -> Backend 전송
3. Scraper 모듈이 검색 페이지 호출 
4. HTML 파싱 -> 가격, URL, 플랫폼 정보 반환
5. Aggregator 정보 통합
6. DB 에 입력
7. Streamlit 시각화

## 4. Aggregator 
같은 상품을 그룹핑하는 기준
- 상품명
- 용량
- 갯수