import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

script = r'''
import requests, json, time

# Get API_BASE from config
import importlib
spec = importlib.util.spec_from_file_location("config", "/home/ubuntu/oiioii/config.py")
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)
API_BASE = config.API_BASE
print(f"API_BASE = {API_BASE}")

# Get a real account
import sys
sys.path.insert(0, "/home/ubuntu/oiioii/core")
sys.path.insert(0, "/home/ubuntu/oiioii")
from db import AccountDB
accounts = AccountDB.get_all(limit=5)
acct = accounts[0]
print(f"Account: {acct['email']} status={acct['status']}")

# Login
s = requests.Session()
s.headers.update({"Content-Type": "application/json"})
r = s.post(f"{API_BASE}/auth/login", json={"email": acct["email"], "password": acct["password"]}, timeout=10)
print(f"Login: {r.status_code}")
token = r.json().get("access_token", "")
print(f"Token: {token[:20]}...")

headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Test 1: Standard base64 JSON upload with 13MB
data = b"x" * 13 * 1024 * 1024
b64 = base64.b64encode(data).decode("ascii")
print(f"\nTest 1: JSON+base64, body size ~{len(b64)/1024/1024:.1f}MB")
start = time.time()
try:
    r = s.post(f"{API_BASE}/res/upload_file", json={"fileBlob": b64, "fileType": "video/mp4"}, headers=headers, timeout=120)
    elapsed = time.time() - start
    print(f"Status: {r.status_code}, Time: {elapsed:.1f}s")
    print(f"Response: {r.text[:200]}")
except Exception as e:
    elapsed = time.time() - start
    print(f"Error after {elapsed:.1f}s: {e}")

# Test 2: Remove Content-Type header and use multipart
print(f"\nTest 2: Multipart upload")
s2 = requests.Session()
r2 = s2.post(f"{API_BASE}/auth/login", json={"email": acct["email"], "password": acct["password"]}, timeout=10)
token2 = r2.json().get("access_token", "")
headers2 = {"Authorization": f"Bearer {token2}"}
start = time.time()
try:
    r2 = s2.post(f"{API_BASE}/res/upload_file", 
        files={"file": ("test.mp4", data, "video/mp4")},
        headers=headers2,
        timeout=120)
    elapsed = time.time() - start
    print(f"Status: {r2.status_code}, Time: {elapsed:.1f}s")
    print(f"Response: {r2.text[:200]}")
except Exception as e:
    elapsed = time.time() - start
    print(f"Error after {elapsed:.1f}s: {e}")
'''

# Write using heredoc-like approach
with client.open_sftp() as sftp:
    with sftp.file('/tmp/test_external_upload.py', 'w') as f:
        f.write('import base64, importlib, sys, time, requests\n')
        f.write('spec = importlib.util.spec_from_file_location("config", "/home/ubuntu/oiioii/config.py")\n')
        f.write('config = importlib.util.module_from_spec(spec)\n')
        f.write('spec.loader.exec_module(config)\n')
        f.write('API_BASE = config.API_BASE\n')
        f.write('print(f"API_BASE = {API_BASE}")\n')
        f.write('sys.path.insert(0, "/home/ubuntu/oiioii")\n')
        f.write('sys.path.insert(0, "/home/ubuntu/oiioii/core")\n')
        f.write('from core.db import AccountDB\n')
        f.write('accounts = AccountDB.get_all(limit=5)\n')
        f.write('acct = [a for a in accounts if a.get("status") == "active"][0]\n')
        f.write('print(f"Account: {acct[\\"email\\"]}")\n')
        f.write('s = requests.Session()\n')
        f.write('s.headers.update({"Content-Type": "application/json"})\n')
        f.write('r = s.post(f"{API_BASE}/auth/login", json={"email": acct["email"], "password": acct["password"]}, timeout=10)\n')
        f.write('print(f"Login: {r.status_code}")\n')
        f.write('token = r.json().get("access_token", "")\n')
        f.write('print(f"Token: {token[:20]}...")\n')
        f.write('headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}\n')
        f.write('data = b"x" * 13 * 1024 * 1024\n')
        f.write('b64 = base64.b64encode(data).decode("ascii")\n')
        f.write('print(f"\\nTest 1: base64 JSON, body ~{len(b64)/1024/1024:.1f}MB")\n')
        f.write('start = time.time()\n')
        f.write('r = s.post(f"{API_BASE}/res/upload_file", json={"fileBlob": b64, "fileType": "video/mp4"}, headers=headers, timeout=120)\n')
        f.write('print(f"Status: {r.status_code}, {time.time()-start:.1f}s")\n')
        f.write('print(f"Response: {r.text[:200]}")\n')
        f.write('print("\\nTest 2: Multipart")\n')
        f.write('h2 = {"Authorization": f"Bearer {token}"}\n')
        f.write('start = time.time()\n')
        f.write('r2 = s.post(f"{API_BASE}/res/upload_file", files={"file": ("test.mp4", data, "video/mp4")}, headers=h2, timeout=120)\n')
        f.write('print(f"Status: {r2.status_code}, {time.time()-start:.1f}s")\n')
        f.write('print(f"Response: {r2.text[:200]}")\n')

stdin, stdout, stderr = client.exec_command('python3 /tmp/test_external_upload.py', timeout=300)
print(stdout.read().decode()[:2000])
err = stderr.read().decode()[:300]
if err: print("ERR:", err)

client.close()