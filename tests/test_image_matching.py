import unittest
import numpy as np
from src.aggregator.image_matcher import download_image, calculate_similarity
from src.frontend.utils import group_similar_products

class TestImageMatching(unittest.TestCase):
    def test_download_image(self):
        url = "https://image.oliveyoung.co.kr/uploads/images/goods/10/0000/0023/A00000023874305ko.jpg?l=ko"
        img = download_image(url)
        self.assertIsNotNone(img)
        self.assertIsInstance(img, np.ndarray)
        self.assertEqual(len(img.shape), 3) # Height, Width, Channels

    def test_similarity_identical(self):
        url = "https://image.oliveyoung.co.kr/uploads/images/goods/10/0000/0023/A00000023874305ko.jpg?l=ko"
        img = download_image(url)
        score = calculate_similarity(img, img)
        self.assertGreater(score, 0.95)

    def test_similarity_different(self):
        url1 = "https://image.oliveyoung.co.kr/uploads/images/goods/10/0000/0023/A00000023874305ko.jpg?l=ko"
        url2 = "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png"
        
        img1 = download_image(url1)
        img2 = download_image(url2)
        
        if img1 is None or img2 is None:
            print("Skipping difference test due to download failure")
            return

        score = calculate_similarity(img1, img2)
        print(f"Similarity score for different images: {score}")
        self.assertLess(score, 0.5)

    def test_grouping_with_images(self):
        # Mock products
        products = [
            {
                "name": "Dr.G Red Blemish Cream",
                "price": 20000,
                "img": "https://image.oliveyoung.co.kr/uploads/images/goods/10/0000/0023/A00000023874305ko.jpg?l=ko"
            },
            {
                "name": "Dr.G Cream Set", # Different name, but same image (simulating same product with different name)
                "price": 25000,
                "img": "https://image.oliveyoung.co.kr/uploads/images/goods/10/0000/0023/A00000023874305ko.jpg?l=ko"
            },
            {
                "name": "Google Logo",
                "price": 100,
                "img": "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png"
            }
        ]
        
        # Threshold 0.8 for text would fail for "Dr.G Red Blemish Cream" vs "Dr.G Cream Set"
        # But image matching should group them if text similarity is in ambiguous range (0.4-0.8)
        # "Dr.G Red Blemish Cream" vs "Dr.G Cream Set" ratio is around 0.5-0.6
        
        groups = group_similar_products(products, threshold=0.8)
        
        # Expect 2 groups: [Dr.G, Dr.G] and [Google]
        self.assertEqual(len(groups), 2)
        self.assertEqual(len(groups[0]), 2)
        self.assertEqual(groups[0][0]["name"], "Dr.G Red Blemish Cream")
        self.assertEqual(groups[0][1]["name"], "Dr.G Cream Set")

if __name__ == '__main__':
    unittest.main()
