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

# Get full workspace data
r = requests.post(f'{API}/workspace/workspace_list', json={"data": {"limit": 10}}, headers=headers, timeout=15)
data = r.json()
# Print the full structure of first workspace
ws = data.get('data', {}).get('workspaces', [])[0] if data.get('data', {}).get('workspaces') else {}
doc = ws.get('workspaceDocument', {})
print('workspaceDocument keys:', list(doc.keys()))
print()
# Print full doc structure (truncated)
print(json.dumps(doc, ensure_ascii=False, indent=2)[:3000])

# Try alternative API endpoints
print('\\n=== Testing alternative endpoints ===')

# Try /workspace/detail
r2 = requests.post(f'{API}/workspace/detail', json={"data": {"workspaceId": "ea60835a-b42e-4300-9fca-f1562b675a09"}}, headers=headers, timeout=15)
print(f'/workspace/detail: {r2.status_code} -> {r2.text[:200]}')

# Try /media/list
r3 = requests.post(f'{API}/media/list', json={"data": {"workspaceId": "ea60835a-b42e-4300-9fca-f1562b675a09", "limit": 10}}, headers=headers, timeout=15)
print(f'/media/list: {r3.status_code} -> {r3.text[:200]}')

# Try /asset/list
r4 = requests.post(f'{API}/asset/list', json={"data": {"workspaceId": "ea60835a-b42e-4300-9fca-f1562b675a09"}}, headers=headers, timeout=15)
print(f'/asset/list: {r4.status_code} -> {r4.text[:200]}')

# Try /workspace/asset_list
r5 = requests.post(f'{API}/workspace/asset_list', json={"data": {"workspaceId": "ea60835a-b42e-4300-9fca-f1562b675a09"}}, headers=headers, timeout=15)
print(f'/workspace/asset_list: {r5.status_code} -> {r5.text[:200]}')
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/_test_api3.py', 'w') as f:
    f.write(script)
sftp.close()

out, err = run('python3 /tmp/_test_api3.py')
print(out[:4000])

ssh.close()
