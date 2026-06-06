import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check what refs routes exist in the backend
stdin, stdout, stderr = client.exec_command(
    'grep -n "refs\|serve_ref" /home/ubuntu/aiforge/backend/api/generate.py | head -10',
    timeout=10
)
print("=== Refs in generate.py ===")
print(stdout.read().decode()[:500])

# Check if the route exists in OpenAPI
script = r'''
import requests
r = requests.get("http://127.0.0.1:7862/openapi.json", timeout=10)
paths = r.json().get("paths", {})
ref_paths = [p for p in paths if "ref" in p.lower()]
print("Ref endpoints:")
for p in ref_paths:
    print(f"  {p}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/check_openapi.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/check_openapi.py', timeout=10)
print(stdout.read().decode()[:500])

# Fix: add the refs route properly
stdin, stdout, stderr = client.exec_command(
    '''python3 -c "
with open('/home/ubuntu/aiforge/backend/api/generate.py') as f:
    content = f.read()
idx = content.find('def serve_ref')
if idx >= 0:
    print('serve_ref found at', idx)
else:
    print('serve_ref NOT found')
idx2 = content.find('import os, hashlib, time')
if idx2 >= 0:
    print('refs imports found at', idx2)
" ''',
    timeout=10
)
print(stdout.read().decode()[:200])

client.close()