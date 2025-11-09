"""
Multi-platform product search aggregator.

This module provides functionality to search for products across multiple
e-commerce platforms and aggregate the results.
"""
from typing import Any, Callable

import streamlit as st


def search_all_platforms(
    keyword: str,
    scrapers: list[tuple[Callable, str]]
) -> list[dict[str, Any]]:
    """
    Search for products across multiple platforms using provided scraper functions.
    
    Args:
        keyword: The search keyword to query across platforms
        scrapers: List of tuples containing (scraper_function, platform_name)
    
    Returns:
        List of product dictionaries with 'source' field added to each result
    """
    results = []
    
    for scraper_func, platform_name in scrapers:
        try:
            platform_results = scraper_func(keyword)
            # Add source field to each result
            for result in platform_results:
                result["source"] = platform_name
            results.extend(platform_results)
        except Exception as e:
            st.warning(f"{platform_name} error: {e}")
    
    return results

