import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

script = r'''
import requests

BASE = "http://127.0.0.1:7862"

# Login
r = requests.post(BASE + "/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# Test upload_video_ref via AiForge proxy
print("=== Test: AiForge upload_video_ref ===")
r = requests.post(BASE + "/api/gen/upload_video_ref",
    headers=headers,
    files={"file": ("test.mp4", b"fake video content for testing", "video/mp4")},
    timeout=15)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:300]}")

# Test upload_ref via AiForge proxy
print("\n=== Test: AiForge upload_ref ===")
r = requests.post(BASE + "/api/gen/upload_ref",
    headers=headers,
    files={"file": ("test.png", b"fake png content", "image/png")},
    timeout=15)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:300]}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_aiforge_upload.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/test_aiforge_upload.py', timeout=15)
print(stdout.read().decode()[:2000])
err = stderr.read().decode()[:300]
if err: print("ERR:", err)

client.close()