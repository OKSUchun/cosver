-- Products table: stores unique products
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    brand TEXT,
    normalized_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(normalized_name, brand)
);
-- Prices table: stores price records from different platforms
CREATE TABLE IF NOT EXISTS prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    price REAL NOT NULL,
    url TEXT,
    img_url TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);
-- Images table: stores downloaded image paths and raw data
CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    img_url TEXT NOT NULL,
    local_path TEXT,
    image_data BLOB,
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE(product_id, platform)
);
-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_prices_product_id ON prices(product_id);
CREATE INDEX IF NOT EXISTS idx_prices_scraped_at ON prices(scraped_at);
CREATE INDEX IF NOT EXISTS idx_products_normalized_name ON products(normalized_name);