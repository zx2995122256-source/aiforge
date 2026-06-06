from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.oiioii.ai/login", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)
    buttons = page.locator("button")
    count = buttons.count()
    print(f"Buttons found: {count}")
    for i in range(min(count, 30)):
        text = buttons.nth(i).inner_text(timeout=2000)
        cls = buttons.nth(i).get_attribute("class") or ""
        print(f"  [{i}] text=[{text}] class=[{cls[:50]}]")
    # Any input fields
    inputs = page.locator("input")
    print(f"\nInputs found: {inputs.count()}")
    for i in range(min(inputs.count(), 10)):
        name = inputs.nth(i).get_attribute("name") or ""
        placeholder = inputs.nth(i).get_attribute("placeholder") or ""
        print(f"  input[{i}]: name=[{name}] placeholder=[{placeholder}]")
    # Page title
    print(f"\nPage title: {page.title()}")
    browser.close()