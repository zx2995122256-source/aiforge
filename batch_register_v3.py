#!/usr/bin/env python3
"""
Batch register oiioii accounts - direct oiioii API, no Supabase.
Uses signin_with_password with signupOnNotFound=True.
Slower but more reliable - avoids Supabase rate limits.
"""
import requests
import json
import time
import random
import string
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

OIIOII_API = "https://api.oiioii.ai"
MAIL_TM = "https://api.mail.tm"

TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 200
WORKERS = int(sys.argv[2]) if len(sys.argv) > 2 else 5
ACCOUNTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "accounts.json")

lock = threading.Lock()
success_count = 0
fail_count = 0

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}", flush=True)

def create_temp_email():
    """创建mail.tm临时邮箱"""
    try:
        r = requests.get(f"{MAIL_TM}/domains", timeout=10)
        domains = r.json().get("hydra:member", [])
        domain = domains[0]["domain"] if domains else "mail.tm"
        rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
        email = f"oiio_{rand}@{domain}"
        pwd = f"Oi{rand}!Pass1"
        r = requests.post(f"{MAIL_TM}/accounts", json={"address": email, "password": pwd}, timeout=15)
        if r.status_code == 201:
            return email, pwd
        else:
            log(f"  Mail.tm failed: {r.status_code}")
    except Exception as e:
        log(f"  Mail.tm error: {e}")
    return None, None

def register_oiioii(email, password):
    """直接通过oiioii API注册+登录"""
    try:
        r = requests.post(f"{OIIOII_API}/auth/signin_with_password", json={
            "email": email,
            "password": password,
            "tencentCaptcha": None,
            "inviteCode": "",
            "language": "zh",
            "nickname": email.split("@")[0],
            "signupOnNotFound": True
        }, headers={"Content-Type": "application/json"}, timeout=20)
        
        if r.status_code == 200:
            data = r.json()
            token = data.get("data", {}).get("access_token", data.get("access_token", ""))
            if token:
                return token
        
        log(f"  Oiioii signin failed: {r.status_code} {r.text[:150]}")
    except Exception as e:
        log(f"  Oiioii error: {e}")
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
    """注册单个账号"""
    global success_count, fail_count
    
    # 随机延迟，避免同时发请求
    time.sleep(random.uniform(0, 3))
    
    for attempt in range(3):
        # Step 1: 创建邮箱
        email, pwd = create_temp_email()
        if not email:
            if attempt < 2:
                time.sleep(random.uniform(5, 15))
                continue
            with lock:
                fail_count += 1
            log(f"[{index}/{TARGET}] FAIL - email creation failed")
            return None
        
        # Step 2: 直接oiioii注册
        token = register_oiioii(email, pwd)
        if not token:
            if attempt < 2:
                time.sleep(random.uniform(10, 20))
                continue
            with lock:
                fail_count += 1
            log(f"[{index}/{TARGET}] FAIL - registration failed (email={email})")
            return None
        
        # Step 3: workspace和积分
        ws_id = get_workspace(token)
        pts = claim_points(token)
        
        with lock:
            success_count += 1
        
        log(f"[{index}/{TARGET}] OK! pts={pts} (success: {success_count}, fail: {fail_count})")
        
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
    log(f"[{index}/{TARGET}] FAIL - all attempts exhausted")
    return None

def main():
    log(f"=== BATCH REGISTER {TARGET} ACCOUNTS ({WORKERS} workers) ===")
    log(f"Strategy: direct oiioii API (no Supabase), {WORKERS} concurrent")
    
    # 加载已有账号
    existing = []
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as f:
            existing = json.load(f)
        log(f"Existing accounts: {len(existing)}")
    
    new_accounts = []
    
    # 分批并发，每批WORKERS个，批间延迟
    batch_size = WORKERS
    
    for batch_start in range(0, TARGET, batch_size):
        batch_end = min(batch_start + batch_size, TARGET)
        batch_num = batch_start // batch_size + 1
        total_batches = (TARGET + batch_size - 1) // batch_size
        
        log(f"--- Batch {batch_num}/{total_batches} (accounts {batch_start+1}-{batch_end}) ---")
        
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            futures = {}
            for i in range(batch_start, batch_end):
                future = executor.submit(register_one, i + 1)
                futures[future] = i + 1
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    new_accounts.append(result)
                    with lock:
                        all_accounts = existing + new_accounts
                        with open(ACCOUNTS_FILE, "w") as f:
                            json.dump(all_accounts, f, indent=2, ensure_ascii=False)
        
        # 批间延迟
        if batch_end < TARGET:
            delay = random.uniform(8, 15)
            log(f"Batch done. Waiting {delay:.1f}s before next batch...")
            time.sleep(delay)
    
    log(f"\n=== DONE ===")
    log(f"Success: {len(new_accounts)} | Failed: {fail_count}")
    log(f"Total accounts: {len(existing) + len(new_accounts)}")
    log(f"Saved to: {ACCOUNTS_FILE}")

if __name__ == "__main__":
    main()
