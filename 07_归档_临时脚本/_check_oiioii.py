#!/usr/bin/env python3
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', password='zx4579561.', timeout=15)

def run(cmd, timeout=15):
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        return stdout.read().decode().strip(), stderr.read().decode().strip()
    except:
        return '(timeout)', ''

# Check current process
out, _ = run('ps aux | grep "python3 main" | grep -v grep')
print('=== Processes ===')
print(out or 'NONE')

# Check port
out, _ = run('sudo lsof -i :7861 2>/dev/null | head -3')
print('\n=== Port 7861 ===')
print(out or 'NOT LISTENING')

# Try API with longer timeout
out, _ = run('curl -s --connect-timeout 10 --max-time 15 http://localhost:7861/api/pool/status 2>&1 | head -200')
print('\n=== API response ===')
print(out[:500])

# Check fresh log
out, _ = run('cat /tmp/oiioii.log | tail -30')
print('\n=== Log tail ===')
print(out)

ssh.close()
