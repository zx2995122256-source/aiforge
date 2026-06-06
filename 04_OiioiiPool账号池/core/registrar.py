import time
import random
import string
import re
import json
import base64
import requests
from typing import Optional, Tuple
from config import MAIL_TM_API, SUPABASE_URL, SUPABASE_ANON_KEY, API_BASE


class TempMailHelper:
    @staticmethod
    def create() -> Tuple[Optional[str], Optional[str]]:
        try:
            r = requests.get(f"{MAIL_TM_API}/domains", timeout=10)
            domains = r.json().get("hydra:member", [])
            if not domains:
                return None, None
            domain = domains[0]["domain"]
            rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
            email = f"oiio_{rand}@{domain}"
            password = f"Oi{rand}!Pass1"
            r = requests.post(
                f"{MAIL_TM_API}/accounts",
                json={"address": email, "password": password}, timeout=15
            )
            if r.status_code == 201:
                return email, password
        except Exception:
            pass
        return None, None

    @staticmethod
    def get_token(email: str, password: str) -> Optional[str]:
        try:
            r = requests.post(
                f"{MAIL_TM_API}/token",
                json={"address": email, "password": password}, timeout=10
            )
            if r.status_code == 200:
                return r.json()["token"]
        except Exception:
            pass
        return None

    @staticmethod
    def poll_verify_link(mail_token: str, timeout: int = 120) -> Optional[str]:
        headers = {"Authorization": f"Bearer {mail_token}"}
        start = time.time()
        while time.time() - start < timeout:
            try:
                r = requests.get(f"{MAIL_TM_API}/messages", headers=headers, timeout=10)
                msgs = r.json().get("hydra:member", [])
                for msg in msgs:
                    msg_id = msg.get("id")
                    r2 = requests.get(
                        f"{MAIL_TM_API}/messages/{msg_id}",
                        headers=headers, timeout=10
                    )
                    html = r2.json().get("html", [])
                    html_content = html[0] if isinstance(html, list) and html else (html or "")
                    links = re.findall(
                        r'https?://[^\s"\'<>]+(?:confirm|verify|token)[^\s"\'<>]*',
                        html_content, re.IGNORECASE
                    )
                    if not links:
                        all_links = re.findall(r'https?://[^\s"\'<>]+', html_content)
                        links = [l for l in all_links if "oiioii" in l or "supabase" in l]
                    if links:
                        return links[0].replace("&amp;", "&")
            except Exception:
                pass
            time.sleep(5)
        return None


class TencentCaptchaSolver:
    def __init__(self):
        self._slider = None

    def _get_slider(self):
        if self._slider is None:
            try:
                from captcha_recognizer.slider import Slider
                self._slider = Slider()
            except ImportError:
                from captcha_recognizer import Slider
                self._slider = Slider()
        return self._slider

    def solve(self, bg_bytes: bytes, css_info: dict = None) -> Optional[int]:
        try:
            import cv2
            import numpy as np
            np_arr = np.frombuffer(bg_bytes, np.uint8)
            raw_bg = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if raw_bg is None:
                return None
            original_w = raw_bg.shape[1]
            display_w = int(css_info.get("bg_w", 0)) if css_info else 0
            if display_w <= 0:
                display_w = 330
            scale = display_w / original_w

            box, confidence = self._get_slider().identify(source=bg_bytes)
            if confidence < 0.5:
                return None

            gap_x = int(box[0])
            slider_offset = int(css_info.get("slider_left", 0)) if css_info else 0
            if slider_offset > 100 or slider_offset <= 0:
                slider_offset = 25
            final_x = int((gap_x * scale) - slider_offset)
            if final_x < 20:
                final_x = 50
            if final_x > 280:
                final_x = 250
            return final_x
        except Exception as e:
            print(f"Captcha solve error: {e}")
            return None


_CAPTCHA_JS = """() => {
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

_STEALTH_JS = """
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


class PlaywrightRegistrar:
    def __init__(self):
        self._browser = None
        self._playwright = None

    async def _ensure_browser(self):
        if self._browser is None:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )

    async def register(self, email: str, password: str) -> bool:
        await self._ensure_browser()
        context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            locale="zh-CN",
        )
        await context.add_init_script(_STEALTH_JS)
        page = await context.new_page()

        try:
            await page.goto("https://www.oiioii.ai/login", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)

            # 点 Email/邮箱 标签
            email_tabs = [
                page.locator("button:has-text('Email')"),
                page.locator("button:has-text('邮箱')"),
                page.locator("button:has-text('email')"),
            ]
            email_tab = None
            for tab in email_tabs:
                try:
                    if await tab.is_visible(timeout=3000):
                        email_tab = tab
                        break
                except Exception:
                    continue
            if email_tab:
                await email_tab.click()
            await page.wait_for_timeout(2000)

            email_input = page.locator("input[name='email']")
            await email_input.click()
            await page.wait_for_timeout(random.randint(200, 500))
            for char in email:
                await page.keyboard.type(char, delay=random.randint(30, 80))

            await page.wait_for_timeout(random.randint(200, 500))

            pwd_input = page.locator("input[name='password']")
            await pwd_input.click()
            await page.wait_for_timeout(random.randint(200, 500))
            for char in password:
                await page.keyboard.type(char, delay=random.randint(30, 80))

            await page.wait_for_timeout(1000)

            submit_btns = [
                page.locator("button:has-text('Login / Sign up')"),
                page.locator("button:has-text('Sign up')"),
                page.locator("button:has-text('注册')"),
                page.locator("button:has-text('Register')"),
                page.locator("button[type='submit']"),
            ]
            submit_btn = None
            for btn in submit_btns:
                try:
                    if await btn.is_visible(timeout=3000):
                        submit_btn = btn
                        break
                except Exception:
                    continue
            if submit_btn:
                await submit_btn.click()
            await page.wait_for_timeout(5000)

            captcha_appeared = await self._wait_for_captcha(page, timeout=20)
            if captcha_appeared:
                solved = await self._solve_captcha(page, max_attempts=5)
                if not solved:
                    print("Captcha not solved after max attempts")
                    return False

            await page.wait_for_timeout(3000)

            if "login" not in page.url.lower():
                return True

            try:
                close_btn = page.locator('button:has-text("Skip"), button:has-text("跳过"), button[aria-label="Close"]').first
                await close_btn.click(timeout=5000)
                await page.wait_for_timeout(2000)
            except Exception:
                pass

            return "login" not in page.url.lower()

        except Exception as e:
            print(f"Registration error: {e}")
            return False
        finally:
            await context.close()

    async def _wait_for_captcha(self, page, timeout=20) -> bool:
        selectors = [
            '.tcaptcha', '.yidun_slider', '.nc_iconfont',
            '[class*="captcha"]', '[class*="turing"]',
            '#tcaptcha_iframe', '[id*="captcha"]',
            '[class*="verify"]', '[class*="slider-btn"]',
            '[class*="drag"]',
        ]
        for i in range(timeout):
            for sel in selectors:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        return True
                except Exception:
                    continue
            canvases = await page.query_selector_all('canvas')
            for c in canvases:
                try:
                    box = await c.bounding_box()
                    if box and box['width'] > 100 and box['height'] > 50:
                        return True
                except Exception:
                    continue
            await page.wait_for_timeout(1000)
        return False

    async def _solve_captcha(self, page, max_attempts=5) -> bool:
        solver = TencentCaptchaSolver()

        for attempt in range(max_attempts):
            try:
                css_info = await page.evaluate(_CAPTCHA_JS)
                bg_url = css_info.get("bg_url") if isinstance(css_info, dict) else None

                if not bg_url:
                    print(f"Captcha attempt {attempt+1}: no bg_url found")
                    await page.wait_for_timeout(2000)
                    continue

                if bg_url.startswith("//"):
                    bg_url = "https:" + bg_url
                elif bg_url.startswith("data:image"):
                    pass
                else:
                    if not bg_url.startswith("http"):
                        bg_url = "https://" + bg_url

                bg_bytes = self._download_image(bg_url)
                if not bg_bytes or len(bg_bytes) < 1000:
                    print(f"Captcha attempt {attempt+1}: bg download failed ({len(bg_bytes) if bg_bytes else 0} bytes)")
                    await page.wait_for_timeout(2000)
                    continue

                drag_x = solver.solve(bg_bytes, css_info)
                if drag_x is None or drag_x <= 0:
                    drag_x = random.randint(100, 220)
                    print(f"Captcha attempt {attempt+1}: fallback drag_x={drag_x}")
                else:
                    print(f"Captcha attempt {attempt+1}: drag_x={drag_x}")

                slider_btn = await self._find_slider_button(page)
                if not slider_btn:
                    print(f"Captcha attempt {attempt+1}: no slider button found")
                    await page.wait_for_timeout(2000)
                    continue

                btn_box = await slider_btn.bounding_box()
                if not btn_box:
                    continue

                start_x = btn_box['x'] + btn_box['width'] / 2
                start_y = btn_box['y'] + btn_box['height'] / 2

                track_width = css_info.get("bg_w", 340) if css_info else 340
                scale_ratio = track_width / 340 if track_width > 0 else 1.0
                scaled_gap = int(drag_x * scale_ratio)
                scaled_gap = max(scaled_gap, 50)

                tracks = self._generate_human_trajectory(scaled_gap)

                await page.mouse.move(start_x, start_y)
                await page.wait_for_timeout(random.randint(100, 300))
                await page.mouse.down()
                await page.wait_for_timeout(random.randint(50, 150))

                total_moved = 0
                for i, move in enumerate(tracks):
                    if move == 0:
                        if i == len(tracks) - 1:
                            await page.wait_for_timeout(random.randint(50, 150))
                            await page.mouse.up()
                        continue
                    total_moved += move
                    await page.mouse.move(
                        start_x + total_moved,
                        start_y + random.randint(-2, 2),
                    )
                    delay = random.uniform(0.006, 0.025)
                    if move < 0:
                        delay = random.uniform(0.01, 0.04)
                    await page.wait_for_timeout(int(delay * 1000))

                await page.wait_for_timeout(5000)

                if "login" not in page.url.lower():
                    return True

                try:
                    success_sels = ['text=验证通过', 'text=验证成功', 'text=success']
                    for sel in success_sels:
                        el = await page.query_selector(sel)
                        if el and await el.is_visible():
                            return True
                except Exception:
                    pass

                captcha_el = await self._wait_for_captcha(page, timeout=1)
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
                print(f"Captcha attempt {attempt+1} error: {e}")

            await page.wait_for_timeout(1000)

        return False

    async def _find_slider_button(self, page):
        btn_selectors = [
            '.tcaptcha-btn', '.yidun_slider__icon', '.nc-lang-cnt',
            '#tcaptcha_drag_button', '[class*="drag"] [class*="btn"]',
            '[class*="slider"] [class*="icon"]', '[class*="handler"]',
            '[role="slider"]', '.slide-btn',
        ]
        for sel in btn_selectors:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    return el
            except Exception:
                continue

        all_divs = await page.query_selector_all('div, span')
        for div in all_divs:
            try:
                cls = await div.get_attribute("class") or ""
                box = await div.bounding_box()
                if box and any(kw in cls.lower() for kw in ["btn", "icon", "handle", "drag", "slider", "arrow"]):
                    if 25 < box['width'] < 70 and 25 < box['height'] < 70:
                        return div
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

    @staticmethod
    def _download_image(url):
        if not url:
            return None
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.oiioii.ai/',
        }
        try:
            if url.startswith('data:image'):
                b64 = url.split(',', 1)[1] if ',' in url else ''
                return base64.b64decode(b64)
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200 and len(r.content) > 1000:
                return r.content
        except Exception as e:
            print(f"Download image error: {e}")
        return None

    @staticmethod
    def _generate_human_trajectory(distance):
        tracks = []
        current = 0
        mid = distance * random.uniform(0.5, 0.7)
        t = 0.08
        v = 0
        while current < distance:
            if current < mid:
                a = random.randint(4, 8)
            else:
                a = -random.randint(3, 6)
            v0 = v
            v = v0 + a * t
            if v < 0:
                v = random.randint(1, 3)
            move = v0 * t + 0.5 * a * t * t
            current += move
            tracks.append(round(move, 1))
        overshoot = random.randint(-3, 8)
        if overshoot != 0:
            tracks.append(overshoot)
        if overshoot > 0:
            tracks.append(-overshoot - random.randint(1, 3))
        tracks.append(0)
        return tracks

    async def close(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


def auto_register_sync(email: str = None, password: str = None) -> dict:
    import asyncio
    import threading

    if not email or not password:
        email, password = TempMailHelper.create()
        if not email:
            return {"success": False, "error": "Failed to create temp email"}

    mail_token = TempMailHelper.get_token(email, password)

    reg_ok = False
    reg_error = ""

    def _run_in_thread():
        nonlocal reg_ok, reg_error
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                registrar = PlaywrightRegistrar()
                reg_ok = loop.run_until_complete(registrar.register(email, password))
            finally:
                loop.run_until_complete(registrar.close())
                loop.close()
        except Exception as e:
            reg_error = str(e)

    t = threading.Thread(target=_run_in_thread, daemon=True)
    t.start()
    t.join(timeout=180)

    if t.is_alive():
        return {"success": False, "error": "Registration timed out (180s)"}

    if not reg_ok:
        return {"success": False, "error": reg_error or "Playwright registration failed"}

    if mail_token:
        verify_link = TempMailHelper.poll_verify_link(mail_token, timeout=90)
        if verify_link:
            try:
                requests.get(verify_link, timeout=15, allow_redirects=True)
            except Exception:
                pass

    r = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        json={"email": email, "password": password, "gotrue_meta_security": {}},
        headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
        timeout=15
    )
    if r.status_code != 200:
        return {"success": False, "error": f"Login after register failed: {r.status_code}"}

    token = r.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    requests.post(f"{API_BASE}/points/active_user", json={"data": {}}, headers=headers, timeout=15)

    r_pts = requests.post(f"{API_BASE}/points/current_user_points", json={"data": {}}, headers=headers, timeout=15)
    points = r_pts.json().get("data", {}).get("available_limited", 0)

    r_ws = requests.post(f"{API_BASE}/workspace/create_workspace", json={"data": {"name": "pool"}}, headers=headers, timeout=15)
    workspace_id = r_ws.json().get("data", {}).get("workspaceId", "")
    if not workspace_id:
        r_ws2 = requests.post(f"{API_BASE}/workspace/workspace_list", json={"data": {"limit": 10}}, headers=headers, timeout=15)
        workspaces = r_ws2.json().get("data", {}).get("workspaces", [])
        if workspaces:
            workspace_id = workspaces[0].get("workspaceId", "")

    return {
        "success": True,
        "email": email,
        "password": password,
        "token": token,
        "points": points,
        "workspace_id": workspace_id
    }
