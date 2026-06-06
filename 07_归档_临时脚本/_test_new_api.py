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

# Test get_workspace
r = requests.post(f'{API}/workspace/get_workspace', json={"data": {"workspaceId": ws_id}}, headers=headers, timeout=15)
print(f'/workspace/get_workspace: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    d = data.get('data', data)
    print(json.dumps(d, ensure_ascii=False, indent=2)[:3000])
else:
    print(r.text[:300])

# Test workspace_logs
print()
r2 = requests.post(f'{API}/points/workspace_logs', json={"data": {"workspaceId": ws_id, "limit": 10}}, headers=headers, timeout=15)
print(f'/points/workspace_logs: {r2.status_code}')
if r2.status_code == 200:
    data2 = r2.json()
    print(json.dumps(data2, ensure_ascii=False, indent=2)[:2000])
else:
    print(r2.text[:300])
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/_test_new_api.py', 'w') as f:
    f.write(script)
sftp.close()

out, err = run('python3 /tmp/_test_new_api.py')
print(out[:4000])

ssh.close()
