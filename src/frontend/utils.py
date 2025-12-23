"""
Utility functions for product grouping and similarity matching.
"""
from difflib import SequenceMatcher
from typing import Any
import concurrent.futures
from src.aggregator.image_matcher import download_image, calculate_similarity

def group_similar_products(results: list[dict[str, Any]], threshold: float = 0.7) -> list[list[dict[str, Any]]]:
    """
    Group similar products based on name similarity and image similarity.
    """
    groups = []
    used: set[int] = set()
    
    # Pre-download images for items that might need comparison
    # To save time, we could only download when needed, but parallel download is faster
    # For now, let's download on demand to save bandwidth, or parallelize if slow.
    # Let's use a cache.
    image_cache = {}

    def get_image(url):
        if url not in image_cache:
            image_cache[url] = download_image(url)
        return image_cache[url]

    for i, item in enumerate(results):
        if i in used:
            continue

        group = [item]
        used.add(i)
        
        for j, other in enumerate(results[i+1:], start=i+1):
            if j in used:
                continue
                
            # 1. Text Similarity
            text_ratio = SequenceMatcher(None, item["name"], other["name"]).ratio()
            
            is_match = False
            if text_ratio >= threshold:
                is_match = True
            elif text_ratio >= 0.4: # Ambiguous range
                # 2. Image Similarity
                if item.get("img") and other.get("img"):
                    # Download images (if not already cached)
                    img1 = get_image(item["img"])
                    img2 = get_image(other["img"])
                    
                    if img1 is not None and img2 is not None:
                        img_score = calculate_similarity(img1, img2)
                        if img_score > 0.6: # Visual match threshold
                            is_match = True
            
            if is_match:
                group.append(other)
                used.add(j)
                
        groups.append(group)
    return groups

