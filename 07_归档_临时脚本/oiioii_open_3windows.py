"""
开3个窗口，用验证链接免密登录，抓取生图/生视频的API
绝不关闭任何窗口
"""
import asyncio, json, re, sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(line_buffering=True)

with open("accounts_5.json") as f:
    accounts = json.load(f)

with open("accounts_done.txt", "r", encoding="utf-8") as f:
    content = f.read()
links = re.findall(r"验证: (https?://[^\s\n]+)", content)

# 账号2,3,4（索引1,2,3,4 → 用2,3,4，索引1已经用过了）
targets = [
    (accounts[2], links[2]),
    (accounts[3], links[3]),
    (accounts[4], links[4]),
]

all_apis = []

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        
        pages = []
        for i, (acc, link) in enumerate(targets):
            page = await browser.new_page()
            
            # 拦截API
            def make_logger(idx):
                async def log(req):
                    url = req.url
                    if "api.oiioii.ai" in url:
                        all_apis.append({"idx": idx, "url": url.split("?")[0], "method": req.method, "body": req.post_data})
                return log
            page.on("request", make_logger(i))
            
            print(f"\n[{i+1}] 打开账号{i+2}: {acc['email']}")
            await page.goto(link, timeout=30000)
            await page.wait_for_timeout(3000)
            print(f"  当前URL: {page.url}")
            
            # 保持状态，先不导航
            pages.append({"page": page, "acc": acc, "idx": i})
        
        print(f"\n{'='*60}")
        print(f"3个窗口已打开，全部免密登录成功！")
        print(f"请在每个窗口中手动操作：")
        print(f"  1. 找到生图/生视频的入口")
        print(f"  2. 点击进去看看界面")
        print(f"  3. 如果方便，尝试生成一次")
        print(f"所有API请求会自动记录下来")
        print(f"{'='*60}")
        
        print(f"\n当前账号:")
        for p in pages:
            print(f"  [{p['idx']+1}] {p['acc']['email']}")
        
        # 定期保存API记录
        while True:
            await asyncio.sleep(10)
            with open("oiioii_api/all_apis.json", "w") as f:
                json.dump(all_apis, f, indent=2, ensure_ascii=False)
            print(f"  已记录 {len(all_apis)} 个API请求...")

asyncio.run(main())