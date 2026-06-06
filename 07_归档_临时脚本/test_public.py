import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

script = r'''
import requests

# Test 1: Is AiForge serving refs?
print("=== Test: Refs served by AiForge ===")
r = requests.get("http://127.0.0.1:7862/refs/vidref_1780291543_1a156a43.mp4", timeout=10)
print(f"Status: {r.status_code}, Size: {len(r.content)}")

# Test 2: Can the external API reach it?
r2 = requests.get("http://122.51.205.94/refs/vidref_1780291543_1a156a43.mp4", timeout=10)
print(f"\n=== Test: Public access ===")
print(f"Status: {r2.status_code}, Size: {len(r2.content)}")

# Test 3: Check if the /refs endpoint exists in AiForge
r3 = requests.get("http://127.0.0.1:7862/openapi.json", timeout=10)
paths = r3.json().get("paths", {})
ref_paths = [p for p in paths if "ref" in p]
print(f"\n=== AiForge paths with 'ref' ===")
for p in ref_paths:
    print(f"  {p}: {list(paths[p].keys())}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_public.py', 'w') as f:
    f.write(script)
sftp.close()

print("Running tests...")
stdin, stdout, stderr = client.exec_command('python3 /tmp/test_public.py', timeout=15)
print(stdout.read().decode()[:1000])
err = stderr.read().decode()[:300]
if err: print("ERR:", err)

client.close()