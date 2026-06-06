from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.oiioii.ai/login", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)
    
    # Click Email tab
    print("Clicking Email tab...")
    email_tab = page.locator("button:has-text('Email')")
    email_tab.click(timeout=10000)
    page.wait_for_timeout(2000)
    
    # Check what inputs appear
    inputs = page.locator("input")
    print(f"Inputs after clicking Email: {inputs.count()}")
    for i in range(inputs.count()):
        name = inputs.nth(i).get_attribute("name") or ""
        placeholder = inputs.nth(i).get_attribute("placeholder") or ""
        input_type = inputs.nth(i).get_attribute("type") or ""
        print(f"  [{i}] name=[{name}] type=[{input_type}] placeholder=[{placeholder}]")
    
    # Check all buttons
    buttons = page.locator("button")
    print(f"\nButtons: {buttons.count()}")
    for i in range(buttons.count()):
        text = buttons.nth(i).inner_text(timeout=2000)
        if text.strip():
            print(f"  [{i}] [{text.strip()}]")
    
    browser.close()