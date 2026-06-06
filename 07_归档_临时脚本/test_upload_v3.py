import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Upload test script to server
sftp = client.open_sftp()
with sftp.file('/tmp/test_upload_server.py', 'w') as f:
    f.write('''
import requests

BASE = "http://127.0.0.1"

# Test 1: OiioiiPool upload_video_ref directly
print("=== Test 1: OiioiiPool upload_video_ref ===")
r = requests.post(f"{BASE}:7861/api/upload_video_ref",
    files={"file": ("test.mp4", b"fake video content for testing", "video/mp4")},
    timeout=10)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:200]}")

# Test 2: OiioiiPool upload_ref (image)
print("\n=== Test 2: OiioiiPool upload_ref ===")
r = requests.post(f"{BASE}:7861/api/upload_ref",
    files={"file": ("test.png", b"fake png content", "image/png")},
    timeout=10)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:200]}")

# Test 3: List all OiioiiPool API endpoints
print("\n=== Test 3: OiioiiPool routes ===")
r = requests.get(f"{BASE}:7861/openapi.json", timeout=10)
paths = r.json().get("paths", {})
for p in sorted(paths.keys()):
    print(f"  {p}")
''')
sftp.close()

stdin, stdout, stderr = client.exec_command('cd /tmp && python3 test_upload_server.py', timeout=15)
out = stdout.read().decode()
err = stderr.read().decode()
print(out)
if err: print("STDERR:", err[:300])

client.close()