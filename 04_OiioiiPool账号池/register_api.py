import requests, time, random, string, json, re
from datetime import datetime

MAIL_TM_API = "https://api.mail.tm"
SUPABASE_URL = "https://spb.oiioii.ai"
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVndnV6ZXN0eXlwYm1jZnVycmJkIiwicm9sZSI6ImFub24iLC"
    "JpYXQiOjE3NjEyMTU4NTEsImV4cCI6MjA3Njc5MTg1MX0."
    "Z1qdxtK0PLF5NV1yXrI9s_W2Hurdxo143DBzuUuajh0"
)
API_BASE = "https://api.oiioii.ai"

def create_temp_email():
    r = requests.get(f"{MAIL_TM_API}/domains", timeout=10)
    domains = r.json().get("hydra:member", [])
    if not domains:
        return None, None
    domain = domains[0]["domain"]
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
    email = f"oiio_{rand}@{domain}"
    password = f"Oi{rand}!Pass1"
    r = requests.post(f"{MAIL_TM_API}/accounts",
        json={"address": email, "password": password}, timeout=15)
    if r.status_code == 201:
        return email, password
    return None, None

def get_mail_token(email, password):
    r = requests.post(f"{MAIL_TM_API}/token",
        json={"address": email, "password": password}, timeout=10)
    if r.status_code == 200:
        return r.json()["token"]
    return None

def poll_verify_link(mail_token, timeout=120):
    headers = {"Authorization": f"Bearer {mail_token}"}
    start = time.time()
    while time.time() - start < timeout:
        r = requests.get(f"{MAIL_TM_API}/messages", headers=headers, timeout=10)
        if r.status_code == 200:
            msgs = r.json().get("hydra:member", [])
            for msg in msgs:
                text = requests.get(msg["downloadUrl"], headers=headers, timeout=10).text
                urls = re.findall(r'https?://[^\s\'\"<>]+verify[^\s\'\"<>]+', text)
                if urls:
                    return urls[0]
        time.sleep(3)
    return None

print("=== 注册 Oiioii 账号 (无验证码) ===")

# 1. Create temp email
print("[1/5] 创建临时邮箱...")
email, password = create_temp_email()
if not email:
    print("  失败！")
    exit(1)
print(f"  邮箱: {email}")
print(f"  密码: {password}")

# 2. Get mail token
mail_token = get_mail_token(email, password)
print(f"[2/5] 邮件token: {'OK' if mail_token else 'FAILED'}")

# 3. Supabase signup via API (no captcha!)
print("[3/5] Supabase API 注册...")
headers = {"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"}
r = requests.post(
    f"{SUPABASE_URL}/auth/v1/signup",
    json={"email": email, "password": password},
    headers=headers,
    timeout=15
)
print(f"  Status: {r.status_code}")
if r.status_code not in (200, 201, 204):
    print(f"  Response: {r.text[:200]}")
    # Maybe already signed up via Playwright
    print("  试试直接登录...")

# 4. Wait for verification email
print("[4/5] 等待验证邮件...")
if mail_token:
    verify_link = poll_verify_link(mail_token, timeout=90)
    if verify_link:
        print(f"  验证链接: {verify_link[:80]}...")
        requests.get(verify_link, timeout=15, allow_redirects=True)
        print("  已点击验证链接")
    else:
        print("  未收到验证邮件")

# 5. Login to get token
print("[5/5] 登录获取token...")
time.sleep(2)
r = requests.post(
    f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
    json={"email": email, "password": password, "gotrue_meta_security": {}},
    headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
    timeout=15
)
if r.status_code == 200:
    token = r.json()["access_token"]
    print(f"  Token: {token[:50]}...")

    # Activate user
    headers_auth = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r2 = requests.post(f"{API_BASE}/points/active_user",
        json={"data": {}}, headers=headers_auth, timeout=15)
    print(f"  激活用户: {r2.status_code}")

    # Get points
    r3 = requests.post(f"{API_BASE}/points/current_user_points",
        json={"data": {}}, headers=headers_auth, timeout=15)
    points = r3.json().get("data", {}).get("available_limited", 0)
    print(f"  积分: {points}")

    print(f"\n✅ 注册成功!")
    print(f"  Email: {email}")
    print(f"  Password: {password}")
    print(f"  Points: {points}")
else:
    print(f"  登录失败: {r.status_code} {r.text[:200]}")
