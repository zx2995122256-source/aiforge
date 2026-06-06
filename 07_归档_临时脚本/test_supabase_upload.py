import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=15)

script = r'''
import sys, os, requests, json, base64, time, sqlite3

sys.path.insert(0, "/home/ubuntu/oiioii")
sys.path.insert(0, "/home/ubuntu/oiioii/core")
sys.path.insert(0, "/home/ubuntu/oiioii/core/core")

# Get Supabase config
from config import SUPABASE_URL, SUPABASE_ANON_KEY, API_BASE

# Get a real account
conn = sqlite3.connect("/home/ubuntu/oiioii/data/oiioii_pool.db")
row = conn.execute("SELECT id, email, password FROM accounts WHERE status='active' ORDER BY points DESC LIMIT 1").fetchone()
conn.close()
email, password = row[1], row[2]
print(f"Account: {email[:15]}... pw={password[:5]}...")
print(f"Supabase: {SUPABASE_URL}")
print(f"API_BASE: {API_BASE}")

# Login via Supabase (same as client.py)
s = requests.Session()
r = s.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
    json={"email": email, "password": password, "gotrue_meta_security": {}},
    headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
    timeout=15)
print(f"\nLogin: {r.status_code}")
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
print(f"Token: {token[:20]}...")

# Activate user
r = s.post(f"{API_BASE}/points/active_user", json={"data": {}}, headers=headers, timeout=15)
print(f"Activate: {r.status_code}")

# Get workspace
r = s.post(f"{API_BASE}/workspace/workspace_list", json={"data": {"limit": 10}}, headers=headers, timeout=15)
ws = r.json().get("data", {}).get("workspaces", [])
if ws:
    wid = ws[0].get("workspaceId", "")
    print(f"Workspace: {wid}")
    headers["x-workspace-id"] = wid

# Test 1: Tiny upload (100KB)
print(f"\n=== Test 1: 100KB video ===")
data = b"x" * 100 * 1024
b64 = base64.b64encode(data).decode("ascii")
body = {"fileBlob": b64, "fileType": "video/mp4"}
start = time.time()
try:
    r = s.post(f"{API_BASE}/res/upload_file", json=body, headers=headers, timeout=120)
    print(f"Status: {r.status_code}, {time.time()-start:.1f}s")
    print(f"Resp: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: 1MB
print(f"\n=== Test 2: 1MB video ===")
data = b"x" * 1024 * 1024
b64 = base64.b64encode(data).decode("ascii")
body = {"fileBlob": b64, "fileType": "video/mp4"}
start = time.time()
try:
    r = s.post(f"{API_BASE}/res/upload_file", json=body, headers=headers, timeout=180)
    print(f"Status: {r.status_code}, {time.time()-start:.1f}s")
    print(f"Resp: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_supabase_upload.py', 'w') as f:
    f.write(script)
sftp.close()

print("Testing via Supabase auth...")
stdin, stdout, stderr = client.exec_command('python3 /tmp/test_supabase_upload.py', timeout=300)
print(stdout.read().decode()[:2000])
err = stderr.read().decode()[:500]
if err: print("ERR:", err)

client.close()