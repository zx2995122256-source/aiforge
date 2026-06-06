"""
开1个窗口，验证链接免密登录，抓API
不关窗口，卡住了告诉你
"""
import asyncio, json, re, sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(line_buffering=True)

with open("accounts_5.json") as f:
    accounts = json.load(f)
with open("accounts_done.txt", "r", encoding="utf-8") as f:
    content = f.read()
links = re.findall(r"验证: (https?://[^\s\n]+)", content)

acc = accounts[2]  # 账号3，链接还没用过 (0,1已用, 2是第三个)
link = links[2]

print(f"账号: {acc['email']}")
print(f"密码: {acc['password']}")
print("正在打开浏览器...")

all_apis = []

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        page = await browser.new_page(no_viewport=True)
        
        # 拦截API
        async def log_req(request):
            url = request.url
            if "api.oiioii.ai" in url:
                body = request.post_data
                entry = {"url": url.split("?")[0], "method": request.method}
                if body:
                    try:
                        entry["body"] = json.loads(body)
                    except:
                        entry["body_str"] = body[:500]
                all_apis.append(entry)
        page.on("request", log_req)
        
        print("[1] 打开验证链接...")
        await page.goto(link, timeout=30000)
        await page.wait_for_timeout(5000)
        print(f"  当前URL: {page.url}")
        
        if "login" in page.url:
            print("[!] 未自动登录，可能需要重新操作")
        else:
            print("[✓] 已自动登录成功")
        
        print(f"\n{'='*60}")
        print(f"浏览器已打开，账号 {acc['email']} 已登录")
        print(f"密码: {acc['password']}")
        print(f"请手动操作生图/生视频")
        print(f"所有API请求会自动记录到 oiioii_api/all_apis.json")
        print(f"{'='*60}")
        print(f"\n卡住了告诉我，不要关闭这个终端或浏览器")
        
        # 持续记录，永不关闭
        while True:
            await asyncio.sleep(5)
            with open("oiioii_api/all_apis.json", "w") as f:
                json.dump(all_apis, f, indent=2, ensure_ascii=False, default=str)

asyncio.run(main())