import requests
import numpy as np
import cv2
from PIL import Image
import imagehash
from io import BytesIO

def download_image(url: str) -> np.ndarray:
    """
    Download image from URL and convert to numpy array (RGB).
    Returns None if download fails.
    """
    if not url:
        return None
        
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return None
            
        image_data = response.content
        image = Image.open(BytesIO(image_data))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        return np.array(image)
    except Exception as e:
        print(f"Error downloading image {url}: {e}")
        return None

def calculate_similarity(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Calculate similarity between two images.
    Combines structural similarity (dHash) and color similarity (Histogram).
    Returns a score between 0.0 and 1.0.
    """
    if img1 is None or img2 is None:
        return 0.0
        
    # 1. Structural Similarity (dHash)
    try:
        pil_img1 = Image.fromarray(img1)
        pil_img2 = Image.fromarray(img2)
        
        hash1 = imagehash.dhash(pil_img1)
        hash2 = imagehash.dhash(pil_img2)
        
        # Hamming distance: 0 means identical, higher means different
        # Max distance for 64-bit hash is 64
        distance = hash1 - hash2
        
        # Normalize to 0-1 (1 means identical)
        # Threshold: if distance > 20, they are very different
        hash_score = max(0.0, (20 - distance) / 20.0)
    except Exception:
        hash_score = 0.0
        
    # 2. Color Similarity (Histogram)
    try:
        # Convert to HSV for better color comparison
        hsv1 = cv2.cvtColor(img1, cv2.COLOR_RGB2HSV)
        hsv2 = cv2.cvtColor(img2, cv2.COLOR_RGB2HSV)
        
        # Calculate histograms
        # H: 50 bins, S: 60 bins
        hist1 = cv2.calcHist([hsv1], [0, 1], None, [50, 60], [0, 180, 0, 256])
        hist2 = cv2.calcHist([hsv2], [0, 1], None, [50, 60], [0, 180, 0, 256])
        
        # Normalize
        cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)
        
        # Compare histograms (Correlation)
        # 1.0 = identical, 0.0 = no correlation
        color_score = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        color_score = max(0.0, color_score) # Clip negative values
    except Exception:
        color_score = 0.0
        
    # Weighted combination
    # Structure is usually more important for product matching
    final_score = 0.6 * hash_score + 0.4 * color_score
    
    return final_score
