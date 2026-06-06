#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', password='zx4579561.', timeout=15)

def run(cmd, timeout=10):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        return stdout.read().decode().strip(), stderr.read().decode().strip()
    except:
        return '(timeout)', ''

# Check models/db.py for _get_conn
out, _ = run('grep -n "_get_conn" /home/ubuntu/aiforge/backend/models/db.py')
print('=== _get_conn in db.py ===')
print(out or 'NOT FOUND')

# Check full AiForge main.py
out, _ = run('cat /home/ubuntu/aiforge/backend/main.py')
print('\n=== Full main.py ===')
print(out)

# Check admin.py on server
out, _ = run('head -50 /home/ubuntu/aiforge/backend/admin.py 2>/dev/null || echo NO_ADMIN')
print('\n=== Server admin.py ===')
print(out)

# Check if admin is mounted in main app
out, _ = run('grep -n "admin" /home/ubuntu/aiforge/backend/main.py')
print('\n=== admin references in main.py ===')
print(out or 'NONE')

# Check models dir
out, _ = run('ls -la /home/ubuntu/aiforge/backend/models/')
print('\n=== models dir ===')
print(out)

# Check current payment.py fully
out, _ = run('cat /home/ubuntu/aiforge/backend/api/payment.py')
print('\n=== Current server payment.py ===')
print(out)

ssh.close()
