import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

script = r'''
import subprocess
import os

# Check OiioiiPool logs
r = subprocess.run(["journalctl", "-u", "oiioii", "--since", "10 min ago", "--no-pager"], capture_output=True, text=True, timeout=10)
lines = r.stdout.strip().split("\n")[-40:]
for l in lines:
    if any(x in l.lower() for x in ["error", "fail", "upload", "ref", "13mb", "larg", "size", "timeout"]):
        print(l)
if not lines:
    print("NO MATCHING LOGS")
else:
    print("--- last 5 lines ---")
    for l in lines[-5:]:
        print(l)

# Check if it's an auth issue
print("\n=== CHECK ACCOUNT ===")
import requests
# Check available accounts
r = requests.get("http://127.0.0.1:7861/api/pool/status", timeout=5)
print(r.json())

# Test account auth
r2 = requests.post("http://127.0.0.1:7861/api/generate_image",
    json={"prompt":"test","model":"Flux","ratio":"1:1","resolution":"1K","reference_images":[]},
    timeout=10)
print(f"Gen test: {r2.status_code} {r2.text[:100]}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/check_logs.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/check_logs.py', timeout=30)
print(stdout.read().decode()[:2000])
err = stderr.read().decode()[:300]
if err: print("ERR:", err)

client.close()