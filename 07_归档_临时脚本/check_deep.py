import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

script = r'''
import requests, time

# Login
r = requests.post("http://127.0.0.1:7862/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 1. All AiForge tasks sorted by id DESC
print("=== AiForge ALL tasks (latest first) ===")
r = requests.get("http://127.0.0.1:7862/api/gen/tasks", headers=headers, timeout=10)
tasks = sorted(r.json(), key=lambda t: -t["id"])
for t in tasks:
    age = int(time.time() - t.get("created_at", 0))
    status = t.get("status","")
    ref = "✅ref" if t.get("reference_video") else "❌无ref" if t.get("task_type") == "video" else "  "
    print(f"  #{t['id']} {t.get('task_type',''):5} {status:10} age={age:5}s {ref} | {t.get('prompt','')[:40]}")

# 2. OiioiiPool newest tasks
print("\n=== OiioiiPool tasks (latest 20) ===")
r = requests.get("http://127.0.0.1:7861/api/tasks", timeout=10)
data = r.json()
if isinstance(data, dict) and "tasks" in data:
    ptasks = data["tasks"]
elif isinstance(data, list):
    ptasks = data
else:
    ptasks = []

for t in sorted(ptasks, key=lambda t: -t["id"])[:20]:
    age = int(time.time() - t.get("created_at", 0))
    status = t.get("status","")
    print(f"  #{t['id']} {t.get('task_type',''):5} {status:10} age={age:5}s | {t.get('prompt','')[:50]}")

# 3. Check OiioiiPool logs for recent errors
import subprocess
r = subprocess.run(["journalctl", "-u", "oiioii", "--since", "30 min ago", "--no-pager"], capture_output=True, text=True, timeout=10)
errors = [l for l in r.stdout.split("\n") if any(x in l.lower() for x in ["error", "exception", "traceback", "fail", "timeout", "rate limit"])]
for l in errors[-10:]:
    print(f"  {l}")
if not errors:
    print("  No recent errors")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/check_deep.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/check_deep.py', timeout=15)
print(stdout.read().decode()[:3000])
err = stderr.read().decode()[:500]
if err: print("ERR:", err)

client.close()