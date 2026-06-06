import paramiko

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

script = r'''
import sqlite3, requests, json, sys

conn = sqlite3.connect('/home/ubuntu/oiioii/data/oiioii_pool.db')
cur = conn.execute("SELECT email, password FROM accounts WHERE email='oiio_fvi9daxst8al@wshu.net'")
email, password = cur.fetchone()

SPB_URL = "https://spb.oiioii.ai"
SPB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVndnV6ZXN0eXlwYm1jZnVycmJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEyMTU4NTEsImV4cCI6MjA3Njc5MTg1MX0.Z1qdxtK0PLF5NV1yXrI9s_W2Hurdxo143DBzuUuajh0"
API = "https://api.oiioii.ai"

s = requests.Session()
r = s.post(f"{SPB_URL}/auth/v1/token?grant_type=password", json={"email": email, "password": password}, headers={"apikey": SPB_KEY}, timeout=15)
token = r.json().get("access_token", "")
headers = {"Authorization": f"Bearer {token}"}

# 1. Get workspace list - full response
r = s.post(f"{API}/workspace/workspace_list", json={"data": {"limit": 10}}, headers=headers, timeout=15)
ws_data = r.json()
print("=== workspace_list FULL response ===")
print(json.dumps(ws_data, indent=2)[:2000])

# 2. Try creating a new workspace
print("\n=== create_workspace ===")
r = s.post(f"{API}/workspace/create_workspace", json={"data": {}}, headers=headers, timeout=15)
print(f"Status: {r.status_code}")
print(r.text[:500])

# 3. Check workspace_list again
print("\n=== workspace_list AFTER create ===")
r = s.post(f"{API}/workspace/workspace_list", json={"data": {"limit": 10}}, headers=headers, timeout=15)
ws = r.json().get("data", {}).get("workspaces", [])
print(f"Workspaces: {len(ws)}")
for w in ws:
    wid = w.get("workspaceId", "")
    doc = w.get("workspaceDocument", {})
    has_assets = "assetList" in doc
    print(f"  ws={wid} has_assetList={has_assets} keys={list(doc.keys())}")

# 4. Try update_workspace with assetList
if ws:
    wid = ws[0].get("workspaceId", "")
    print(f"\n=== update_workspace (adding assetList) for {wid[:20]} ===")
    r = s.post(f"{API}/workspace/update_workspace", json={"data": {"workspaceId": wid, "assetList": []}}, headers=headers, timeout=15)
    print(f"Status: {r.status_code}")
    print(r.text[:500])

    # Check again
    r = s.post(f"{API}/workspace/workspace_list", json={"data": {"limit": 10}}, headers=headers, timeout=15)
    ws2 = r.json().get("data", {}).get("workspaces", [])
    for w in ws2:
        wid2 = w.get("workspaceId", "")
        doc2 = w.get("workspaceDocument", {})
        has2 = "assetList" in doc2
        print(f"  ws={wid2[:20]} has_assetList={has2}")

conn.close()
'''

sftp = ssh.open_sftp()
with sftp.open('/tmp/diag_workspace.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/diag_workspace.py')
out = stdout.read().decode()
print(out[:4000])

ssh.close()
