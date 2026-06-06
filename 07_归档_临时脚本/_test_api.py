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

# Check what the API actually returns for tasks - get a token first
script = """import requests, json

# Login
r = requests.post('http://localhost:7862/api/auth/login', json={'email':'test@test.com','password':'test123'})
data = r.json()
token = data.get('token','')
if not token:
    print('Login failed:', data)
    exit()

# Get tasks
r = requests.get('http://localhost:7862/api/generate/tasks', headers={'Authorization': f'Bearer {token}'})
tasks = r.json().get('tasks', [])
for t in tasks[-5:]:
    print(f'#{t.get("id")} type={t.get("task_type")} status={t.get("status")}')
    print(f'  ref_imgs={json.dumps(t.get("reference_images",""), ensure_ascii=False)[:120]}')
    print(f'  ref_vid={json.dumps(t.get("reference_video",""), ensure_ascii=False)[:120]}')
    print(f'  prompt={t.get("prompt","")[:60]}')
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/_test_api.py', 'w') as f:
    f.write(script)
sftp.close()

out, err = run('python3 /tmp/_test_api.py')
print('=== API task data ===')
print(out)
if err:
    print(f'ERR: {err[:300]}')

ssh.close()
