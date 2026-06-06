import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

script = r'''
import requests

# Test refs locally
urls = [
    "http://127.0.0.1:7862/api/gen/refs/vidref_1780291543_8719f3fa.mp4",
    "http://127.0.0.1:7862/refs/vidref_1780291543_8719f3fa.mp4",
    "http://122.51.205.94/api/gen/refs/vidref_1780291543_8719f3fa.mp4",
]

for url in urls:
    r = requests.get(url, timeout=10)
    print(f"{url}")
    print(f"  Status: {r.status_code}, Size: {len(r.content)}")
    if len(r.content) < 1000:
        print(f"  Content: {r.text[:100]}")

# Check if the ref file exists
import os
for f in ["/home/ubuntu/oiioii/data/output/refs/vidref_1780291543_8719f3fa.mp4"]:
    if os.path.exists(f):
        print(f"\nFile exists: {f} ({os.path.getsize(f)} bytes)")
    else:
        # Find it
        import subprocess
        r = subprocess.run(["find", "/home/ubuntu/oiioii/data/output/refs/", "-name", "*8719f3fa*"], capture_output=True, text=True, timeout=5)
        print(f"\nSearching: {r.stdout}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/check_ref_url.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/check_ref_url.py', timeout=15)
print(stdout.read().decode()[:1500])
err = stderr.read().decode()[:300]
if err: print("ERR:", err)

# Check what the OiioiiPool returns for the ref
stdin, stdout, stderr = client.exec_command(
    'ls -lah /home/ubuntu/oiioii/data/output/refs/ 2>/dev/null',
    timeout=10
)
print("\n=== All refs ===")
print(stdout.read().decode()[:500])

client.close()