#!/usr/bin/env python3
"""
Batch register oiioii accounts - concurrent with proxy rotation.
Uses free proxy sources + multiple temp email services to avoid rate limits.
"""
import requests
import json
import time
import random
import string
import re
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

MAIL_TM = "https://api.mail.tm"
MAIL_GW = "https://api.guerrillamail.com/ajax.php"
SUPABASE = "https://spb.oiioii.ai"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVndnV6ZXN0eXlwYm1jZnVycmJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEyMTU4NTEsImV4cCI6MjA3Njc5MTg1MX0.Z1qdxtK0PLF5NV1yXrI9s_W2Hurdxo143DBzuUuajh0"
OIIOII_API = "https://api.oiioii.ai"

TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 200
WORKERS = int(sys.argv[2]) if len(sys.argv) > 2 else 3  # 并发数，默认3
ACCOUNTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "accounts.json")

# 线程安全
lock = threading.Lock()
success_count = 0
fail_count = 0
proxy_list = []
proxy_index = 0

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}", flush=True)

# ============ Proxy Management ============

def fetch_free_proxies():
    """从多个免费代理源获取代理列表"""
    proxies = []
    sources = [
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    ]
    for url in sources:
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                for line in r.text.strip().split('\n'):
                    line = line.strip()
                    if ':' in line and len(line) < 30:
                        proxies.append(f"http://{line}")
                log(f"  Got {len([p for p in proxies if url.split('/')[-1] in str(p)])} proxies from {url.split('/')[-1][:20]}")
        except Exception as e:
            log(f"  Proxy source failed: {e}")
    # 去重
    proxies = list(set(proxies))
    log(f"Total proxies loaded: {len(proxies)}")
    return proxies

def get_proxy_session():
    """获取一个带代理的session，轮换代理"""
    global proxy_index
    if not proxy_list:
        return requests.Session()
    
    with lock:
        idx = proxy_index % len(proxy_list)
        proxy_index += 1
        proxy = proxy_list[idx]
    
    session = requests.Session()
    session.proxies = {"http": proxy, "https": proxy}
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    return session

def test_proxy(proxy_str):
    """测试代理是否可用"""
    try:
        r = requests.get("https://httpbin.org/ip", proxies={"http": proxy_str, "https": proxy_str}, timeout=8)
        return r.status_code == 200
    except:
        return False

def filter_working_proxies(max_test=50):
    """筛选可用代理"""
    global proxy_list
    if not proxy_list:
        return
    log(f"Testing {min(len(proxy_list), max_test)} proxies...")
    working = []
    test_list = proxy_list[:max_test]
    
    def test_one(p):
        if test_proxy(p):
            working.append(p)
    
    with ThreadPoolExecutor(max_workers=10) as ex:
        list(ex.map(test_one, test_list))
    
    proxy_list = working
    log(f"Working proxies: {len(proxy_list)}")

# ============ Email Services ============

def create_email_mailtm(session):
    """mail.tm 创建临时邮箱"""
    try:
        r = session.get(f"{MAIL_TM}/domains", timeout=10)
        domains = r.json().get("hydra:member", [])
        domain = domains[0]["domain"] if domains else "mail.tm"
        rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
        email = f"oiio_{rand}@{domain}"
        pwd = f"Oi{rand}!Pass1"
        r = session.post(f"{MAIL_TM}/accounts", json={"address": email, "password": pwd}, timeout=15)
        if r.status_code == 201:
            return email, pwd, "mailtm"
    except:
        pass
    return None, None, None

def create_email_guerrilla(session):
    """guerrillamail 创建临时邮箱"""
    try:
        rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
        r = session.get(f"{MAIL_GW}?f=get_email_address&lang=en&site=guerrillamail.com", timeout=10)
        if r.status_code == 200:
            data = r.json()
            base_email = data.get("email_addr", "")
            if base_email:
                # guerrillamail用sid_token管理
                sid = data.get("sid_token", "")
                return base_email, sid, "guerrilla"
    except:
        pass
    return None, None, None

def create_temp_email():
    """轮换使用不同邮箱服务"""
    session = get_proxy_session()
    
    # 随机选择邮箱服务
    services = [create_email_mailtm, create_email_guerrilla]
    random.shuffle(services)
    
    for svc in services:
        email, pwd, svc_name = svc(session)
        if email:
            return email, pwd, svc_name
        # 换个代理重试
        session = get_proxy_session()
    
    # 最后不使用代理试试
    try:
        rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
        r = requests.get(f"{MAIL_TM}/domains", timeout=10)
        domains = r.json().get("hydra:member", [])
        domain = domains[0]["domain"] if domains else "mail.tm"
        email = f"oiio_{rand}@{domain}"
        pwd = f"Oi{rand}!Pass1"
        r = requests.post(f"{MAIL_TM}/accounts", json={"address": email, "password": pwd}, timeout=15)
        if r.status_code == 201:
            return email, pwd, "mailtm_direct"
    except:
        pass
    
    return None, None, None

# ============ Registration ============

def poll_verify_mailtm(email, pwd, timeout=90):
    """轮询mail.tm验证链接"""
    try:
        r = requests.post(f"{MAIL_TM}/token", json={"address": email, "password": pwd}, timeout=10)
        if r.status_code != 200:
            return False
        mail_token = r.json()["token"]
        headers = {"Authorization": f"Bearer {mail_token}"}
        start = time.time()
        while time.time() - start < timeout:
            try:
                r = requests.get(f"{MAIL_TM}/messages", headers=headers, timeout=10)
                msgs = r.json().get("hydra:member", [])
                for msg in msgs:
                    from_addr = msg.get("from", {}).get("address", "")
                    if "oiioii" in from_addr or "supabase" in from_addr:
                        msg_id = msg.get("id")
                        r2 = requests.get(f"{MAIL_TM}/messages/{msg_id}", headers=headers, timeout=10)
                        html = r2.json().get("html", "")
                        if isinstance(html, list):
                            html = html[0]
                        links = re.findall(r'https?://[^\s"\'<>]+confirm[^\s"\'<>]*', html)
                        if not links:
                            links = re.findall(r'https?://[^\s"\'<>]*supabase[^\s"\'<>]*token[^\s"\'<>]*', html)
                        if not links:
                            all_links = re.findall(r'https?://[^\s"\'<>]+', html)
                            links = [l for l in all_links if "oiioii" in l or "supabase" in l]
                        if links:
                            verify_url = links[0].replace("&amp;", "&")
                            requests.get(verify_url, timeout=15, allow_redirects=True)
                            return True
            except:
                pass
            time.sleep(5)
    except:
        pass
    return False

def signup_via_supabase(email, password, session=None):
    """Supabase注册"""
    s = session or get_proxy_session()
    try:
        r = s.post(f"{SUPABASE}/auth/v1/signup", json={
            "email": email,
            "password": password,
            "data": {"language": "zh", "nickname": email.split("@")[0]}
        }, headers={"apikey": ANON_KEY, "Content-Type": "application/json"}, timeout=20)
        return r.status_code, r.json()
    except Exception as e:
        return 0, {"error": str(e)}

def login_oiioii(email, password, session=None):
    """Oiioii登录/注册"""
    s = session or get_proxy_session()
    try:
        r = s.post(f"{OIIOII_API}/auth/signin_with_password", json={
            "email": email, "password": password, "tencentCaptcha": None,
            "inviteCode": "", "language": "zh", "nickname": email.split("@")[0],
            "signupOnNotFound": True
        }, headers={"Content-Type": "application/json"}, timeout=20)
        if r.status_code == 200:
            token = r.json().get("data", {}).get("access_token", r.json().get("access_token", ""))
            return token
    except:
        pass
    return None

def get_workspace(token):
    try:
        H = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        r = requests.post(f"{OIIOII_API}/workspace/create_workspace", json={"data": {"name": "default"}}, headers=H, timeout=15)
        ws_id = r.json().get("data", {}).get("workspaceId")
        if not ws_id:
            r = requests.post(f"{OIIOII_API}/workspace/workspace_list", json={"data": {"limit": 10}}, headers=H, timeout=15)
            try:
                ws_id = r.json()["data"]["workspaces"][0]["workspaceId"]
            except:
                ws_id = None
        return ws_id
    except:
        return None

def claim_points(token):
    try:
        H = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        requests.post(f"{OIIOII_API}/points/active_user", json={"data": {}}, headers=H, timeout=15)
        r = requests.post(f"{OIIOII_API}/points/current_user_points", json={"data": {}}, headers=H, timeout=15)
        return r.json().get("data", {}).get("available_limited", "?")
    except:
        return "?"

def register_one(index):
    """注册单个账号，带重试和代理轮换"""
    global success_count, fail_count
    
    for attempt in range(3):  # 最多重试3次
        session = get_proxy_session()
        
        # Step 1: 创建临时邮箱
        email, pwd, svc = create_temp_email()
        if not email:
            if attempt < 2:
                time.sleep(random.uniform(2, 5))
                continue
            with lock:
                fail_count += 1
            log(f"[{index}/{TARGET}] FAIL - cannot create email (attempt {attempt+1})")
            return None
        
        # Step 2: Supabase注册
        status, data = signup_via_supabase(email, pwd, session)
        
        if status in (200, 201):
            # Step 3: 邮箱验证
            if svc == "mailtm" or svc == "mailtm_direct":
                poll_verify_mailtm(email, pwd, timeout=60)
            
            # Step 4: 登录
            token = login_oiioii(email, pwd, session)
        elif status == 422:
            # 被限流，换代理重试
            if attempt < 2:
                log(f"[{index}/{TARGET}] 422 rate limited, retry with new proxy...")
                time.sleep(random.uniform(5, 15))
                continue
            # 最后尝试直接oiioii注册
            token = login_oiioii(email, pwd, session)
        else:
            token = login_oiioii(email, pwd, session)
        
        if not token:
            # 再试一次不用代理
            token = login_oiioii(email, pwd)
        
        if not token:
            with lock:
                fail_count += 1
            log(f"[{index}/{TARGET}] FAIL - login failed (attempt {attempt+1})")
            return None
        
        # Step 5: workspace和积分
        ws_id = get_workspace(token)
        pts = claim_points(token)
        
        with lock:
            success_count += 1
        
        log(f"[{index}/{TARGET}] OK! pts={pts} ws={ws_id} email={svc} (success: {success_count}, fail: {fail_count})")
        
        return {
            "email": email,
            "password": pwd,
            "token": token,
            "workspace_id": ws_id,
            "points": pts,
            "registered_at": time.time()
        }
    
    with lock:
        fail_count += 1
    log(f"[{index}/{TARGET}] FAIL - all attempts exhausted (success: {success_count}, fail: {fail_count})")
    return None

def main():
    global proxy_list
    
    log(f"=== BATCH REGISTER {TARGET} ACCOUNTS ({WORKERS} workers) ===")
    
    # Step 1: 获取代理
    log("Fetching proxies...")
    proxy_list = fetch_free_proxies()
    if proxy_list:
        filter_working_proxies(max_test=80)
    
    if not proxy_list:
        log("WARNING: No working proxies found, registering without proxy rotation!")
    else:
        log(f"Using {len(proxy_list)} proxies for rotation")
    
    # Step 2: 加载已有账号
    existing = []
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as f:
            existing = json.load(f)
        log(f"Existing accounts: {len(existing)}")
    
    # Step 3: 并发注册
    new_accounts = []
    
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {}
        for i in range(TARGET):
            # 每批之间加延迟，避免瞬间发太多请求
            if i > 0 and i % WORKERS == 0:
                time.sleep(random.uniform(1, 3))
            future = executor.submit(register_one, i + 1)
            futures[future] = i + 1
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                new_accounts.append(result)
                # 增量保存
                with lock:
                    all_accounts = existing + new_accounts
                    with open(ACCOUNTS_FILE, "w") as f:
                        json.dump(all_accounts, f, indent=2, ensure_ascii=False)
    
    log(f"\n=== DONE ===")
    log(f"Success: {len(new_accounts)} | Failed: {fail_count}")
    log(f"Total accounts: {len(existing) + len(new_accounts)}")
    log(f"Saved to: {ACCOUNTS_FILE}")

if __name__ == "__main__":
    main()
