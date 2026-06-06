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

# Find DB files
out, _ = run('find /home/ubuntu/oiioii -name "*.db" -o -name "*.sqlite" 2>/dev/null')
print('=== DB files ===')
print(out)

# Check config for DB path
out, _ = run('grep -i "db\|database\|sqlite" /home/ubuntu/oiioii/config.py')
print('\n=== Config DB settings ===')
print(out)

# Check the actual running process's DB
out, _ = run('sudo ls -la /proc/528215/fd/ 2>/dev/null | grep -i "db\|sqlite" | head -5')
print('\n=== Open DB files ===')
print(out)

ssh.close()
