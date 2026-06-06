import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

script = r'''
import requests, time

BASE = "http://127.0.0.1:7862"

# Login
r = requests.post(BASE + "/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# Test with a larger file (10MB simulated)
print("=== Test with 10MB file ===")
data = b"x" * 10 * 1024 * 1024
start = time.time()
r = requests.post(BASE + "/api/gen/upload_video_ref",
    headers=headers,
    files={"file": ("large_test.mp4", data, "video/mp4")},
    timeout=120)
elapsed = time.time() - start
print(f"Status: {r.status_code}, Time: {elapsed:.1f}s")
print(f"Response: {r.text[:200]}")

# Test with 50MB
print("\n=== Test with 50MB file ===")
data = b"x" * 50 * 1024 * 1024
start = time.time()
r = requests.post(BASE + "/api/gen/upload_video_ref",
    headers=headers,
    files={"file": ("large_test_50mb.mp4", data, "video/mp4")},
    timeout=180)
elapsed = time.time() - start
print(f"Status: {r.status_code}, Time: {elapsed:.1f}s")
print(f"Response: {r.text[:200]}")

# Check disk
import os
s = os.statvfs("/home/ubuntu")
free_gb = s.f_bavail * s.f_frsize / 1024 / 1024 / 1024
print(f"\nDisk free: {free_gb:.1f} GB")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_large_upload.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/test_large_upload.py', timeout=300)
print(stdout.read().decode()[:3000])
err = stderr.read().decode()[:500]
if err: print("ERR:", err)

client.close()