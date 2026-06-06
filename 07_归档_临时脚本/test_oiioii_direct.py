import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=15)

script = r'''
import requests, json

# Login to OiioiiPool to get a real account
r = requests.get("http://127.0.0.1:7861/api/pool/status", timeout=10)
data = r.json()
accts = data.get("accounts", [])
# Find an account with high points
accts.sort(key=lambda a: -a.get("points", 0))
acct = accts[0]
print(f"Using account: {acct['email']} points={acct['points']}")

# Get token from local OiioiiPool account
# We need the password from DB
import sqlite3
conn = sqlite3.connect("/home/ubuntu/oiioii/data/oiioii_pool.db")
row = conn.execute("SELECT email, password FROM accounts WHERE id=?", (acct["id"],)).fetchone()
conn.close()
email, password = row
print(f"Password: {password[:5]}...")

# Login to api.oiioii.ai
API = "https://api.oiioii.ai"
r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=10)
print(f"\nLogin: {r.status_code}")
if r.status_code != 200:
    print(f"Resp: {r.text[:200]}")
    exit()
token = r.json()["access_token"]
print(f"Token: {token[:20]}...")

# Test 1: Upload a small video reference
print("\n=== Test 1: Small video (0.5MB) ===")
data = b"x" * 512 * 1024
s = requests.Session()
s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
import base64, time
b64 = base64.b64encode(data).decode("ascii")
start = time.time()
r = s.post(f"{API}/res/upload_file", json={"fileBlob": b64, "fileType": "video/mp4"}, timeout=120)
elapsed = time.time() - start
print(f"Status: {r.status_code}, Time: {elapsed:.1f}s")
print(f"Resp: {r.text[:200]}")

# Test 2: Try 5MB
print("\n=== Test 2: 5MB video ===")
data = b"x" * 5 * 1024 * 1024
b64 = base64.b64encode(data).decode("ascii")
start = time.time()
r = s.post(f"{API}/res/upload_file", json={"fileBlob": b64, "fileType": "video/mp4"}, timeout=180)
elapsed = time.time() - start
print(f"Status: {r.status_code}, Time: {elapsed:.1f}s")
print(f"Resp: {r.text[:200]}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_oiioii_direct.py', 'w') as f:
    f.write(script)
sftp.close()

print("Testing Oiioii external API directly...")
stdin, stdout, stderr = client.exec_command('python3 /tmp/test_oiioii_direct.py', timeout=300)
print(stdout.read().decode()[:2000])
err = stderr.read().decode()[:500]
if err: print("ERR:", err)

client.close()