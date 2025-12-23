"""
Tests for group_similar_products function.
"""
from cosver.frontend.utils import group_similar_products


def test_group_similar_products_basic():
    """Test basic grouping functionality."""
    products = [
        {"name": "헤라 센슈얼 누드 글로스", "price": 35000, "source": "OliveYoung"},
        {"name": "헤라 센슈얼 누드 글로스 3.5g", "price": 35000, "source": "Ably"},
        {
            "name": "[OY단독컬러/NEW 홀리데이] 헤라 센슈얼 누드 글로스",
            "price": 20000,
            "source": "OliveYoung",
        },
    ]

    groups = group_similar_products(products, threshold=0.7)

    # Should have 2 groups because the third item varies significantly in text length (prefix)
    # and we don't have images to compare.
    # Item 1 and 2 match (high similarity). Item 3 ("OY단독컬러...") is distinct enough at 0.7 threshold.
    assert len(groups) == 2
    # First group has 2 items
    assert len(groups[0]) == 2
    # Second group has 1 item
    assert len(groups[1]) == 1


def test_group_similar_products_exact_match():
    """Test that exact matches are grouped together."""
    products = [
        {"name": "헤라 센슈얼 누드 글로스", "price": 35000, "source": "OliveYoung"},
        {"name": "헤라 센슈얼 누드 글로스", "price": 35000, "source": "Ably"},
        {"name": "헤라 센슈얼 누드 글로스", "price": 35000, "source": "Zigzag"},
    ]
    
    groups = group_similar_products(products, threshold=0.7)
    
    # All three should be in one group
    assert len(groups) == 1
    assert len(groups[0]) == 3


def test_group_similar_products_no_similarity():
    """Test that products with low similarity are not grouped."""
    products = [
        {"name": "제품 A", "price": 10000, "source": "OliveYoung"},
        {"name": "제품 B", "price": 20000, "source": "Ably"},
        {"name": "제품 C", "price": 30000, "source": "Zigzag"},
    ]
    
    groups = group_similar_products(products, threshold=0.9)
    
    # All should be separate groups
    assert len(groups) == 3
    assert all(len(group) == 1 for group in groups)


def test_group_similar_products_empty_list():
    """Test with empty input."""
    products = []
    
    groups = group_similar_products(products)
    
    assert len(groups) == 0


def test_group_similar_products_single_item():
    """Test with single item."""
    products = [
        {"name": "헤라 센슈얼 누드 글로스", "price": 35000, "source": "OliveYoung"},
    ]
    
    groups = group_similar_products(products)
    
    assert len(groups) == 1
    assert len(groups[0]) == 1
    assert groups[0][0]["name"] == "헤라 센슈얼 누드 글로스"


def test_group_similar_products_threshold_adjustment():
    """Test that threshold affects grouping."""
    products = [
        {"name": "헤라 센슈얼 누드 글로스", "price": 35000, "source": "OliveYoung"},
        {"name": "헤라 센슈얼 누드", "price": 35000, "source": "Ably"},
    ]
    
    # High threshold - might not group
    groups_high = group_similar_products(products, threshold=0.95)
    
    # Low threshold - should group
    groups_low = group_similar_products(products, threshold=0.5)
    
    # With low threshold, they should be grouped
    assert len(groups_low) <= len(groups_high)


def test_group_similar_products_multiple_groups():
    """Test grouping multiple sets of similar products."""
    products = [
        {"name": "헤라 센슈얼 누드 글로스", "price": 35000, "source": "OliveYoung"},
        {"name": "헤라 센슈얼 누드 글로스 3.5g", "price": 35000, "source": "Ably"},
        {"name": "라네즈 네오 파우더", "price": 25000, "source": "OliveYoung"},
        {"name": "라네즈 네오 파우더 매트", "price": 25000, "source": "Zigzag"},
        {"name": "완전히 다른 제품", "price": 20000, "source": "Musinsa"},
    ]
    
    groups = group_similar_products(products, threshold=0.7)
    
    # Should have 3 groups: 헤라 그룹, 라네즈 그룹, 다른 제품
    assert len(groups) == 3
    # Check that similar products are grouped
    group_names = [group[0]["name"] for group in groups]
    assert "헤라" in group_names[0] or "헤라" in group_names[1] or "헤라" in group_names[2]


if __name__ == "__main__":
    # Run tests if executed directly
    import pytest
    pytest.main([__file__, "-v"])
