import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check what API_BASE is and test multipart upload
script = r'''
import requests, base64, time

# Test 1: Try multipart upload to the external API
# First get an account token  
import sys
sys.path.insert(0, "/home/ubuntu/oiioii/core")
sys.path.insert(0, "/home/ubuntu/oiioii")

# Read API_BASE from client  
with open("/home/ubuntu/oiioii/core/core/client.py") as f:
    for line in f:
        if "API_BASE" in line and "=" in line and "http" in line:
            API_BASE = line.split("=")[1].strip().strip('"').strip("'")
            print(f"API_BASE = {API_BASE}")
            break

# Test multipart upload with 13MB file
data = b"x" * 13 * 1024 * 1024
print(f"\nTesting multipart with {len(data)} bytes...")

# Use a fresh session  
s = requests.Session()
# First login to get token
r = s.post(f"{API_BASE}/auth/login", json={"email":"oiio_xxx@test.com","password":"test"}, timeout=10)
print(f"Login: {r.status_code}")

# Actually let me just test whether the external API supports multipart
# Try sending as multipart file
r = s.post(f"{API_BASE}/res/upload_file", 
    files={"file": ("test.mp4", data, "video/mp4")},
    timeout=180)
print(f"Multipart upload: {r.status_code} {r.text[:200]}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_multipart.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/test_multipart.py', timeout=300)
print(stdout.read().decode()[:2000])
err = stderr.read().decode()[:300]
if err: print("ERR:", err)
client.close()