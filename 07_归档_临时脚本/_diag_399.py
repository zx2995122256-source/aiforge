import paramiko

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

# Check the account used for task 399 and its async_tasks
script = r'''
import sqlite3, requests, json, sys

conn = sqlite3.connect('/home/ubuntu/oiioii/data/oiioii_pool.db')
cur = conn.execute("SELECT t.account_id, a.email, a.password FROM tasks t JOIN accounts a ON t.account_id=a.id WHERE t.id=399")
row = cur.fetchone()
if not row:
    print("Task 399 not found")
    sys.exit(1)
aid, email, password = row
print(f"Account: {email}")

SPB_URL = "https://spb.oiioii.ai"
SPB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVndnV6ZXN0eXlwYm1jZnVycmJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEyMTU4NTEsImV4cCI6MjA3Njc5MTg1MX0.Z1qdxtK0PLF5NV1yXrI9s_W2Hurdxo143DBzuUuajh0"
API = "https://api.oiioii.ai"

s = requests.Session()
r = s.post(f"{SPB_URL}/auth/v1/token?grant_type=password", json={"email": email, "password": password}, headers={"apikey": SPB_KEY}, timeout=15)
token = r.json().get("access_token", "")
if not token:
    print(f"Login failed: {r.text[:200]}")
    sys.exit(1)
print("Login OK")

headers = {"Authorization": f"Bearer {token}"}

# Check async tasks
r = s.get(f"{API}/media/canvas_async_tasks/sync", headers=headers, timeout=15)
tasks = r.json().get("data", {}).get("tasks", [])
print(f"\nAsync tasks: {len(tasks)}")
for t in tasks[:10]:
    tid = t.get("task_id", "")[:60]
    status = t.get("status", "")
    uri = t.get("result_payload", {}).get("uri", "")[:50]
    print(f"  {tid} status={status} uri={uri}")

# Check workspace
r = s.post(f"{API}/workspace/workspace_list", json={"data": {"limit": 10}}, headers=headers, timeout=15)
ws = r.json().get("data", {}).get("workspaces", [])
print(f"\nWorkspaces: {len(ws)}")
for w in ws:
    wid = w.get("workspaceId", "")[:20]
    doc = w.get("workspaceDocument", {})
    has_assets = "assetList" in doc
    asset_count = len(doc.get("assetList", [])) if has_assets else 0
    print(f"  ws={wid} has_assetList={has_assets} assets={asset_count}")
    if has_assets:
        for a in doc.get("assetList", [])[:5]:
            print(f"    uri={a.get('uri','')[:50]} type={a.get('type','')}")

conn.close()
'''

sftp = ssh.open_sftp()
with sftp.open('/tmp/diag_399.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/diag_399.py')
out = stdout.read().decode()
print(out[:3000])

ssh.close()
