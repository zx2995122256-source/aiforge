import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=15)

script = r'''
import sys, requests, base64, time, sqlite3
sys.path.insert(0, "/home/ubuntu/oiioii")
from config import SUPABASE_URL, SUPABASE_ANON_KEY, API_BASE

conn = sqlite3.connect("/home/ubuntu/oiioii/data/oiioii_pool.db")
row = conn.execute("SELECT email, password FROM accounts WHERE status='active' LIMIT 1").fetchone()
conn.close()
email, password = row[0], row[1]

s = requests.Session()
r = s.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
    json={"email": email, "password": password, "gotrue_meta_security": {}},
    headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"}, timeout=15)
token = r.json()["access_token"]
headers_auth = {"Authorization": f"Bearer {token}"}

r = s.post(f"{API_BASE}/workspace/workspace_list", json={"data": {"limit": 10}}, headers={**headers_auth, "Content-Type": "application/json"}, timeout=15)
ws = r.json().get("data", {}).get("workspaces", [])
if ws:
    headers_auth["x-workspace-id"] = ws[0].get("workspaceId", "")

# Test: Use multipart upload (no base64, no Content-Type: application/json)
print("=== Test multipart upload 13MB ===")
data = b"x" * 13 * 1024 * 1024
start = time.time()
# Don't set Content-Type for multipart
try:
    r = requests.post(f"{API_BASE}/res/upload_file", 
        files={"file": ("test.mp4", data, "video/mp4")},
        headers=headers_auth,
        timeout=180)
    elapsed = time.time() - start
    print(f"Status: {r.status_code}, {elapsed:.1f}s")
    if r.status_code == 200:
        rj = r.json()
        print(f"Code: {rj.get('code','?')}")
        if rj.get("code") == "SUCCESS":
            print(f"✅ Multipart 13MB works! URI: {rj.get('data',{}).get('uri','?')[:60]}")
        else:
            print(f"Resp: {r.text[:200]}")
    else:
        print(f"Resp: {r.text[:200]}")
except Exception as e:
    elapsed = time.time() - start
    print(f"Error after {elapsed:.1f}s: {e}")

# Also test 5MB multipart
print("\n=== Test multipart 5MB ===")
data = b"x" * 5 * 1024 * 1024
start = time.time()
try:
    r = requests.post(f"{API_BASE}/res/upload_file",
        files={"file": ("test.mp4", data, "video/mp4")},
        headers=headers_auth,
        timeout=120)
    elapsed = time.time() - start
    print(f"Status: {r.status_code}, {elapsed:.1f}s")
    if r.status_code == 200:
        print(f"✅ 5MB via multipart works!")
        print(f"Resp: {r.text[:200]}")
    else:
        print(f"Resp: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_multipart_direct.py', 'w') as f:
    f.write(script)
sftp.close()

print("Testing multipart upload (like the website)...")
stdin, stdout, stderr = client.exec_command('python3 /tmp/test_multipart_direct.py', timeout=300)
print(stdout.read().decode()[:2000])
err = stderr.read().decode()[:500]
if err: print("ERR:", err)

client.close()