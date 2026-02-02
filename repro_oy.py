
from cosver.scraper.oliveyoung_playwright import search_product
import sys

try:
    print("Running search_product with headful=False...")
    items = search_product("test", headful=False)
    print(f"Success! Found {len(items)} items.")
except Exception as e:
    print(f"Failed: {e}")
