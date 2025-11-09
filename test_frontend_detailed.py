"""
Detailed Playwright test to verify the Streamlit frontend design,
including search functionality and product grouping with highlighting.
"""
import time
import subprocess
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def start_streamlit():
    """Start Streamlit server in the background."""
    print("🚀 Starting Streamlit server...")
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path(__file__).parent
    )
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(8)  # Give more time for server to fully start
    
    return process


def test_frontend_detailed():
    """Test the Streamlit frontend with Playwright - detailed version."""
    process = None
    
    try:
        # Start Streamlit
        process = start_streamlit()
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(viewport={"width": 1400, "height": 1000})
            page = context.new_page()
            
            print("🌐 Navigating to Streamlit app...")
            page.goto("http://localhost:8501", wait_until="networkidle", timeout=30000)
            
            # Wait for page to load
            time.sleep(3)
            
            # Take initial screenshot
            print("📸 Taking initial screenshot...")
            page.screenshot(path="screenshot_1_initial.png", full_page=True)
            
            # Verify basic UI elements
            print("\n✅ Verifying basic UI elements...")
            checks = {
                "Title": page.locator("h1:has-text('Multi-Platform Beauty Search')"),
                "Caption": page.locator("text=Compare product prices"),
                "Search Input": page.locator('input[placeholder*="헤라"]'),
                "Search Button": page.locator('button:has-text("Search")'),
            }
            
            for name, locator in checks.items():
                if locator.is_visible():
                    print(f"   ✓ {name} found")
                else:
                    print(f"   ✗ {name} not found")
            
            # Perform a search
            print("\n🔍 Performing search test...")
            search_input = page.locator('input[placeholder*="헤라"]')
            search_input.fill("헤라 센슈얼 누드 글로스")
            time.sleep(1)
            
            search_button = page.locator('button:has-text("Search")')
            search_button.click()
            
            print("⏳ Waiting for search results...")
            # Wait for spinner to appear and disappear
            try:
                page.wait_for_selector('[data-testid="stSpinner"]', timeout=5000)
                print("   ✓ Spinner appeared")
            except:
                print("   ⚠ Spinner not detected (may have loaded too fast)")
            
            # Wait for results (this might take a while due to scraping)
            print("   ⏳ Waiting for results to load (this may take 30-60 seconds)...")
            time.sleep(40)  # Give time for scraping
            
            # Take screenshot after search
            print("📸 Taking screenshot after search...")
            page.screenshot(path="screenshot_2_after_search.png", full_page=True)
            
            # Check for results
            print("\n✅ Checking search results...")
            
            # Check for "Found X results" message
            results_text = page.locator('text=/Found.*results.*grouped/')
            if results_text.count() > 0:
                print(f"   ✓ Results summary found: {results_text.first.inner_text()}")
            else:
                print("   ⚠ Results summary not found")
            
            # Check for product groups
            product_groups = page.locator('h3:has-text("💄")')
            group_count = product_groups.count()
            print(f"   ✓ Found {group_count} product group(s)")
            
            # Check for cheapest product highlighting
            print("\n✅ Checking cheapest product highlighting...")
            
            # Look for "최저가" badge
            cheapest_badge = page.locator('text=최저가')
            badge_count = cheapest_badge.count()
            print(f"   ✓ Found {badge_count} '최저가' badge(s)")
            
            # Check for highlighted borders (red border around cheapest product)
            # This is harder to detect programmatically, but we can check the HTML
            page_content = page.content()
            if 'border: 3px solid #FF6B6B' in page_content:
                print("   ✓ Red border styling found in HTML")
            else:
                print("   ⚠ Red border styling not found")
            
            # Check for sorted prices (cheapest first)
            print("\n✅ Checking price sorting...")
            price_elements = page.locator('text=/💰.*원/')
            prices = []
            for i in range(min(price_elements.count(), 10)):  # Check first 10 prices
                price_text = price_elements.nth(i).inner_text()
                # Extract number from price text
                import re
                price_match = re.search(r'(\d+)', price_text.replace(',', ''))
                if price_match:
                    prices.append(int(price_match.group(1)))
            
            if prices:
                print(f"   Found prices: {prices[:5]}...")  # Show first 5
                # Check if first price in each group is the lowest
                if len(prices) > 1:
                    first_price = prices[0]
                    other_prices = prices[1:]
                    if all(first_price <= p for p in other_prices[:3]):  # Check first few
                        print("   ✓ Prices appear to be sorted (cheapest first)")
                    else:
                        print("   ⚠ Prices may not be sorted correctly")
            
            # Final screenshot
            print("\n📸 Taking final screenshot...")
            page.screenshot(path="screenshot_3_final.png", full_page=True)
            
            print("\n" + "="*50)
            print("✅ Detailed frontend test completed!")
            print("📸 Screenshots saved:")
            print("   - screenshot_1_initial.png")
            print("   - screenshot_2_after_search.png")
            print("   - screenshot_3_final.png")
            print("="*50)
            
            # Keep browser open for inspection
            print("\n👀 Browser will stay open for 10 seconds for manual inspection...")
            time.sleep(10)
            
            browser.close()
            
    except PlaywrightTimeoutError as e:
        print(f"❌ Timeout error: {e}")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop Streamlit server
        if process:
            print("\n🛑 Stopping Streamlit server...")
            process.terminate()
            process.wait()
            print("✅ Server stopped")


if __name__ == "__main__":
    test_frontend_detailed()

