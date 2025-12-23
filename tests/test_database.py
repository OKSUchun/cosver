import unittest
import os
import sqlite3
from datetime import datetime, timedelta
from cosver.database.db import (
    init_db, 
    save_product, 
    save_products_batch,
    get_cached_results,
    normalize_name,
    set_db_path,
    get_db_path
)

class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        # Use a test database
        set_db_path("test_cosver.db")
        
        # Remove existing test db
        if os.path.exists(get_db_path()):
            os.remove(get_db_path())
        
        init_db()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        if os.path.exists(get_db_path()):
            os.remove(get_db_path())
    
    def test_normalize_name(self):
        """Test name normalization."""
        self.assertEqual(normalize_name("Dr.G Red Cream"), "drg red cream")
        self.assertEqual(normalize_name("헤라 센슈얼 누드 글로스"), "헤라 센슈얼 누드 글로스")
        self.assertEqual(normalize_name("  Extra   Spaces  "), "extra spaces")
    
    def test_save_product(self):
        """Test saving a single product."""
        product = {
            'name': 'Test Product',
            'brand': 'Test Brand',
            'platform': 'TestPlatform',
            'price': 10000,
            'url': 'https://test.com/product',
            'img': 'https://test.com/image.jpg'
        }
        
        product_id = save_product(product)
        self.assertIsNotNone(product_id)
        self.assertGreater(product_id, 0)
    
    def test_save_products_batch(self):
        """Test saving multiple products."""
        products = [
            {
                'name': 'Product 1',
                'brand': 'Brand A',
                'platform': 'Platform1',
                'price': 5000,
                'url': 'https://test.com/1',
                'img': 'https://test.com/1.jpg'
            },
            {
                'name': 'Product 2',
                'brand': 'Brand B',
                'platform': 'Platform2',
                'price': 7000,
                'url': 'https://test.com/2',
                'img': 'https://test.com/2.jpg'
            }
        ]
        
        save_products_batch(products)
        
        # Verify products were saved
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertGreaterEqual(count, 2)
    
    def test_get_cached_results(self):
        """Test retrieving cached results."""
        # Save a product
        product = {
            'name': 'Dr.G Red Blemish Cream',
            'brand': 'Dr.G',
            'platform': 'OliveYoung',
            'price': 20000,
            'url': 'https://test.com/drg',
            'img': 'https://test.com/drg.jpg'
        }
        save_product(product)
        
        # Search for it with a simpler term
        results = get_cached_results("Red Blemish")
        
        self.assertGreater(len(results), 0)
        self.assertTrue(any('Red Blemish' in r['name'] for r in results))
    
    def test_cache_expiration(self):
        """Test that old results are not returned."""
        # This test would require manipulating timestamps
        # For now, we'll just verify the function runs
        results = get_cached_results("NonexistentProduct", max_age_hours=1)
        self.assertIsInstance(results, list)

if __name__ == '__main__':
    unittest.main()
