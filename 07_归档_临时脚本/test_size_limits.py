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
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

r = s.post(f"{API_BASE}/workspace/workspace_list", json={"data": {"limit": 10}}, headers=headers, timeout=15)
ws = r.json().get("data", {}).get("workspaces", [])
if ws:
    headers["x-workspace-id"] = ws[0].get("workspaceId", "")

# Test increasing sizes
for size_mb in [0.5, 1, 2, 3, 5, 8, 10, 13]:
    size = int(size_mb * 1024 * 1024)
    data = b"x" * size
    b64_len = len(base64.b64encode(data).decode("ascii"))
    start = time.time()
    try:
        r = s.post(f"{API_BASE}/res/upload_file", 
            json={"fileBlob": base64.b64encode(data).decode("ascii"), "fileType": "video/mp4"},
            headers=headers, timeout=120)
        elapsed = time.time() - start
        ok = r.json().get("code") == "SUCCESS"
        status = "✅" if ok else "❌"
        print(f"{status} {size_mb:4.1f}MB ({b64_len/1024/1024:.0f}MB base64) -> {r.status_code} {elapsed:5.1f}s {'SUCCESS' if ok else r.text[:50]}")
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ {size_mb:4.1f}MB -> ERROR after {elapsed:.1f}s: {str(e)[:60]}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_size_limits.py', 'w') as f:
    f.write(script)
sftp.close()

print("Testing upload size limits...")
stdin, stdout, stderr = client.exec_command('python3 /tmp/test_size_limits.py', timeout=600)
print(stdout.read().decode()[:1500])
err = stderr.read().decode()[:300]
if err: print("ERR:", err)

client.close()