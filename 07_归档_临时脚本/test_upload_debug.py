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

# Fresh session for each test
def get_headers():
    s = requests.Session()
    r = s.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        json={"email": email, "password": password, "gotrue_meta_security": {}},
        headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"}, timeout=15)
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    r2 = s.post(f"{API_BASE}/workspace/workspace_list", json={"data": {"limit": 10}}, headers={**h, "Content-Type": "application/json"}, timeout=15)
    ws = r2.json().get("data", {}).get("workspaces", [])
    if ws:
        h["x-workspace-id"] = ws[0].get("workspaceId", "")
    return h

# Test multipart with tiny file first
print("=== Multipart tiny 10KB ===")
data = b"x" * 10 * 1024
h = get_headers()
r = requests.post(f"{API_BASE}/res/upload_file", files={"file": ("t.mp4", data, "video/mp4")}, headers=h, timeout=60)
print(f"  Status: {r.status_code}, Resp: {r.text[:100]}")

# Test multipart 100KB
print("\n=== Multipart 100KB ===")
data = b"x" * 100 * 1024
h = get_headers()
r = requests.post(f"{API_BASE}/res/upload_file", files={"file": ("t.mp4", data, "video/mp4")}, headers=h, timeout=60)
print(f"  Status: {r.status_code}, Resp: {r.text[:100]}")

# Test base64 100KB (controls match)
print("\n=== Base64 100KB ===")
data = b"x" * 100 * 1024
h2 = get_headers()
h2["Content-Type"] = "application/json"
b64 = base64.b64encode(data).decode("ascii")
r = requests.post(f"{API_BASE}/res/upload_file", json={"fileBlob": b64, "fileType": "video/mp4"}, headers=h2, timeout=60)
print(f"  Status: {r.status_code}, Resp: {r.text[:100]}")

# Test with different field name - maybe it's not "file"
print("\n=== Try different field names ===")
data = b"x" * 50 * 1024
h = get_headers()
for fname in ["fileBlob", "file", "upload", "video"]:
    try:
        r = requests.post(f"{API_BASE}/res/upload_file", files={fname: ("t.mp4", data, "video/mp4")}, headers=h, timeout=30)
        print(f"  field='{fname}' -> {r.status_code}")
    except Exception as e:
        print(f"  field='{fname}' -> Error: {str(e)[:40]}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_upload_debug.py', 'w') as f:
    f.write(script)
sftp.close()

print("Debugging upload API...")
stdin, stdout, stderr = client.exec_command('python3 /tmp/test_upload_debug.py', timeout=120)
print(stdout.read().decode()[:1500])
err = stderr.read().decode()[:500]
if err: print("ERR:", err)

client.close()