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
conv_id = 'af3eb38f-df4e-4e30-83f6-6f754dbbaabc'

# Try conversation-related endpoints
endpoints = [
    ('/conversation/detail', {"data": {"conversationId": conv_id, "workspaceId": ws_id}}),
    ('/conversation/list', {"data": {"workspaceId": ws_id}}),
    ('/conversation/messages', {"data": {"conversationId": conv_id}}),
    ('/conversation/sync', {"data": {"conversationId": conv_id, "workspaceId": ws_id}}),
    ('/media/conversation/list', {"data": {"workspaceId": ws_id}}),
    ('/media/canvas_async_tasks', {"data": {"workspaceId": ws_id}}),
    ('/media/video_generate/status', {"data": {"taskId": "video_generate_1780362503559_qibpiv9"}}),
    ('/media/video_generate/result', {"data": {"taskId": "video_generate_1780362503559_qibpiv9"}}),
    ('/media/task/status', {"data": {"taskId": "video_generate_1780362503559_qibpiv9"}}),
    ('/task/status', {"data": {"taskId": "video_generate_1780362503559_qibpiv9"}}),
    ('/media/batch_gen/status', {"data": {"taskId": "video_generate_1780362503559_qibpiv9"}}),
]

for path, body in endpoints:
    try:
        r = requests.post(f'{API}{path}', json=body, headers=headers, timeout=10)
        status = r.status_code
        text = r.text[:150].replace('\\n', ' ')
        print(f'{path}: {status} -> {text}')
    except Exception as e:
        print(f'{path}: ERROR {e}')
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/_explore_api.py', 'w') as f:
    f.write(script)
sftp.close()

out, err = run('python3 /tmp/_explore_api.py')
print(out[:3000])

ssh.close()
