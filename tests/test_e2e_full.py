import os
import subprocess
import sys
import time
import pytest
import re
from pathlib import Path
from playwright.sync_api import Page, expect

# Define port and URL
PORT = 8501
BASE_URL = f"http://localhost:{PORT}"

@pytest.fixture(scope="module")
def streamlit_app():
    """
    Fixture to start the Streamlit app in the background.
    """
    print("🚀 Starting Streamlit server...")
    
    # Path to the app file
    app_path = Path(__file__).parent.parent / "src" / "cosver" / "app.py"
    
    # Environment setup
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")
    
    # Command to run streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(app_path),
        "--server.port", str(PORT),
        "--server.headless", "true",
        "--server.address", "localhost"
    ]
    
    # Start process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=Path(__file__).parent.parent
    )
    
    # Wait for server to be ready
    # Check if process exited early
    time.sleep(5)
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        print(f"❌ Streamlit failed to start. Return code: {process.returncode}")
        print(f"STDOUT: {stdout.decode()}")
        print(f"STDERR: {stderr.decode()}")
        raise RuntimeError("Streamlit failed to start")
    
    print("✅ Streamlit process running...")
    
    yield process
    
    # Cleanup
    print("\n🛑 Stopping Streamlit server...")
    process.terminate()
    process.wait()

def test_search_flow(page: Page, streamlit_app):
    """
    Test the full search flow on the local Streamlit instance.
    """
    try:
        # 1. Navigate to the local app
        try:
            page.goto(BASE_URL, timeout=10000)
        except Exception as e:
            print(f"Initial navigation failed: {e}")
            time.sleep(2)
            page.goto(BASE_URL)

        # 2. Verify Title matches "💄 올최맞"
        # Use a more generic locator first to see what's there
        page.wait_for_load_state("networkidle")
        
        # Check if we are stuck on "Please wait"
        if page.get_by_text("Please wait").is_visible():
            print("⏳ Still seeing 'Please wait'...")
            page.wait_for_timeout(5000)

        # Debug: print all h1s
        h1s = page.locator("h1").all_inner_texts()
        print(f"Found H1 headers: {h1s}")
        
        expect(page.get_by_role("heading", name="💄 올최맞")).to_be_visible(timeout=30000)
        
        # 3. Enter search term "퓌 푸딩"
        search_input = page.get_by_placeholder(re.compile(r"헤라|product search|e\.g\.", re.IGNORECASE))
        expect(search_input).to_be_visible()
        search_input.fill("퓌 푸딩")
        
        # 4. Click Search
        search_button = page.get_by_role("button", name="Search")
        search_button.click()
        
        # 5. Wait for Results
        print("⏳ Waiting for scrape results (this may take 30s+)...")
        expect(page.get_by_text(re.compile(r"Found \d+ results"))).to_be_visible(timeout=60000)
        
        # 6. Verify at least one product card or group
        expect(page.get_by_role("heading", level=3).first).to_be_visible()
        
        print("✅ Local E2E search test passed.")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        page.screenshot(path="failure_screenshot.png", full_page=True)
        print(f"📸 Screenshot saved to failure_screenshot.png")
        raise e
