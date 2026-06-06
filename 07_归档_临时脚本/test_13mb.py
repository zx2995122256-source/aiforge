import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Test 13MB upload to OiioiiPool
script = r'''
import requests, time, base64

# Test 13MB file
data = b"x" * 13 * 1024 * 1024
print(f"File size: {len(data)} bytes")

# Check if issue is the base64 encoding size
b64 = base64.b64encode(data)
print(f"Base64 size: {len(b64)} bytes ({len(b64)/1024/1024:.1f} MB)")

# Test 1: Direct OiioiiPool upload
print("\n=== OiioiiPool upload_video_ref with 13MB ===")
start = time.time()
r = requests.post("http://127.0.0.1:7861/api/upload_video_ref",
    files={"file": ("test_13mb.mp4", data, "video/mp4")},
    timeout=180)
elapsed = time.time() - start
print(f"Status: {r.status_code}, Time: {elapsed:.1f}s")
print(f"Response: {r.text[:200]}")

# Test 2: Via AiForge backend 
print("\n=== AiForge upload_video_ref with 13MB ===")
r = requests.post("http://127.0.0.1:7862/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
start = time.time()
r = requests.post("http://127.0.0.1:7862/api/gen/upload_video_ref",
    headers={"Authorization": f"Bearer {token}"},
    files={"file": ("test_13mb.mp4", data, "video/mp4")},
    timeout=180)
elapsed = time.time() - start
print(f"Status: {r.status_code}, Time: {elapsed:.1f}s")
print(f"Response: {r.text[:200]}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_13mb.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/test_13mb.py', timeout=300)
print(stdout.read().decode()[:2000])
err = stderr.read().decode()[:300]
if err: print("ERR:", err)

client.close()