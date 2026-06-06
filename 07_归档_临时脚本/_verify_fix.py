#!/usr/bin/env python3
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', password='zx4579561.', timeout=15)

def run(cmd, timeout=10):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        return stdout.read().decode().strip(), stderr.read().decode().strip()
    except:
        return '(timeout)', ''

# Check all python processes
out, _ = run('ps aux | grep python | grep -v grep')
print('=== Python processes ===')
print(out)

# Check port 7861
out, _ = run('sudo lsof -i :7861 2>/dev/null | head -5')
print('\n=== Port 7861 ===')
print(out)

# Test the API
out, _ = run('curl -s http://localhost:7861/api/pool/status | head -200')
print('\n=== API test ===')
print(out[:500])

ssh.close()
