import paramiko

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

script = r'''
import sqlite3, requests, json, sys

conn = sqlite3.connect('/home/ubuntu/oiioii/data/oiioii_pool.db')

# Check ALL recent tasks and their accounts
cur = conn.execute("""
    SELECT t.id, t.account_id, a.email, a.password, t.status, t.result_uri, t.task_id
    FROM tasks t JOIN accounts a ON t.account_id=a.id 
    WHERE t.id >= 395 ORDER BY t.id DESC
""")
tasks = cur.fetchall()
print(f"Recent tasks: {len(tasks)}")
for t in tasks:
    print(f"  ID={t[0]} account={t[2][:25]} status={t[4]} uri={str(t[5])[:40]} remote_id={str(t[6])[:40]}")

# For each account, check workspace and async_tasks
SPB_URL = "https://spb.oiioii.ai"
SPB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVndnV6ZXN0eXlwYm1jZnVycmJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEyMTU4NTEsImV4cCI6MjA3Njc5MTg1MX0.Z1qdxtK0PLF5NV1yXrI9s_W2Hurdxo143DBzuUuajh0"
API = "https://api.oiioii.ai"

checked = set()
for t in tasks:
    email, password = t[2], t[3]
    if email in checked:
        continue
    checked.add(email)
    
    s = requests.Session()
    r = s.post(f"{SPB_URL}/auth/v1/token?grant_type=password", json={"email": email, "password": password}, headers={"apikey": SPB_KEY}, timeout=15)
    token = r.json().get("access_token", "")
    if not token:
        print(f"\n{email}: login failed")
        continue
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check async_tasks
    r = s.get(f"{API}/media/canvas_async_tasks/sync", headers=headers, timeout=15)
    async_tasks = r.json().get("data", {}).get("tasks", [])
    
    # Check workspace
    r = s.post(f"{API}/workspace/workspace_list", json={"data": {"limit": 10}}, headers=headers, timeout=15)
    ws = r.json().get("data", {}).get("workspaces", [])
    
    print(f"\n=== {email} ===")
    print(f"  Async tasks: {len(async_tasks)}")
    for at in async_tasks[:5]:
        tid = at.get("task_id", "")[:50]
        status = at.get("status", "")
        uri = at.get("result_payload", {}).get("uri", "")[:50]
        print(f"    {tid} status={status} uri={uri}")
    
    print(f"  Workspaces: {len(ws)}")
    for w in ws:
        doc = w.get("workspaceDocument", {})
        has_assets = "assetList" in doc
        assets = doc.get("assetList", [])
        print(f"    has_assetList={has_assets} assets={len(assets)}")
        for a in assets[:5]:
            print(f"      uri={a.get('uri','')[:50]} type={a.get('type','')}")

conn.close()
'''

sftp = ssh.open_sftp()
with sftp.open('/tmp/diag_full.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/diag_full.py')
out = stdout.read().decode()
print(out[:5000])

ssh.close()
