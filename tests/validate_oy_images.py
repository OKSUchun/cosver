
import os
import sys
from src.scraper.oliveyoung_playwright import search_product
from src.database.db import save_product, download_and_save_image, init_db, get_db_path, get_image_data_from_db

def validate():
    keyword = "닥터지 크림"
    print(f"🔍 Searching for '{keyword}' on OliveYoung...")
    
    try:
        results = search_product(keyword, headful=True)
    except Exception as e:
        print(f"❌ Scraper failed: {e}")
        return

    if not results:
        print("❓ No results found.")
        return

    print(f"✅ Found {len(results)} items.")
    
    # Take the first one to validate
    item = results[0]
    print(f"\n🏷️ Validating item: {item['name']}")
    print(f"🖼️ Image URL: {item['img']}")
    
    if not item['img']:
        print("❌ Image URL is missing!")
        return

    # 1. Save to DB (this creates the product entry)
    print("💾 Saving to database...")
    product_id = save_product(item)
    print(f"✅ Product ID: {product_id}")

    # 2. Download and save image (File + BLOB)
    print("⏬ Downloading and saving image (File + BLOB)...")
    local_path = download_and_save_image(product_id, "OliveYoung", item['img'])
    
    blob_data = get_image_data_from_db(product_id, "OliveYoung")

    if blob_data:
        print(f"✅ Image successfully saved as BLOB. Size: {len(blob_data)} bytes")
    else:
        print("❌ Failed to save image as BLOB.")

    if local_path and os.path.exists(local_path):
        print(f"✅ Image also saved to: {local_path}")
        print(f"📁 File size: {os.path.getsize(local_path)} bytes")
    elif local_path == "DB_BLOB":
        print(f"✅ Image saved to database BLOB correctly.")
    else:
        print(f"❌ Failed to download/save image.")

if __name__ == "__main__":
    # Ensure DB is initialized
    if not os.path.exists(get_db_path()):
        init_db()
    validate()
