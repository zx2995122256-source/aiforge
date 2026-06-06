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

# Check the actual app log file
out, _ = run('ls -la /home/ubuntu/oiioii/logs/ 2>/dev/null')
print('=== Log files ===')
print(out or 'NO LOGS DIR')

out, _ = run('tail -200 /home/ubuntu/oiioii/logs/app.log 2>/dev/null || echo NO_APP_LOG')
print('\n=== app.log last 200 ===')
print(out[:5000])

# Also check the DB for task 405
out, _ = run('sqlite3 /home/ubuntu/oiioii/data/pool.db "SELECT id, task_type, status, account_id, task_id, error_message, created_at, finished_at FROM tasks WHERE id=405" 2>/dev/null')
print('\n=== Task 405 in DB ===')
print(out)

# Check recent tasks
out, _ = run('sqlite3 /home/ubuntu/oiioii/data/pool.db "SELECT id, task_type, status, account_id, substr(task_id,1,40), substr(error_message,1,60), datetime(created_at, \'unixepoch\'), datetime(finished_at, \'unixepoch\') FROM tasks ORDER BY id DESC LIMIT 10" 2>/dev/null')
print('\n=== Recent tasks ===')
print(out)

ssh.close()
