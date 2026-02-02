import re
from playwright.sync_api import Page, expect

def test_search_functionality(page: Page):
    """
    Test the search functionality of the deployed Streamlit app.
    Navigates to the deployed URL, verifies the title, performs a search,
    and checks if results are displayed.
    """
    # 1. Navigate to the deployed app
    page.goto("https://cosver-zk7itetontkdjm2d5peg2v.streamlit.app/", timeout=60000)

    # 2. Wait for the app to load (Streamlit apps can be slow to start)
    # Check for a specific element that confirms the app is ready.
    # We look for the main title or the search input.
    # Increasing timeout for the initial load significantly.
    
    # Wait for the title to verify app loaded
    # Update title to match current app version "💄 올최맞"
    # We use a regex or partial match to be more robust
    expect(page.get_by_role("heading", name=re.compile(r"올최맞|Multi-Platform"))).to_be_visible(timeout=30000)

    # 3. Verify Search Input exists
    search_input = page.get_by_placeholder(re.compile(r"헤라|product search", re.IGNORECASE))
    expect(search_input).to_be_visible()

    # 4. Perform a search
    # Using a known term that should return results
    search_term = "헤라 센슈얼"
    search_input.fill(search_term)
    
    # Click search button
    search_button = page.get_by_role("button", name="Search")
    search_button.click()

    # 5. Verify Results
    # Wait for the spinner to disappear (optional, but good practice)
    # page.wait_for_selector('[data-testid="stSpinner"]', state="detached", timeout=10000)

    # Check for success message or result headers
    # "Found X results" or similar text
    # We'll look for the "Found" text which appears in the success message
    expect(page.get_by_text(re.compile(r"Found \d+ results"))).to_be_visible(timeout=60000)

    # Check that we have some product groups (h3 headers)
    # At least one product group should appear
    expect(page.get_by_role("heading", level=3).first).to_be_visible()

    print("✅ Search test passed successfully against deployed app.")
