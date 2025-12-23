"""
Playwright test script to verify the Streamlit frontend design.
"""
import time
import subprocess
import sys
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def start_streamlit():
    """Start Streamlit server in the background."""
    print("🚀 Starting Streamlit server...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "../src/cosver/app.py", "--server.port", "8501", "--server.headless", "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path(__file__).parent,
        env=env
    )
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(5)
    
    return process


def test_frontend():
    """Test the Streamlit frontend with Playwright."""
    process = None
    
    try:
        # Start Streamlit
        process = start_streamlit()
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()
            
            print("🌐 Navigating to Streamlit app...")
            page.goto("http://localhost:8501", wait_until="networkidle", timeout=30000)
            
            # Wait for page to load
            time.sleep(2)
            
            # Take initial screenshot
            print("📸 Taking initial screenshot...")
            page.screenshot(path="screenshot_initial.png", full_page=True)
            
            # Check if title is present
            print("✅ Checking page title...")
            title = page.locator("h1:has-text('Multi-Platform Beauty Search')")
            if title.is_visible():
                print("   ✓ Title found")
            else:
                print("   ✗ Title not found")
            
            # Check if search input is present
            print("✅ Checking search input...")
            search_input = page.locator('input[placeholder*="헤라 센슈얼 누드 글로스"]')
            if search_input.is_visible():
                print("   ✓ Search input found")
            else:
                print("   ✗ Search input not found")
            
            # Check if search button is present
            print("✅ Checking search button...")
            search_button = page.locator('button:has-text("Search")')
            if search_button.is_visible():
                print("   ✓ Search button found")
            else:
                print("   ✗ Search button not found")
            
            # Test search functionality (if we want to test with actual search)
            # For now, just verify the UI elements are present
            
            # Check for any error messages
            error_msg = page.locator('div[data-testid="stAlert"]')
            if error_msg.count() > 0:
                print(f"⚠️  Found {error_msg.count()} alert(s)")
            
            # Take final screenshot
            print("📸 Taking final screenshot...")
            page.screenshot(path="screenshot_final.png", full_page=True)
            
            print("\n✅ Frontend test completed!")
            print("📸 Screenshots saved: screenshot_initial.png, screenshot_final.png")
            
            # Keep browser open for a moment to see the result
            time.sleep(3)
            
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
    test_frontend()

