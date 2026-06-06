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

# Check the full oiioii.log with grep for Engine/Client/poll
out, _ = run('grep -E "Engine|Client|poll|skip_uri|Task #|generate|timeout|failed|error" /tmp/oiioii.log | tail -100')
print('=== Engine/Client logs ===')
print(out[:5000])

# Check AiForge task DB
out, _ = run('sqlite3 /home/ubuntu/aiforge/backend/data/aiforge.db "SELECT id, user_id, task_type, status, substr(task_id,1,50), substr(error,1,80), datetime(created_at, \'unixepoch\'), datetime(finished_at, \'unixepoch\') FROM tasks ORDER BY id DESC LIMIT 10" 2>/dev/null')
print('\n=== AiForge recent tasks ===')
print(out)

# Check task 405 specifically in AiForge DB
out, _ = run('sqlite3 /home/ubuntu/aiforge/backend/data/aiforge.db "SELECT * FROM tasks WHERE id=405" 2>/dev/null')
print('\n=== AiForge task 405 ===')
print(out)

# Check OiioiiPool tasks DB
out, _ = run('find /home/ubuntu/oiioii -name "*.db" 2>/dev/null')
print('\n=== DB files ===')
print(out)

out, _ = run('sqlite3 /home/ubuntu/oiioii/data/pool.db ".tables" 2>/dev/null')
print('\n=== OiioiiPool DB tables ===')
print(out)

out, _ = run('sqlite3 /home/ubuntu/oiioii/data/pool.db "SELECT id, task_type, status, account_id, substr(task_id,1,50), substr(error_message,1,80), datetime(created_at, \'unixepoch\') FROM tasks ORDER BY id DESC LIMIT 10" 2>/dev/null')
print('\n=== OiioiiPool recent tasks ===')
print(out)

ssh.close()
