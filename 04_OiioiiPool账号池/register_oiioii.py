"""
自包含 Oiioii 账号注册脚本 —— 无需本地项目依赖
可在 GitHub Actions / Colab / 任意 Linux/Windows 上运行

使用方法：
    # 默认：注册5个，推到服务器
    python register_oiioii.py --count 5

    # 连续模式：注册到50个为止
    python register_oiioii.py --continuous --target 50

    # 用 capsolver 解验证码（推荐，成功率95%+）
    export CAPSOLVER_API_KEY=CAP-xxxx
    python register_oiioii.py --count 20

环境变量：
    SERVER_URL     - 目标服务器地址 (默认 http://122.51.205.94)
    CAPSOLVER_API_KEY - Capsolver API Key（不用就靠 OpenCV 硬解）
"""
import os
import sys
import time
import json
import random
import string
import re
import base64
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests as http_req

SERVER_URL = os.environ.get("SERVER_URL", "http://122.51.205.94")
CAPSOLVER_KEY = os.environ.get("CAPSOLVER_API_KEY", "")

# ─── API 地址 ───
MAIL_TM_API = "https://api.mail.tm"
SUPABASE_URL = "https://spb.oiioii.ai"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVndnV6ZXN0eXlwYm1jZnVycmJkIiwicm9sZSI6ImFub24iLC"
    "JpYXQiOjE3NjEyMTU4NTEsImV4cCI6MjA3Njc5MTg1MX0."
    "Z1qdxtK0PLF5NV1yXrI9s_W2Hurdxo143DBzuUuajh0"
)
API_BASE = "https://api.oiioii.ai"


# ====================================================================
# 临时邮箱 (mail.tm)
# ====================================================================
class TempMail:
    @staticmethod
    def create():
        try:
            r = http_req.get(f"{MAIL_TM_API}/domains", timeout=10)
            domains = r.json().get("hydra:member", [])
            if not domains:
                return None, None
            domain = domains[0]["domain"]
            rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
            email = f"oiio_{rand}@{domain}"
            password = f"Oi{rand}!Pass1"
            r = http_req.post(f"{MAIL_TM_API}/accounts", json={"address": email, "password": password}, timeout=15)
            if r.status_code == 201:
                return email, password
        except Exception as e:
            print(f"  [TempMail] create error: {e}")
        return None, None

    @staticmethod
    def get_token(email, password):
        try:
            r = http_req.post(f"{MAIL_TM_API}/token", json={"address": email, "password": password}, timeout=10)
            if r.status_code == 200:
                return r.json()["token"]
        except Exception:
            pass
        return None

    @staticmethod
    def poll_verify_link(mail_token, timeout=90):
        headers = {"Authorization": f"Bearer {mail_token}"}
        start = time.time()
        while time.time() - start < timeout:
            try:
                r = http_req.get(f"{MAIL_TM_API}/messages", headers=headers, timeout=10)
                for msg in r.json().get("hydra:member", []):
                    r2 = http_req.get(f"{MAIL_TM_API}/messages/{msg['id']}", headers=headers, timeout=10)
                    html = r2.json().get("html", [])
                    html_content = html[0] if isinstance(html, list) and html else (html or "")
                    links = re.findall(r'https?://[^\s"\'<>]+(?:confirm|verify|token)[^\s"\'<>]*', html_content, re.IGNORECASE)
                    if not links:
                        all_links = re.findall(r'https?://[^\s"\'<>]+', html_content)
                        links = [l for l in all_links if "oiioii" in l or "supabase" in l]
                    if links:
                        return links[0].replace("&amp;", "&")
            except Exception:
                pass
            time.sleep(5)
        return None


# ====================================================================
# 验证码解析
# ====================================================================
CAPTCHA_JS = """() => {
    const result = {bg_url: null, slider_url: null, bg_w: 0, bg_h: 0,
                   slider_w: 0, slider_h: 0, slider_left: 0,
                   bg_size_width: 0, bg_size_height: 0,
                   bg_pos_x: 0, bg_pos_y: 0};
    const allEls = document.querySelectorAll('div');
    let bgEl = null, sliderEl = null;
    for (const el of allEls) {
        const s = window.getComputedStyle(el);
        const bi = s.backgroundImage;
        if (!bi || bi === 'none') continue;
        const dw = el.offsetWidth;
        const dh = el.offsetHeight;
        if (dw > 200 && dh > 150 && !bgEl) bgEl = el;
        else if (dw > 30 && dw < 100 && dh > 30 && dh < 100 && !sliderEl) sliderEl = el;
    }
    if (bgEl) {
        const bs = window.getComputedStyle(bgEl);
        const match = bs.backgroundImage.match(/url\\(["']?(.*?)["']?\\)/);
        result.bg_url = match ? match[1] : null;
        result.bg_w = bgEl.offsetWidth;
        result.bg_h = bgEl.offsetHeight;
    }
    if (sliderEl) {
        const ss = window.getComputedStyle(sliderEl);
        const match = ss.backgroundImage.match(/url\\(["']?(.*?)["']?\\)/);
        result.slider_url = match ? match[1] : null;
        result.slider_w = sliderEl.offsetWidth;
        result.slider_h = sliderEl.offsetHeight;
        result.slider_left = sliderEl.offsetLeft;
        const bsParts = ss.backgroundSize.split(/\\s+/);
        result.bg_size_width = parseFloat(bsParts[0]) || 0;
        result.bg_size_height = parseFloat(bsParts[1]) || 0;
        const bpParts = ss.backgroundPosition.split(/\\s+/);
        result.bg_pos_x = parseFloat(bpParts[0]) || 0;
        result.bg_pos_y = parseFloat(bpParts[1]) || 0;
    }
    return result;
}"""

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
window.chrome = {runtime: {}};
const origQuery = navigator.permissions.query;
navigator.permissions.query = (params) =>
    params.name === 'notifications' ?
        Promise.resolve({state: Notification.permission}) :
        origQuery(params);
"""


class BuiltinCaptchaSolver:
    """使用 OpenCV 边缘检测找滑块缺口（无需外部包）"""

    @staticmethod
    def solve(bg_bytes, css_info=None):
        try:
            import cv2
            import numpy as np
        except ImportError:
            print("  [Captcha] opencv not installed, cannot solve locally")
            return None

        try:
            np_arr = np.frombuffer(bg_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img is None:
                return None

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)

            h, w = edges.shape
            display_w = int(css_info.get("bg_w", 0)) if css_info else 0
            if display_w <= 0:
                display_w = 340
            scale = display_w / w

            # 垂直投影：统计每列的边缘密度
            col_density = np.sum(edges, axis=0)

            # 找边缘密度最低的区间（缺口位置）
            min_density = float("inf")
            gap_x = 50
            window = int(w * 0.08)  # 滑块宽度约 8% 图像宽度
            for x in range(window, w - window):
                density = np.sum(col_density[x - window // 2 : x + window // 2])
                density_avg = density / window
                if density_avg < min_density:
                    min_density = density_avg
                    gap_x = x

            slider_offset = int(css_info.get("slider_left", 0)) if css_info else 0
            if slider_offset > 100 or slider_offset <= 0:
                slider_offset = 25
            final_x = int((gap_x * scale) - slider_offset)
            final_x = max(30, min(final_x, 280))
            return final_x
        except Exception as e:
            print(f"  [Captcha] solve error: {e}")
            return None


class CapsolverSolver:
    """使用 Capsolver API 解验证码（付费，成功率 95%+）"""

    BASE = "https://api.capsolver.com"

    @staticmethod
    def solve(bg_url, page_obj=None):
        if not CAPSOLVER_KEY:
            return None
        try:
            r = http_req.post(f"{CapsolverSolver.BASE}/createTask", json={
                "clientKey": CAPSOLVER_KEY,
                "task": {
                    "type": "TencentCaptcha",
                    "websiteURL": "https://www.oiioii.ai",
                    "appId": "2081732914425521",
                }
            }, timeout=30)
            task_id = r.json().get("taskId")
            if not task_id:
                return None

            for _ in range(30):
                time.sleep(2)
                r2 = http_req.post(f"{CapsolverSolver.BASE}/getTaskResult", json={
                    "clientKey": CAPSOLVER_KEY,
                    "taskId": task_id,
                }, timeout=15)
                data = r2.json()
                if data.get("status") == "ready":
                    return data.get("solution", {}).get("ticket")
                if data.get("status") == "failed":
                    return None
            return None
        except Exception as e:
            print(f"  [Capsolver] error: {e}")
            return None


def _download_image(url):
    if not url:
        return None
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        if url.startswith("data:image"):
            b64 = url.split(",", 1)[1] if "," in url else ""
            return base64.b64decode(b64)
        r = http_req.get(url, headers=headers, timeout=15)
        if r.status_code == 200 and len(r.content) > 1000:
            return r.content
    except Exception:
        pass
    return None


def _generate_tracks(distance):
    tracks = []
    current = 0
    mid = distance * random.uniform(0.5, 0.7)
    v = 0
    while current < distance:
        a = random.randint(4, 8) if current < mid else -random.randint(3, 6)
        v = max(1, v + a * 0.08)
        move = v * 0.08 + 0.5 * a * 0.08 * 0.08
        current += move
        tracks.append(round(move, 1))
    overshoot = random.randint(-3, 8)
    if overshoot:
        tracks.append(overshoot)
    if overshoot > 0:
        tracks.append(-overshoot - random.randint(1, 3))
    tracks.append(0)
    return tracks


async def _wait_for_captcha(page, timeout=20):
    """等待验证码出现"""
    selectors = [
        ".tcaptcha", ".yidun_slider", ".nc_iconfont",
        '[class*="captcha"]', '[class*="turing"]',
        "#tcaptcha_iframe", '[id*="captcha"]',
        '[class*="verify"]', '[class*="slider-btn"]',
        '[class*="drag"]',
    ]
    for _ in range(timeout):
        for sel in selectors:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    return True
            except Exception:
                continue
        canvases = await page.query_selector_all("canvas")
        for c in canvases:
            try:
                box = await c.bounding_box()
                if box and box["width"] > 100 and box["height"] > 50:
                    return True
            except Exception:
                continue
        await page.wait_for_timeout(1000)
    return False


async def _find_slider_btn(page):
    btn_selectors = [
        ".tcaptcha-btn", ".yidun_slider__icon", ".nc-lang-cnt",
        "#tcaptcha_drag_button", '[class*="drag"] [class*="btn"]',
        '[class*="slider"] [class*="icon"]', '[class*="handler"]',
        '[role="slider"]', ".slide-btn",
    ]
    for sel in btn_selectors:
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                return el
        except Exception:
            continue
    frames = page.frames
    for frame in frames:
        try:
            el = await frame.query_selector('[class*="btn"], [class*="drag"], [class*="handle"]')
            if el and await el.is_visible():
                return el
        except Exception:
            continue
    return None


async def _solve_slider_captcha(page, max_attempts=5):
    """解滑动验证码"""
    # 如果 capsolver 可用，优先用它
    if CAPSOLVER_KEY:
        ticket = CapsolverSolver.solve(None, page)
        if ticket:
            return True

    solver = BuiltinCaptchaSolver()

    for attempt in range(max_attempts):
        try:
            css_info = await page.evaluate(CAPTCHA_JS)
            bg_url = css_info.get("bg_url") if isinstance(css_info, dict) else None
            if not bg_url:
                await page.wait_for_timeout(2000)
                continue

            if bg_url.startswith("//"):
                bg_url = "https:" + bg_url
            elif not bg_url.startswith("http") and not bg_url.startswith("data"):
                bg_url = "https://" + bg_url

            bg_bytes = _download_image(bg_url)
            if not bg_bytes or len(bg_bytes) < 1000:
                await page.wait_for_timeout(2000)
                continue

            drag_x = solver.solve(bg_bytes, css_info)
            if drag_x is None or drag_x <= 0:
                drag_x = random.randint(100, 220)

            slider_btn = await _find_slider_btn(page)
            if not slider_btn:
                await page.wait_for_timeout(2000)
                continue

            btn_box = await slider_btn.bounding_box()
            if not btn_box:
                continue

            start_x = btn_box["x"] + btn_box["width"] / 2
            start_y = btn_box["y"] + btn_box["height"] / 2

            track_width = css_info.get("bg_w", 340) if css_info else 340
            scale = track_width / 340 if track_width > 0 else 1.0
            scaled = int(drag_x * scale)
            scaled = max(scaled, 50)

            tracks = _generate_tracks(scaled)

            await page.mouse.move(start_x, start_y)
            await page.wait_for_timeout(random.randint(100, 300))
            await page.mouse.down()
            await page.wait_for_timeout(random.randint(50, 150))

            moved = 0
            for move in tracks:
                if move == 0:
                    continue
                moved += move
                await page.mouse.move(start_x + moved, start_y + random.randint(-2, 2))
                await page.wait_for_timeout(random.randint(6, 25))

            await page.wait_for_timeout(5000)

            if "login" not in page.url.lower():
                return True

            captcha_el = await _wait_for_captcha(page, timeout=1)
            if not captcha_el:
                return True

            try:
                refresh_btn = await page.query_selector('[class*="refresh"], [title*="刷新"]')
                if refresh_btn:
                    await refresh_btn.click()
                    await page.wait_for_timeout(2000)
            except Exception:
                pass

        except Exception as e:
            print(f"  [Captcha] attempt {attempt+1} error: {e}")
        await page.wait_for_timeout(1000)

    return False


# ====================================================================
# 浏览器注册
# ====================================================================
async def _register_browser(email, password):
    """用 Playwright 打开 Oiioii 注册页，填表注册"""
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            locale="zh-CN",
        )
        await context.add_init_script(STEALTH_JS)
        page = await context.new_page()

        try:
            print("    打开 Oiioii 登录页...")
            await page.goto("https://www.oiioii.ai/login", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)

            # 点 Email 标签
            email_tab = page.locator("button:has-text('Email')")
            await email_tab.click(timeout=15000)
            await page.wait_for_timeout(2000)

            # 填邮箱
            email_input = page.locator("input[name='email']")
            await email_input.click()
            await page.wait_for_timeout(random.randint(200, 500))
            for char in email:
                await page.keyboard.type(char, delay=random.randint(30, 80))

            await page.wait_for_timeout(random.randint(200, 500))

            # 填密码
            pwd_input = page.locator("input[name='password']")
            await pwd_input.click()
            await page.wait_for_timeout(random.randint(200, 500))
            for char in password:
                await page.keyboard.type(char, delay=random.randint(30, 80))

            await page.wait_for_timeout(1000)

            # 点注册按钮
            submit_btn = page.locator("button:has-text('Login / Sign up')")
            await submit_btn.click()
            await page.wait_for_timeout(5000)

            # 处理验证码
            captcha = await _wait_for_captcha(page, timeout=20)
            if captcha:
                print("    验证码出现，尝试解决...")
                solved = await _solve_slider_captcha(page, max_attempts=5)
                if not solved:
                    print("    ✗ 验证码解了5次都没过")
                    return False
                await page.wait_for_timeout(3000)

            # 检查是否注册成功
            if "login" not in page.url.lower():
                print("    注册成功（已跳转）")
                return True

            # 关掉可能出现的弹窗
            try:
                close_btn = page.locator('button:has-text("Skip"), button:has-text("跳过"), button[aria-label="Close"]').first
                await close_btn.click(timeout=5000)
                await page.wait_for_timeout(2000)
            except Exception:
                pass

            ok = "login" not in page.url.lower()
            print(f"    {'注册成功' if ok else '注册失败（还在登录页）'}")
            return ok

        except Exception as e:
            print(f"    浏览器注册异常: {e}")
            return False
        finally:
            await context.close()
            await browser.close()


# ====================================================================
# 注册 + 签到 + 获取积分
# ====================================================================
def register_one():
    """完整注册流程：临时邮箱 → 浏览器注册 → 验证邮箱 → 签到 → 查积分"""
    print("  [1/5] 创建临时邮箱...")
    email, password = TempMail.create()
    if not email:
        return {"success": False, "error": "TempMail creation failed"}
    print(f"  [2/5] email: {email}")

    # 获取 mail.tm token，用于之后收验证邮件
    mail_token = TempMail.get_token(email, password)

    print("  [3/5] 浏览器注册...")
    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        reg_ok = loop.run_until_complete(_register_browser(email, password))
        loop.close()
    except Exception as e:
        print(f"  [3/5] 浏览器异常: {e}")
        return {"success": False, "error": f"Browser error: {e}"}

    if not reg_ok:
        return {"success": False, "error": "Browser registration failed"}

    print("  [4/5] 验证邮箱...")
    if mail_token:
        verify_link = TempMail.poll_verify_link(mail_token, timeout=90)
        if verify_link:
            try:
                http_req.get(verify_link, timeout=15, allow_redirects=True)
                print("    邮箱已验证")
            except Exception:
                print("    验证链接访问失败，可能已自动验证")
        else:
            print("    未收到验证邮件，继续")
    else:
        print("    无法获取 mail.tm token，跳过验证")

    print("  [5/5] 登录获取积分...")
    r = http_req.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        json={"email": email, "password": password, "gotrue_meta_security": {}},
        headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
        timeout=15,
    )
    if r.status_code != 200:
        print(f"    登录失败 (HTTP {r.status_code})")
        return {
            "success": True,
            "email": email,
            "password": password,
            "token": "",
            "points": 0,
            "workspace_id": "",
            "note": "注册成功但Supabase登录失败，可手动添加",
        }

    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 激活 + 积分
    http_req.post(f"{API_BASE}/points/active_user", json={"data": {}}, headers=headers, timeout=15)

    r_pts = http_req.post(f"{API_BASE}/points/current_user_points", json={"data": {}}, headers=headers, timeout=15)
    points = r_pts.json().get("data", {}).get("available_limited", 0)
    print(f"    积分: {points}")

    # 创建工作区
    r_ws = http_req.post(f"{API_BASE}/workspace/create_workspace", json={"data": {"name": "pool"}}, headers=headers, timeout=15)
    ws_id = r_ws.json().get("data", {}).get("workspaceId", "")
    if not ws_id:
        r_ws2 = http_req.post(f"{API_BASE}/workspace/workspace_list", json={"data": {"limit": 10}}, headers=headers, timeout=15)
        workspaces = r_ws2.json().get("data", {}).get("workspaces", [])
        if workspaces:
            ws_id = workspaces[0].get("workspaceId", "")

    print(f"    工作区: {ws_id or '无'}")

    return {
        "success": True,
        "email": email,
        "password": password,
        "token": token,
        "points": points,
        "workspace_id": ws_id,
    }


# ====================================================================
# 推送到服务器
# ====================================================================
def push_to_server(email, password):
    try:
        r = http_req.post(
            f"{SERVER_URL}/pool/api/pool/add",
            json={"email": email, "password": password},
            timeout=30,
        )
        if r.status_code == 200:
            data = r.json()
            print(f"    ✓ 推送到服务器: account_id={data.get('account_id')}, points={data.get('points')}")
            return True
        else:
            print(f"    ✗ 推送失败 (HTTP {r.status_code})")
            return False
    except Exception as e:
        print(f"    ✗ 推送异常: {e}")
        return False


# ====================================================================
# 主流程
# ====================================================================
def do_register(index, total):
    tag = f"[{index+1}/{total}]"
    print(f"\n{tag} {'='*40}")
    print(f"{tag} 开始注册 #{index+1}")
    print(f"{tag} {'='*40}")

    start = time.time()
    result = register_one()
    elapsed = time.time() - start

    if not result["success"]:
        print(f"{tag} ✗ 失败 ({elapsed:.0f}s): {result.get('error', '?')}")
        return {"index": index, "success": False, "error": result.get("error", "")}

    email = result.get("email", "")
    points = result.get("points", 0)
    print(f"{tag} ✓ 成功! {email} 积分:{points} ({elapsed:.0f}s)")

    pushed = push_to_server(email, result.get("password", ""))

    return {
        "index": index,
        "success": True,
        "email": email,
        "points": points,
        "pushed": pushed,
    }


def print_summary(results):
    ok = [r for r in results if r.get("success")]
    fail = [r for r in results if not r.get("success")]
    pushed = [r for r in ok if r.get("pushed")]

    print("\n" + "=" * 50)
    print(f"  完成! 成功:{len(ok)}  失败:{len(fail)}  已推送:{len(pushed)}")
    for f in fail[:5]:
        print(f"    - {f.get('error', '?')}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="在 GitHub Actions 上注册 Oiioii 账号")
    parser.add_argument("--count", type=int, default=5, help="注册数量")
    parser.add_argument("--continuous", action="store_true", help="连续模式")
    parser.add_argument("--target", type=int, default=50, help="连续模式目标")
    parser.add_argument("--concurrent", type=int, default=1, help="并发数(1-3)")
    args = parser.parse_args()

    print("=" * 50)
    print("  Oiioii 自动注册机")
    print(f"  服务器: {SERVER_URL}")
    print(f"  验证码: {'Capsolver' if CAPSOLVER_KEY else 'OpenCV(内置)'}")
    print("=" * 50)

    count = args.target if args.continuous else args.count
    results = []

    for i in range(count):
        r = do_register(i, count)
        results.append(r)
        if i < count - 1:
            wait = 5 if r["success"] else 10
            print(f"  等待 {wait}s...")
            time.sleep(wait)

    print_summary(results)

    # 保存结果
    out = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "server": SERVER_URL,
        "total": len(results),
        "success": len([r for r in results if r.get("success")]),
        "failed": len([r for r in results if not r.get("success")]),
        "pushed": len([r for r in results if r.get("pushed")]),
    }
    with open("register_result.json", "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\n结果保存到 register_result.json")


if __name__ == "__main__":
    main()