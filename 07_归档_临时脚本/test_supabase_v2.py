import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=15)

script = r'''
import sys, requests, json, base64, time, sqlite3

sys.path.insert(0, "/home/ubuntu/oiioii")
from config import SUPABASE_URL, SUPABASE_ANON_KEY, API_BASE

# Get a real active account
conn = sqlite3.connect("/home/ubuntu/oiioii/data/oiioii_pool.db")
row = conn.execute("SELECT id, email, password FROM accounts WHERE status='active' LIMIT 1").fetchone()
conn.close()
email, password = row[1], row[2]
print(f"Account: {email[:15]}...")
print(f"Supabase: {SUPABASE_URL}")
print(f"API_BASE: {API_BASE}")

# Login via Supabase
s = requests.Session()
r = s.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
    json={"email": email, "password": password, "gotrue_meta_security": {}},
    headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
    timeout=15)
print(f"\nLogin: {r.status_code}")
if r.status_code != 200:
    print(r.text[:200])
    sys.exit(1)
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
print(f"Token: {token[:20]}...")

# Activate
r = s.post(f"{API_BASE}/points/active_user", json={"data": {}}, headers=headers, timeout=15)
print(f"Activate: {r.status_code}")

# Get workspace
r = s.post(f"{API_BASE}/workspace/workspace_list", json={"data": {"limit": 10}}, headers=headers, timeout=15)
ws = r.json().get("data", {}).get("workspaces", [])
if ws:
    wid = ws[0].get("workspaceId", "")
    print(f"Workspace: {wid}")
    headers["x-workspace-id"] = wid

# Test upload - 100KB first
print(f"\n=== Upload 100KB ===")
data = b"x" * 100 * 1024
b64 = base64.b64encode(data).decode("ascii")
start = time.time()
try:
    r = s.post(f"{API_BASE}/res/upload_file", json={"fileBlob": b64, "fileType": "video/mp4"}, headers=headers, timeout=120)
    print(f"Status: {r.status_code}, {time.time()-start:.1f}s")
    rj = r.json()
    print(f"Code: {rj.get('code','?')}")
    if rj.get("code") == "SUCCESS":
        uri = rj.get("data", {}).get("uri", "")
        print(f"hogi URI: {uri[:60]}")
    else:
        print(f"Resp: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e} ({time.time()-start:.1f}s)")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_supabase_v2.py', 'w') as f:
    f.write(script)
sftp.close()

print("Testing via Supabase...")
stdin, stdout, stderr = client.exec_command('python3 /tmp/test_supabase_v2.py', timeout=300)
print(stdout.read().decode()[:2000])
err = stderr.read().decode()[:500]
if err: print("ERR:", err)

client.close()