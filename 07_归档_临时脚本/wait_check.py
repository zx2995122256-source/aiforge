import paramiko, time

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

script = r'''
import requests, time

BASE = "http://127.0.0.1"
r = requests.post(BASE + ":7862/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

for i in range(6):
    time.sleep(10)
    for tid in [37, 38]:
        r = requests.get(BASE + f":7862/api/gen/task/{tid}", headers=headers, timeout=10)
        t = r.json()
        s = t["status"]
        oid = t.get("oiioii_task_id", 0)
        r2 = requests.get(BASE + f":7861/api/task/{oid}", timeout=10)
        ps = r2.json().get("status", "?")
        result = "✅" if t.get("result_url") else ""
        print(f"[{i*10}s] #{tid} Ai={s:10} Pool={ps:10} {result}")
        if s == "completed":
            print(f"  URL: {t.get('result_url', '?')}")
    if i >= 3:
        break
'''

sftp = client.open_sftp()
with sftp.file('/tmp/wait_and_check.py', 'w') as f:
    f.write(script)
sftp.close()

print("Waiting for tasks...")
stdin, stdout, stderr = client.exec_command('python3 /tmp/wait_and_check.py', timeout=120)
print(stdout.read().decode()[:1000])

client.close()