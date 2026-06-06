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

# Verify the running code has the fix
out, _ = run('grep "uploaded_refs" /home/ubuntu/oiioii/core/engine.py | head -5')
print('=== uploaded_refs references in engine.py ===')
print(out)

# Check the specific line that was buggy
out, _ = run('grep -n "skip_uris.*known.*claimed" /home/ubuntu/oiioii/core/engine.py')
print('\n=== Fixed print line ===')
print(out)

# Check task 405 status
out, _ = run('sqlite3 /home/ubuntu/oiioii/data/oiioii_pool.db "SELECT id, status, error_message FROM tasks WHERE id=405" 2>/dev/null')
print('\n=== Task 405 status ===')
print(out)

# Check if there are other stuck tasks
out, _ = run('sqlite3 /home/ubuntu/oiioii/data/oiioii_pool.db "SELECT id, status, task_type, datetime(created_at, \'unixepoch\') FROM tasks WHERE status=\'processing\' ORDER BY id DESC LIMIT 10" 2>/dev/null')
print('\n=== Stuck processing tasks ===')
print(out or 'NONE')

ssh.close()
