#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', password='zx4579561.', timeout=15)

def run(cmd, timeout=15):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        return stdout.read().decode().strip(), stderr.read().decode().strip()
    except:
        return '(timeout)', ''

script = """
import requests, json

token = 'eyJhbGciOiJIUzI1NiIsImtpZCI6IlRxTGhKT0JtWi81K0txRkYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3VndnV6ZXN0eXlwYm1jZnVycmJkLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIzZTY5M2NlZS1lMjllLTRiMDQtOTczOS1iNTYwYWNmYzFmZWEiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzgwOTU2ODc3LCJpYXQiOjE3ODAzNTIwNzcsImVtYWlsIjoib2lpb19mdmk5ZGF4c3Q4YWxAd3NodS5uZXQiLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJsYW5ndWFnZSI6InpoIiwibmlja25hbWUiOiJvaWlvX2Z2aTlkYXhzdDhhbCJ9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzgwMzUyMDc3fV0sInNlc3Npb25faWQiOiI5YmJhMDA5NS05Yzg0LTQwZWUtYmUwYS00NDU0MzI4ODVkNjciLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.n1D9-XE1n8Hgy1tPRR7hbZhbkxYHPmRfmOUANZIUu28'

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

API = 'https://api.oiioii.ai'
ws_id = 'ea60835a-b42e-4300-9fca-f1562b675a09'

# canvas_async_tasks/sync is GET with query params!
r = requests.get(f'{API}/media/canvas_async_tasks/sync?workspaceId={ws_id}', headers=headers, timeout=15)
print(f'canvas_async_tasks/sync GET: {r.status_code}')
print(r.text[:500])

# Try workspace_list with limit=50 (maybe need more)
print()
r2 = requests.post(f'{API}/workspace/workspace_list', json={"data": {"limit": 50}}, headers=headers, timeout=15)
if r2.status_code == 200:
    data = r2.json()
    workspaces = data.get('data', {}).get('workspaces', [])
    print(f'workspace_list: {len(workspaces)} workspaces')
    for ws in workspaces:
        doc = ws.get('workspaceDocument', {})
        has_assets = 'assetList' in doc
        print(f'  ws={ws.get("workspaceId","")[:20]} has_assetList={has_assets} keys={list(doc.keys())}')
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/_test_sync.py', 'w') as f:
    f.write(script)
sftp.close()

out, err = run('python3 /tmp/_test_sync.py')
print(out[:3000])

ssh.close()
