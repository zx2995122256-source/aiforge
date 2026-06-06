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

# Test the workspace_list API that _get_asset_list actually uses
script = """
import requests, json

token = 'eyJhbGciOiJIUzI1NiIsImtpZCI6IlRxTGhKT0JtWi81K0txRkYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3VndnV6ZXN0eXlwYm1jZnVycmJkLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIzZTY5M2NlZS1lMjllLTRiMDQtOTczOS1iNTYwYWNmYzFmZWEiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzgwOTU2ODc3LCJpYXQiOjE3ODAzNTIwNzcsImVtYWlsIjoib2lpb19mdmk5ZGF4c3Q4YWxAd3NodS5uZXQiLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJsYW5ndWFnZSI6InpoIiwibmlja25hbWUiOiJvaWlvX2Z2aTlkYXhzdDhhbCJ9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzgwMzUyMDc3fV0sInNlc3Npb25faWQiOiI5YmJhMDA5NS05Yzg0LTQwZWUtYmUwYS00NDU0MzI4ODVkNjciLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.n1D9-XE1n8Hgy1tPRR7hbZhbkxYHPmRfmOUANZIUu28'

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# This is what _get_asset_list actually calls
r = requests.post('https://ugvuzestyypbmcfurrbd.supabase.co/functions/v1/workspace/workspace_list',
                   json={"data": {"limit": 10}}, headers=headers, timeout=15)
print(f'workspace_list status: {r.status_code}')
data = r.json()
print(f'Response keys: {list(data.keys()) if isinstance(data, dict) else type(data)}')

# Check workspaces
workspaces = data.get('data', {}).get('workspaces', [])
print(f'Workspaces count: {len(workspaces)}')
for ws in workspaces[:3]:
    ws_id = ws.get('workspaceId', '')[:20]
    doc = ws.get('workspaceDocument', {})
    has_assets = 'assetList' in doc
    asset_count = len(doc.get('assetList', [])) if has_assets else 0
    print(f'  ws={ws_id}... has_assetList={has_assets} assets={asset_count}')
    if has_assets and asset_count > 0:
        for a in doc['assetList'][-3:]:
            print(f'    type={a.get("type")} uri={a.get("uri","")[:60]}')
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/_test_ws.py', 'w') as f:
    f.write(script)
sftp.close()

out, err = run('python3 /tmp/_test_ws.py')
print(out[:2000])
if err:
    print(f'ERR: {err[:300]}')

ssh.close()
