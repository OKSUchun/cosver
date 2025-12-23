"""
Multi-platform product search aggregator.

This module provides functionality to search for products across multiple
e-commerce platforms and aggregate the results.
"""
from typing import Any, Callable

import streamlit as st
from cosver.database.db import get_cached_results, save_products_batch


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
    # 1. Check cache first
    cached_results = get_cached_results(keyword)
    
    if cached_results:
        st.info(f"📦 Found {len(cached_results)} cached results (less than 24 hours old)")
        # Still scrape to get fresh data, but we have fallback
    
    # 2. Scrape fresh data
    fresh_results = []
    
    for scraper_func, platform_name in scrapers:
        try:
            platform_results = scraper_func(keyword)
            # Add source field to each result
            for result in platform_results:
                result["source"] = platform_name
            fresh_results.extend(platform_results)
        except Exception as e:
            st.warning(f"{platform_name} error: {e}")
    
    # 3. Save fresh results to database
    if fresh_results:
        try:
            save_products_batch(fresh_results)
        except Exception as e:
            print(f"Failed to save to database: {e}")
    
    # 4. Combine cached and fresh results (prefer fresh, use cached as fallback)
    # For now, just return fresh results if available, otherwise cached
    results = fresh_results if fresh_results else cached_results

    return results


