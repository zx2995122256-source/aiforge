import paramiko

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

# Run a diagnostic script on the server that directly calls the Oiioii API
script = r'''
import requests, json, sys, time

# Login to the account used for task 396
email = "oiio_fvi9daxst8al@wshu.net"
password = "Oiioii@2024"

API = "https://www.oiioii.ai/api"

s = requests.Session()

# Login
r = s.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=15)
login = r.json()
token = login.get("data", {}).get("accessToken", "")
if not token:
    print(f"Login failed: {r.text[:200]}")
    sys.exit(1)
print(f"Login OK, token: {token[:30]}...")

headers = {"Authorization": f"Bearer {token}"}

# Check canvas_async_tasks
r = s.get(f"{API}/media/canvas_async_tasks/sync", headers=headers, timeout=15)
tasks_data = r.json().get("data", {}).get("tasks", [])
print(f"\nAsync tasks: {len(tasks_data)}")
for t in tasks_data:
    print(f"  task_id={t.get('task_id','')[:40]} status={t.get('status','')} uri={t.get('result_payload',{}).get('uri','')[:50]}")

# Check workspace list
r = s.post(f"{API}/workspace/workspace_list", json={"data": {"limit": 10}}, headers=headers, timeout=15)
ws_data = r.json().get("data", {}).get("workspaces", [])
print(f"\nWorkspaces: {len(ws_data)}")
for w in ws_data:
    wid = w.get("workspaceId", "")[:20]
    doc = w.get("workspaceDocument", {})
    has_assets = "assetList" in doc
    asset_count = len(doc.get("assetList", [])) if has_assets else 0
    print(f"  ws={wid} has_assetList={has_assets} assets={asset_count}")
    if has_assets:
        for a in doc.get("assetList", [])[:5]:
            print(f"    uri={a.get('uri','')[:50]} type={a.get('type','')}")

# Check the specific task remote_id
remote_id = "video_generate_1780352300509_6cv72fg"
print(f"\nLooking for task: {remote_id}")
found = False
for t in tasks_data:
    if remote_id in t.get("task_id", ""):
        print(f"  FOUND: {json.dumps(t, indent=2)[:500]}")
        found = True
if not found:
    print("  NOT FOUND in async_tasks")

print("\n=== DONE ===")
'''

sftp = ssh.open_sftp()
with sftp.open('/tmp/diag_oiioii.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/diag_oiioii.py')
out = stdout.read().decode()
err = stderr.read().decode()
print(out[:3000])
if err:
    print(f"STDERR: {err[:500]}")

ssh.close()
