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

# Test the Oiioii API directly - check assetList
script = """
import requests, json

token = 'eyJhbGciOiJIUzI1NiIsImtpZCI6IlRxTGhKT0JtWi81K0txRkYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3VndnV6ZXN0eXlwYm1jZnVycmJkLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIzZTY5M2NlZS1lMjllLTRiMDQtOTczOS1iNTYwYWNmYzFmZWEiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzgwOTU2ODc3LCJpYXQiOjE3ODAzNTIwNzcsImVtYWlsIjoib2lpb19mdmk5ZGF4c3Q4YWxAd3NodS5uZXQiLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJsYW5ndWFnZSI6InpoIiwibmlja25hbWUiOiJvaWlvX2Z2aTlkYXhzdDhhbCJ9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzgwMzUyMDc3fV0sInNlc3Npb25faWQiOiI5YmJhMDA5NS05Yzg0LTQwZWUtYmUwYS00NDU0MzI4ODVkNjciLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.n1D9-XE1n8Hgy1tPRR7hbZhbkxYHPmRfmOUANZIUu28'
ws_id = 'ea60835a-b42e-4300-9fca-f1562b675a09'

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Get asset list
r = requests.get(f'https://ugvuzestyypbmcfurrbd.supabase.co/functions/v1/assetList?workspaceId={ws_id}', headers=headers, timeout=15)
print(f'assetList status: {r.status_code}')
data = r.json()
print(f'assetList response: {json.dumps(data, ensure_ascii=False)[:500]}')

# Count assets by type
if isinstance(data, list):
    videos = [a for a in data if a.get('type') == 'video']
    images = [a for a in data if a.get('type') == 'image']
    print(f'Total assets: {len(data)} videos={len(videos)} images={len(images)}')
    for v in videos[-3:]:
        print(f'  video: uri={v.get("uri","")[:60]} created={v.get("createdAt","")}')
elif isinstance(data, dict):
    assets = data.get('assets', data.get('data', []))
    print(f'Assets in response: {len(assets)}')
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/_test_api.py', 'w') as f:
    f.write(script)
sftp.close()

out, err = run('python3 /tmp/_test_api.py')
print(out[:2000])
if err:
    print(f'ERR: {err[:500]}')

ssh.close()
