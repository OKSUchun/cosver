import sqlite3
import os
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import re

_DB_PATH = os.getenv("COSVER_DB_PATH", "cosver.db")
_IMAGE_DIR = os.getenv("COSVER_IMAGE_DIR", "downloaded_images")
CACHE_HOURS = 24

def set_db_path(path: str):
    """Set custom database path (useful for testing)."""
    global _DB_PATH
    _DB_PATH = path

def get_db_path() -> str:
    """Get current database path."""
    return _DB_PATH

def normalize_name(name: str) -> str:
    """Normalize product name for matching."""
    if not name:
        return ""
    # Remove special characters, convert to lowercase
    normalized = re.sub(r'[^\w\s가-힣]', '', name.lower())
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def init_db():
    """Initialize database and create tables."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Read and execute schema
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path, 'r') as f:
        schema = f.read()
    
    cursor.executescript(schema)
    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {get_db_path()}")

def get_or_create_product(cursor, name: str, brand: str) -> int:
    """Get existing product ID or create new product."""
    normalized = normalize_name(name)
    
    # Try to find existing product
    cursor.execute(
        "SELECT id FROM products WHERE normalized_name = ? AND brand = ?",
        (normalized, brand)
    )
    result = cursor.fetchone()
    
    if result:
        return result[0]
    
    # Create new product
    cursor.execute(
        "INSERT INTO products (name, brand, normalized_name) VALUES (?, ?, ?)",
        (name, brand, normalized)
    )
    return cursor.lastrowid

def save_product(product_data: Dict[str, Any]) -> int:
    """
    Save product and price data to database.
    Returns product_id.
    """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        # Get or create product
        product_id = get_or_create_product(
            cursor,
            product_data.get('name', ''),
            product_data.get('brand', '')
        )
        
        # Save price record
        cursor.execute(
            """INSERT INTO prices (product_id, platform, price, url, img_url)
               VALUES (?, ?, ?, ?, ?)""",
            (
                product_id,
                product_data.get('platform', ''),
                product_data.get('price', 0),
                product_data.get('url', ''),
                product_data.get('img', '')
            )
        )
        
        conn.commit()
        return product_id
    finally:
        conn.close()

def save_products_batch(products: List[Dict[str, Any]]):
    """Save multiple products in a single transaction."""
    if not products:
        return
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        for product in products:
            product_id = get_or_create_product(
                cursor,
                product.get('name', ''),
                product.get('brand', '')
            )
            
            cursor.execute(
                """INSERT INTO prices (product_id, platform, price, url, img_url)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    product_id,
                    product.get('platform', ''),
                    product.get('price', 0),
                    product.get('url', ''),
                    product.get('img', '')
                )
            )
            
            # Also download and save image as BLOB
            if product.get('img'):
                download_and_save_image(product_id, product.get('platform', ''), product.get('img'), conn=conn)
        
        conn.commit()
        print(f"💾 Saved {len(products)} products and their images to database")
    finally:
        conn.close()

def get_cached_results(keyword: str, max_age_hours: int = CACHE_HOURS) -> List[Dict[str, Any]]:
    """
    Get cached results for a keyword.
    Returns results scraped within max_age_hours.
    """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        normalized_keyword = normalize_name(keyword)
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # Find products matching the keyword
        cursor.execute(
            """SELECT DISTINCT p.id, p.name, p.brand
               FROM products p
               WHERE p.normalized_name LIKE ?""",
            (f'%{normalized_keyword}%',)
        )
        
        product_ids = cursor.fetchall()
        
        if not product_ids:
            return []
        
        results = []
        for product_id, name, brand in product_ids:
            # Get recent prices for this product
            cursor.execute(
                """SELECT platform, price, url, img_url, scraped_at
                   FROM prices
                   WHERE product_id = ? AND scraped_at >= ?
                   ORDER BY scraped_at DESC""",
                (product_id, cutoff_time)
            )
            
            prices = cursor.fetchall()
            for platform, price, url, img_url, scraped_at in prices:
                results.append({
                    'name': name,
                    'brand': brand,
                    'platform': platform,
                    'price': price,
                    'url': url,
                    'img': img_url,
                    'source': platform,
                    'cached': True
                })
        
        return results
    finally:
        conn.close()

def download_and_save_image(product_id: int, platform: str, img_url: str, base_dir: str = None, conn=None) -> Optional[str]:
    """
    Download image, save to file (optional) and save as BLOB to database.
    Returns local file path if saved, or "DB_BLOB" if only saved in DB.
    """
    if base_dir is None:
        base_dir = _IMAGE_DIR
    if not img_url:
        return None
    
    try:
        # Use existing connection if provided, else create new one
        should_close = False
        if conn is None:
            conn = sqlite3.connect(get_db_path())
            should_close = True
        
        cursor = conn.cursor()
        
        # Check if already downloaded
        cursor.execute(
            "SELECT local_path, image_data FROM images WHERE product_id = ? AND platform = ?",
            (product_id, platform)
        )
        result = cursor.fetchone()
        
        if result:
            local_path, image_data = result
            if local_path and os.path.exists(local_path):
                if should_close: conn.close()
                return local_path
            if image_data:
                if should_close: conn.close()
                return "DB_BLOB"
        
        # Download image
        response = requests.get(img_url, timeout=10)
        if response.status_code != 200:
            if should_close: conn.close()
            return None
        
        image_content = response.content
        
        # 1. Save to File (Optional)
        save_path = Path(base_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        content_type = response.headers.get('Content-Type', '')
        ext = '.jpg'
        if 'png' in content_type: ext = '.png'
        elif 'webp' in content_type: ext = '.webp'
        
        filename = f"{platform}_{product_id}{ext}"
        full_path = save_path / filename
        
        try:
            with open(full_path, 'wb') as f:
                f.write(image_content)
            local_path_str = str(full_path)
        except Exception as e:
            print(f"⚠️ Failed to write to local filesystem: {e}")
            local_path_str = None
        
        # 2. Save to database as BLOB
        cursor.execute(
            """INSERT OR REPLACE INTO images (product_id, platform, img_url, local_path, image_data)
               VALUES (?, ?, ?, ?, ?)""",
            (product_id, platform, img_url, local_path_str, sqlite3.Binary(image_content))
        )
        
        if should_close:
            conn.commit()
            conn.close()
        
        return local_path_str or "DB_BLOB"
    except Exception as e:
        print(f"❌ Failed to download/save image: {e}")
        return None

def get_image_data_from_db(product_id: int, platform: str) -> Optional[bytes]:
    """Retrieve raw image data from database BLOB."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT image_data FROM images WHERE product_id = ? AND platform = ?",
            (product_id, platform)
        )
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def get_all_products_with_images() -> List[Dict[str, Any]]:
    """Get all products with their image info (local path or BLOB status)."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """SELECT p.id, p.name, p.brand, i.platform, i.local_path, pr.price, 
                      CASE WHEN i.image_data IS NOT NULL THEN 1 ELSE 0 END as has_blob
               FROM products p
               JOIN images i ON p.id = i.product_id
               JOIN prices pr ON p.id = pr.product_id AND i.platform = pr.platform
               ORDER BY p.id"""
        )
        
        results = []
        for product_id, name, brand, platform, local_path, price, has_blob in cursor.fetchall():
            results.append({
                'product_id': product_id,
                'name': name,
                'brand': brand,
                'platform': platform,
                'local_image_path': local_path,
                'price': price,
                'has_blob': bool(has_blob)
            })
        
        return results
    finally:
        conn.close()

# Initialize database on import
if not os.path.exists(get_db_path()):
    init_db()
