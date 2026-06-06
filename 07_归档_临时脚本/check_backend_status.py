import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

script = r'''
import requests, json, time

# 1. Check AiForge tasks
print("=== AiForge tasks ===")
r = requests.post("http://127.0.0.1:7862/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

r = requests.get("http://127.0.0.1:7862/api/gen/tasks", headers=headers, timeout=10)
tasks = r.json()
for t in tasks[-10:]:
    status = t.get("status","")
    vid_ref = "✅ref" if t.get("reference_video") else "❌无ref"
    age = int(time.time() - t.get("created_at", 0))
    print(f"  #{t['id']} {t.get('task_type','')} {status:12} age={age}s {vid_ref} {t.get('prompt','')[:30]}")

# 2. Check OiioiiPool tasks
print("\n=== OiioiiPool tasks ===")
r = requests.get("http://127.0.0.1:7861/api/tasks", timeout=10)
pool_tasks = r.json()
if isinstance(pool_tasks, list):
    for t in pool_tasks[-10:]:
        age = int(time.time() - t.get("created_at", 0))
        print(f"  #{t['id']} {t.get('task_type','')} {t.get('status','')} age={age}s {t.get('prompt','')[:30]}")
else:
    print(pool_tasks)

# 3. Check OiioiiPool pool status
print("\n=== Pool status ===")
r = requests.get("http://127.0.0.1:7861/api/pool/status", timeout=10)
print(r.json())
'''

sftp = client.open_sftp()
with sftp.file('/tmp/check_status.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/check_status.py', timeout=15)
print(stdout.read().decode()[:2000])
err = stderr.read().decode()[:300]
if err: print("ERR:", err)

client.close()