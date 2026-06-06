import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check services
for svc in ['aiforge', 'oiioii']:
    stdin, stdout, stderr = client.exec_command(f'sudo systemctl is-active {svc}', timeout=10)
    print(f"{svc}: {stdout.read().decode().strip()}")

# Quick test
script = r'''
import requests
r = requests.post("http://127.0.0.1:7862/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
print(f"Login: {r.status_code}")
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}
# Upload 5MB
data = b"x" * 5 * 1024 * 1024
r = requests.post("http://127.0.0.1:7862/api/gen/upload_video_ref",
    headers=headers, files={"file": ("test.mp4", data, "video/mp4")}, timeout=30)
print(f"Upload: {r.status_code}")
if r.status_code == 200:
    uri = r.json().get("uri", "")
    r2 = requests.get(uri, timeout=10)
    print(f"Ref: {r2.status_code}, {len(r2.content)}b (expected {len(data)}b)")
    print("OK" if len(r2.content) == len(data) else "SIZE MISMATCH")
else:
    print(r.text[:200])
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_quick.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/test_quick.py', timeout=30)
print("\n" + stdout.read().decode()[:500])

client.close()