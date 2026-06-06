import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

script = r'''
import requests, sqlite3

# 1. Get all tasks from AiForge DB directly  
conn = sqlite3.connect("/home/ubuntu/aiforge/backend/data/aiforge.db")
rows = conn.execute("SELECT id, task_type, status, oiioii_task_id, prompt FROM tasks WHERE user_id=1 ORDER BY id").fetchall()
print("=== AiForge tasks ===")
for r in rows:
    ref = "✅ref视频" if conn.execute("SELECT reference_video FROM tasks WHERE id=?", (r[0],)).fetchone() and conn.execute("SELECT reference_video FROM tasks WHERE id=?", (r[0],)).fetchone()[0] else "❌无ref"
    if r[0] >= 30:
        print(f"  #{r[0]} {r[1]:5} {r[2]:10} oid={r[3]} {ref} | {r[4][:40]}")
conn.close()

# 2. Get all Pool tasks that are still processing
conn2 = sqlite3.connect("/home/ubuntu/oiioii/data/oiioii_pool.db")
rows2 = conn2.execute("SELECT id, task_type, status, prompt FROM tasks WHERE status='processing' OR status='running' ORDER BY id DESC LIMIT 10").fetchall()
print("\n=== OiioiiPool processing tasks ===")
for r in rows2:
    print(f"  #{r[0]} {r[1]:5} {r[2]:10} | {r[3][:40]}")
conn2.close()

# 3. Login to see if there are tasks with ref video
BASE = "http://127.0.0.1:7862"
r = requests.post(BASE + "/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

r = requests.get(BASE + "/api/gen/tasks", headers=headers, timeout=10)
tasks = r.json()
print(f"\n=== Last 5 from API ===")
for t in tasks[-5:]:
    ref_video = "✅vid" if t.get("reference_video") else "❌无"
    print(f"  #{t['id']} {t['task_type']} {t['status']:10} ref_video={ref_video} | {t.get('prompt','')[:30]}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/check_all_tasks.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/check_all_tasks.py', timeout=15)
print(stdout.read().decode()[:2000])
err = stderr.read().decode()[:500]
if err: print("ERR:", err)

client.close()