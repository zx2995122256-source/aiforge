import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

script = r'''
import requests
BASE = "http://127.0.0.1"

print("=== Test 1: OiioiiPool upload_video_ref ===")
r = requests.post(BASE + ":7861/api/upload_video_ref",
    files={"file": ("test.mp4", b"fake video", "video/mp4")},
    timeout=10)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:200]}")

print("\n=== Test 2: OiioiiPool upload_ref ===")
r = requests.post(BASE + ":7861/api/upload_ref",
    files={"file": ("test.png", b"fake png", "image/png")},
    timeout=10)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:200]}")

print("\n=== Test 3: OiioiiPool endpoints ===")
r = requests.get(BASE + ":7861/openapi.json", timeout=10)
for p in sorted(r.json().get("paths", {}).keys()):
    print(f"  {p}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_upload_v4.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/test_upload_v4.py', timeout=15)
print(stdout.read().decode()[:2000])
err = stderr.read().decode()[:300]
if err: print("ERR:", err)

client.close()