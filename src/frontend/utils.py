"""
Utility functions for product grouping and similarity matching.
"""
from difflib import SequenceMatcher
from typing import Any


def group_similar_products(results: list[dict[str, Any]], threshold: float = 0.7) -> list[list[dict[str, Any]]]:
    """
    Group similar products based on name similarity.
    
    Args:
        results: List of product dictionaries, each must have a 'name' key
        threshold: Similarity threshold (0.0 to 1.0) for grouping products. Default is 0.7
    
    Returns:
        List of groups, where each group is a list of similar products
    
    Example:
        >>> products = [
        ...     {"name": "헤라 센슈얼 누드 글로스", "price": 35000},
        ...     {"name": "헤라 센슈얼 누드 글로스 3.5g", "price": 35000},
        ...     {"name": "다른 제품", "price": 20000},
        ... ]
        >>> groups = group_similar_products(products, threshold=0.7)
        >>> len(groups)
        2
    """
    groups = []
    used: set[int] = set()

    for i, item in enumerate(results):
        if i in used:
            continue

        group = [item]
        used.add(i)
        for j, other in enumerate(results[i+1:], start=i+1):
            ratio = SequenceMatcher(None, item["name"], other["name"]).ratio()
            if ratio >= threshold:
                group.append(other)
                used.add(j)
        groups.append(group)
    return groups

