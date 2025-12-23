
from src.aggregator.search import search_all_platforms
from src.scraper.ably import search_product as ab
from src.scraper.musinsa import search_product as ms
from src.scraper.oliveyoung_playwright import search_product as oy
from src.scraper.zigzag import search_product as zz
import sys

def backfill(keyword: str):
    print(f"🚀 Starting backfill for keyword: '{keyword}'")
    
    scrapers = [
        (oy, "OliveYoung"),
        (ab, "Ably"),
        (zz, "Zigzag"),
        (ms, "Musinsa"),
    ]
    
    results = search_all_platforms(keyword, scrapers)
    
    print(f"✅ Backfill complete. Found and stored {len(results)} items.")

if __name__ == "__main__":
    keyword = "설화수 자음생크림"
    if len(sys.argv) > 1:
        keyword = sys.argv[1]
    
    backfill(keyword)
