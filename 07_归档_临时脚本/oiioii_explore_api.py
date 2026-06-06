"""
oiioii.ai - 激活账号 + 登录 + 抓取API
"""
import asyncio, json, re, sys, urllib.parse
from playwright.async_api import async_playwright

sys.stdout.reconfigure(line_buffering=True)

with open("accounts_5.json") as f:
    accounts = json.load(f)

# Account 0 needs activation first via verification link
ACC = accounts[0]
print(f"Account: {ACC['email']}")
print(f"Password: {ACC['password']}")

# Check if there's a verify link in accounts_done
with open("accounts_done.txt", "r", encoding="utf-8") as f:
    content = f.read()

# Extract the first verify link
links = re.findall(r"验证: (https?://[^\s\n]+)", content)
print(f"Found {len(links)} verify links")

all_api_calls = []

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        ctx = await browser.new_context(no_viewport=True, storage_state=None)
        page = await ctx.new_page()
        
        captured = []
        
        def on_request(request):
            url = request.url
            if "api.oiioii.ai" in url:
                method = request.method
                body = request.post_data
                captured.append({
                    "method": method,
                    "url": url.split("?")[0],
                    "body": body[:500] if body else None,
                    "headers": dict(request.headers),
                })
        
        def on_response(response):
            url = response.url
            if "api.oiioii.ai" in url:
                try:
                    status = response.status
                    print(f"  [{status}] {url.split('?')[0]}")
                except:
                    pass
        
        page.on("request", on_request)
        page.on("response", on_response)
        
        # Step 1: Activate via verification link (if available)
        if len(links) > 0:
            verify_link = links[0]
            # Clean the link - extract pure supabase URL
            if "awstrack" in verify_link:
                decoded = urllib.parse.unquote(verify_link)
                supabase_match = re.search(r'(https?://[^/]+\.supabase\.co/auth/v1/verify\?token=[^&\s]+&type=[^&\s]+)', decoded)
                if supabase_match:
                    verify_link = supabase_match.group(1)
            
            print(f"\n[1] Opening verification link...")
            await page.goto(verify_link, timeout=30000)
            await page.wait_for_timeout(3000)
            print(f"  After verify URL: {page.url}")
            await page.screenshot(path="oiioii_api/verified.png")
        
        # Step 2: Login
        print("\n[2] Login page...")
        await page.goto("https://www.oiioii.ai/login", timeout=60000)
        await page.wait_for_timeout(2000)
        
        print("[3] Switching to email tab & filling...")
        await page.locator("button:has-text('邮箱')").click()
        await page.wait_for_timeout(500)
        await page.fill("#email", ACC["email"])
        await page.fill("#password", ACC["password"])
        await page.locator("button:has-text('登录/注册')").click()
        
        print("[4] Please solve CAPTCHA manually...")
        
        for i in range(180):
            url = page.url
            if "login" not in url:
                print(f"✓ Logged in! URL: {url}")
                break
            if i % 10 == 0:
                print(f"  Waiting... ({i}s)")
            await page.wait_for_timeout(1000)
        
        await page.wait_for_timeout(3000)
        await page.screenshot(path="oiioii_api/home.png")
        
        # Step 5: Navigate to generation page
        print("\n[5] Looking for generation features...")
        
        # Check what buttons are available
        buttons = await page.query_selector_all("button, a, [role='button'], [class*='btn'], [class*='card'], [class*='item']")
        print("\nAvailable elements:")
        for b in buttons:
            try:
                txt = (await b.inner_text()).strip()
                cls = await b.get_attribute("class") or ""
                href = await b.get_attribute("href") or ""
                if txt and len(txt) < 40:
                    print(f"  '{txt}' | href='{href[:80]}'")
            except:
                pass
        
        # Try common navigation
        for target in ["直接生图", "直接生视频", "智能生图", "创作", "画布", "canvas", "image", "video", "生成"]:
            try:
                el = page.locator(f"text={target}").first
                if await el.is_visible(timeout=2000):
                    print(f"\nClicking '{target}'...")
                    await el.click()
                    await page.wait_for_timeout(3000)
                    break
            except:
                pass
        
        await page.screenshot(path="oiioii_api/generation.png")
        print(f"\nURL after navigation: {page.url}")
        
        # Show captured API calls so far
        print(f"\n=== Captured API Calls ({len(captured)}) ===")
        for c in captured:
            print(f"  {c['method']} {c['url']}")
            if c['body']:
                print(f"    Body: {c['body'][:300]}")
        
        # Save API calls for analysis
        with open("oiioii_api_calls.json", "w") as f:
            json.dump(captured, f, indent=2, ensure_ascii=False)
        print(f"\nSaved {len(captured)} API calls to oiioii_api_calls.json")
        
        print("\n\nBrowser open - navigate to generate an image/video to capture more APIs!")
        while True:
            await page.wait_for_timeout(30000)

asyncio.run(main())