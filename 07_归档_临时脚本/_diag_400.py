import paramiko

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

# Check the EXACT request body that OiioiiPool sent for task 400
stdin, stdout, stderr = ssh.exec_command('journalctl -u oiioii --no-pager --since "8 min ago" 2>/dev/null | grep -iE "generate_video:|resolve_video|videoUrl|submitted" | head -10')
print("OiioiiPool request details:")
print(stdout.read().decode()[:1000])

# Now directly check the Oiioii workspace for the account used by task 400
stdin, stdout, stderr = ssh.exec_command('''python3 -c "
import sqlite3, requests, json
conn = sqlite3.connect('/home/ubuntu/oiioii/data/oiioii_pool.db')
cur = conn.execute('SELECT a.email, a.password FROM tasks t JOIN accounts a ON t.account_id=a.id WHERE t.id=400')
email, password = cur.fetchone()

SPB_URL = 'https://spb.oiioii.ai'
SPB_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVndnV6ZXN0eXlwYm1jZnVycmJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEyMTU4NTEsImV4cCI6MjA3Njc5MTg1MX0.Z1qdxtK0PLF5NV1yXrI9s_W2Hurdxo143DBzuUuajh0'
API = 'https://api.oiioii.ai'

s = requests.Session()
r = s.post(f'{SPB_URL}/auth/v1/token?grant_type=password', json={'email': email, 'password': password}, headers={'apikey': SPB_KEY}, timeout=15)
token = r.json().get('access_token', '')
headers = {'Authorization': f'Bearer {token}'}

# Check async_tasks
r = s.get(f'{API}/media/canvas_async_tasks/sync', headers=headers, timeout=15)
tasks = r.json().get('data', {}).get('tasks', [])
print(f'Async tasks: {len(tasks)}')
for t in tasks[:5]:
    print(f'  {t.get(\"task_id\",\"\")[:50]} status={t.get(\"status\",\"\")} uri={t.get(\"result_payload\",{}).get(\"uri\",\"\")[:50]}')

# Check workspace
r = s.post(f'{API}/workspace/workspace_list', json={'data': {'limit': 10}}, headers=headers, timeout=15)
ws = r.json().get('data', {}).get('workspaces', [])
for w in ws:
    doc = w.get('workspaceDocument', {})
    assets = doc.get('assetList', [])
    print(f'Workspace assets: {len(assets)}')
    for a in assets[:5]:
        print(f'  uri={a.get(\"uri\",\"\")[:50]} type={a.get(\"type\",\"\")}')
"''')
print("\nDirect API check:")
print(stdout.read().decode()[:1500])

ssh.close()
