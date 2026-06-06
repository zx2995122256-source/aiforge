import base64
import importlib
import sys
import time
import requests

sys.path.insert(0, "/home/ubuntu/oiioii")
sys.path.insert(0, "/home/ubuntu/oiioii/core")

spec = importlib.util.spec_from_file_location("config", "/home/ubuntu/oiioii/config.py")
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)
API_BASE = config.API_BASE
print(f"API_BASE = {API_BASE}")

from core.db import AccountDB

accounts = AccountDB.get_all(limit=5)
acct = None
for a in accounts:
    if a.get("status") == "active":
        acct = a
        break

if not acct:
    print("No active account found")
    sys.exit(1)

print(f"Account: {acct['email']}")

s = requests.Session()
s.headers.update({"Content-Type": "application/json"})

r = s.post(f"{API_BASE}/auth/login", json={"email": acct["email"], "password": acct["password"]}, timeout=10)
print(f"Login: {r.status_code}")
token = r.json().get("access_token", "")
print(f"Token: {token[:20]}...")

data = b"x" * 13 * 1024 * 1024

# Test 1: base64 JSON
b64 = base64.b64encode(data).decode("ascii")
print(f"\nTest 1: base64 JSON (body ~{len(b64)/1024/1024:.1f}MB)")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
start = time.time()
try:
    r = s.post(f"{API_BASE}/res/upload_file", json={"fileBlob": b64, "fileType": "video/mp4"}, headers=headers, timeout=180)
    print(f"Status: {r.status_code}, Time: {time.time()-start:.1f}s")
    print(f"Response: {r.text[:200]}")
except Exception as e:
    print(f"Error after {time.time()-start:.1f}s: {e}")

# Test 2: Multipart
print(f"\nTest 2: Multipart upload")
h2 = {"Authorization": f"Bearer {token}"}
start = time.time()
try:
    r2 = s.post(f"{API_BASE}/res/upload_file", files={"file": ("test.mp4", data, "video/mp4")}, headers=h2, timeout=180)
    print(f"Status: {r2.status_code}, Time: {time.time()-start:.1f}s")
    print(f"Response: {r2.text[:200]}")
except Exception as e:
    print(f"Error after {time.time()-start:.1f}s: {e}")