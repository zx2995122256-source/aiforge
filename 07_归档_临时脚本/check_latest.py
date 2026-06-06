import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

script = r'''
import requests, time, sqlite3

BASE = "http://127.0.0.1"

# Login
r = requests.post(BASE + ":7862/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# Check task #37 (with ref) and #38 (no ref)
for tid in [37, 38]:
    r = requests.get(BASE + f":7862/api/gen/task/{tid}", headers=headers, timeout=10)
    t = r.json()
    oid = t.get("oiioii_task_id", 0)
    print(f"AiForge #{tid}: {t['status']} oid={oid}")
    if oid:
        r2 = requests.get(BASE + f":7861/api/task/{oid}", timeout=10)
        pt = r2.json()
        print(f"  OiioiiPool #{oid}: {pt.get('status','?')} model={pt.get('model','?')}")

# Check AiForge poll logs
import subprocess
r = subprocess.run(["journalctl", "-u", "aiforge", "--since", "3 min ago", "--no-pager"], capture_output=True, text=True, timeout=10)
lines = r.stdout.split("\n")
polls = [l for l in lines if "[Poll]" in l]
for l in polls[-5:]:
    print(f"\n  {l.strip()[:120]}")

# Check OiioiiPool processing tasks
conn = sqlite3.connect("/home/ubuntu/oiioii/data/oiioii_pool.db")
rows = conn.execute("SELECT id, status, model, created_at FROM tasks WHERE status='processing' ORDER BY id DESC LIMIT 5").fetchall()
for r2 in rows:
    age = int(time.time() - r2[3])
    print(f"\n  Pool #{r2[0]}: {r2[1]} {r2[2]} age={age}s")
conn.close()
'''

sftp = client.open_sftp()
with sftp.file('/tmp/check_latest.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/check_latest.py', timeout=15)
print(stdout.read().decode()[:1000])

client.close()