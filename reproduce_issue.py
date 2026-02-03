
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from cosver.scraper.oliveyoung_playwright import search_product

if __name__ == "__main__":
    keyword = "퓌 푸딩팟"
    print(f"Searching for {keyword}...")
    try:
        results = search_product(keyword, headful=True)
        print(f"Found {len(results)} results")
        if results:
            print(results[0])
    except Exception as e:
        print(f"Error: {e}")
