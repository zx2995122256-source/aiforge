#!/usr/bin/env python3
"""
Batch register oiioii accounts via API (Supabase + mail.tm)
Registers accounts and adds them to the local oiioii account pool.
Uses delays between registrations to avoid rate limiting.
"""
import requests
import json
import time
import random
import string
import re
import os
import sys

MAIL_TM = "https://api.mail.tm"
SUPABASE = "https://spb.oiioii.ai"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVndnV6ZXN0eXlwYm1jZnVycmJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEyMTU4NTEsImV4cCI6MjA3Njc5MTg1MX0.Z1qdxtK0PLF5NV1yXrI9s_W2Hurdxo143DBzuUuajh0"
OIIOII_API = "https://api.oiioii.ai"

# Target number of accounts
TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 100

# Output file for registered accounts
ACCOUNTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "accounts.json")

log = lambda msg: print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def create_temp_email():
    """Create a temporary email on mail.tm"""
    try:
        r = requests.get(f"{MAIL_TM}/domains", timeout=10)
        domains = r.json().get("hydra:member", [])
        domain = domains[0]["domain"] if domains else "mail.tm"
        rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
        email = f"oiio_{rand}@{domain}"
        password = f"Oi{rand}!Pass1"
        r = requests.post(f"{MAIL_TM}/accounts", json={"address": email, "password": password}, timeout=15)
        if r.status_code == 201:
            return email, password
        else:
            log(f"  Mail.tm create failed: {r.status_code} {r.text[:100]}")
    except Exception as e:
        log(f"  Mail.tm error: {e}")
    return None, None

def get_mail_token(email, password):
    try:
        r = requests.post(f"{MAIL_TM}/token", json={"address": email, "password": password}, timeout=10)
        if r.status_code == 200:
            return r.json()["token"]
    except:
        pass
    return None

def poll_verify_link(mail_token, email, timeout=120):
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
                    detail = r2.json()
                    html_content = ""
                    if detail.get("html"):
                        html_content = detail["html"][0] if isinstance(detail["html"], list) else detail["html"]
                    links = re.findall(r'https?://[^\s"\'<>]+confirm[^\s"\'<>]*', html_content)
                    if not links:
                        links = re.findall(r'https?://[^\s"\'<>]*supabase[^\s"\'<>]*token[^\s"\'<>]*', html_content)
                    if not links:
                        links = re.findall(r'https?://[^\s"\'<>]*(?:verify|confirm|click)[^\s"\'<>]*', html_content, re.IGNORECASE)
                    if not links:
                        all_links = re.findall(r'https?://[^\s"\'<>]+', html_content)
                        for link in all_links:
                            if "oiioii" in link or "supabase" in link:
                                links.append(link)
                    if links:
                        verify_url = links[0].replace("&amp;", "&")
                        r3 = requests.get(verify_url, timeout=15, allow_redirects=True)
                        log(f"  Verify status: {r3.status_code}")
                        return True
        except:
            pass
        time.sleep(5)
    return False

def signup_via_supabase(email, password):
    r = requests.post(f"{SUPABASE}/auth/v1/signup", json={
        "email": email,
        "password": password,
        "data": {"language": "zh", "nickname": email.split("@")[0]}
    }, headers={"apikey": ANON_KEY, "Content-Type": "application/json"}, timeout=15)
    return r.status_code, r.json()

def login_oiioii(email, password):
    """Try oiioii signin (which also signs up if not found)"""
    r = requests.post(f"{OIIOII_API}/auth/signin_with_password", json={
        "email": email, "password": password, "tencentCaptcha": None,
        "inviteCode": "", "language": "zh", "nickname": email.split("@")[0],
        "signupOnNotFound": True
    }, headers={"Content-Type": "application/json"}, timeout=15)
    if r.status_code == 200:
        token = r.json().get("data", {}).get("access_token", r.json().get("access_token", ""))
        return token
    return None

def get_workspace(token):
    H = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    # Try to create workspace
    r = requests.post(f"{OIIOII_API}/workspace/create_workspace", json={"data": {"name": "default"}}, headers=H, timeout=15)
    ws_id = r.json().get("data", {}).get("workspaceId")
    if not ws_id:
        r = requests.post(f"{OIIOII_API}/workspace/workspace_list", json={"data": {"limit": 10}}, headers=H, timeout=15)
        try:
            ws_id = r.json()["data"]["workspaces"][0]["workspaceId"]
        except:
            ws_id = None
    return ws_id

def claim_points(token):
    H = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    requests.post(f"{OIIOII_API}/points/active_user", json={"data": {}}, headers=H, timeout=15)
    r = requests.post(f"{OIIOII_API}/points/current_user_points", json={"data": {}}, headers=H, timeout=15)
    try:
        pts = r.json().get("data", {}).get("available_limited", "?")
        return pts
    except:
        return "?"

def register_one(index):
    """Register a single account and return account info dict"""
    log(f"[{index}/{TARGET}] Starting registration...")
    
    # Step 1: Create temp email
    email, pwd = create_temp_email()
    if not email:
        return None
    
    # Step 2: Signup via Supabase
    status, data = signup_via_supabase(email, pwd)
    if status not in (200, 201):
        log(f"  Supabase signup failed: {status}")
        # Try oiioii direct signin
        token = login_oiioii(email, pwd)
        if not token:
            log(f"  All signup methods failed")
            return None
    else:
        # Step 3: Verify email
        mail_token = get_mail_token(email, pwd)
        if mail_token:
            verified = poll_verify_link(mail_token, email, timeout=90)
            if not verified:
                log(f"  Email verification timeout, trying login anyway...")
        
        # Step 4: Login
        token = login_oiioii(email, pwd)
        if not token:
            log(f"  Login failed")
            return None
    
    # Step 5: Get workspace and claim points
    ws_id = get_workspace(token)
    pts = claim_points(token)
    
    log(f"  OK! pts={pts} ws={ws_id}")
    
    return {
        "email": email,
        "password": pwd,
        "token": token,
        "workspace_id": ws_id,
        "points": pts,
        "registered_at": time.time()
    }

def main():
    log(f"=== BATCH REGISTER {TARGET} OIIOII ACCOUNTS ===")
    
    # Load existing accounts
    existing = []
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as f:
            existing = json.load(f)
        log(f"Existing accounts: {len(existing)}")
    
    new_accounts = []
    failed = 0
    
    for i in range(TARGET):
        result = register_one(i + 1)
        if result:
            new_accounts.append(result)
            # Save incrementally
            all_accounts = existing + new_accounts
            with open(ACCOUNTS_FILE, "w") as f:
                json.dump(all_accounts, f, indent=2)
            log(f"  Saved. Total new: {len(new_accounts)}")
        else:
            failed += 1
            log(f"  Failed. Total failed: {failed}")
        
        # Random delay between registrations (3-8 seconds)
        delay = random.uniform(3, 8)
        time.sleep(delay)
    
    log(f"\n=== DONE ===")
    log(f"Success: {len(new_accounts)} | Failed: {failed}")
    log(f"Total accounts in pool: {len(existing) + len(new_accounts)}")
    log(f"Saved to: {ACCOUNTS_FILE}")

if __name__ == "__main__":
    main()
