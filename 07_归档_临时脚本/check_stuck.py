import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

script = r'''
import requests, time, subprocess

BASE = "http://127.0.0.1"

# Check AiForge task detail for the stuck ones
r = requests.post(BASE + ":7862/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# Check each stuck task
for af_id in [36, 35, 34, 31]:
    r = requests.get(BASE + f":7862/api/gen/task/{af_id}", headers=headers, timeout=10)
    try:
        t = r.json()
        oid = t.get("oiioii_task_id", 0)
        print(f"AiForge #{af_id}: status={t['status']} oiioii_id={oid} | {t.get('prompt','')[:30]}")
        # Also check OiioiiPool side
        if oid:
            r2 = requests.get(BASE + f":7861/api/task/{oid}", timeout=10)
            pt = r2.json()
            print(f"  OiioiiPool #{oid}: status={pt.get('status','?')}")
    except Exception as e:
        print(f"AiForge #{af_id}: error {e}")

# Check OiioiiPool task detail for #295 and #296
print()
for oid in [296, 295, 294, 293]:
    r = requests.get(BASE + f":7861/api/task/{oid}", timeout=10)
    try:
        t = r.json()
        print(f"OiioiiPool #{oid}: status={t.get('status','?')} model={t.get('model','')} age={int(time.time()-t.get('created_at',0))}s")
    except:
        print(f"OiioiiPool #{oid}: {r.text[:100]}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/check_stuck_tasks.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/check_stuck_tasks.py', timeout=15)
print(stdout.read().decode()[:1500])
err = stderr.read().decode()[:300]
if err: print("ERR:", err)

# Also check the /api/gen/task/{id} endpoint
stdin, stdout, stderr = client.exec_command(
    "grep -n -A 15 '@router.get(\"/task\"' /home/ubuntu/aiforge/backend/api/generate.py",
    timeout=10
)
print("\n=== Task detail endpoint ===")
print(stdout.read().decode()[:1000])

client.close()