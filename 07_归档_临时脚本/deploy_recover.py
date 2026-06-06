import paramiko, tarfile, io

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Package backend only
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w:gz') as tar:
    tar.add(r"C:\Users\Administrator\Documents\AiForge\backend\api\generate.py", "backend/api/generate.py")
buf.seek(0)

sftp = client.open_sftp()
with sftp.file('/tmp/recover_fix.tar.gz', 'wb') as f:
    f.write(buf.getvalue())
sftp.close()

cmds = [
    "tar -xzf /tmp/recover_fix.tar.gz -C /tmp && cp /tmp/backend/api/generate.py /home/ubuntu/aiforge/backend/api/generate.py",
    "sudo systemctl restart aiforge && sleep 3",
]
for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
    out = stdout.read().decode().strip()
    if out: print(out[:200])

# Check if tasks recover
script = r'''
import requests
BASE = "http://127.0.0.1:7862"
r = requests.post(BASE + "/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# Check #37 - should auto-recover to completed
r = requests.get(BASE + "/api/gen/task/37", headers=headers, timeout=15)
t = r.json()
print(f"#37: {t['status']} | url={t.get('result_url','')[:50]}")

# Check #38
r = requests.get(BASE + "/api/gen/task/38", headers=headers, timeout=15)
t = r.json()
print(f"#38: {t['status']} | url={t.get('result_url','')[:50]}")

# Also check OiioiiPool
r2 = requests.get("http://127.0.0.1:7861/api/task/297", timeout=10)
print(f"Pool #297: {r2.json().get('status','?')}")
r2 = requests.get("http://127.0.0.1:7861/api/task/298", timeout=10)
print(f"Pool #298: {r2.json().get('status','?')}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/check_recovery.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/check_recovery.py', timeout=15)
print("\n" + stdout.read().decode()[:500])

client.close()