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

# Check recent tasks in OiioiiPool
out, _ = run('sqlite3 /home/ubuntu/oiioii/data/oiioii_pool.db "SELECT id, task_type, status, account_id, model_name, substr(prompt,1,60), substr(task_id,1,40), substr(error_message,1,80), datetime(created_at, \'unixepoch\'), datetime(finished_at, \'unixepoch\') FROM tasks ORDER BY id DESC LIMIT 15" 2>/dev/null')
print('=== OiioiiPool recent tasks ===')
print(out)

# Check AiForge tasks
out, _ = run('sqlite3 /home/ubuntu/aiforge/backend/data/aiforge.db "SELECT id, user_id, task_type, status, model_name, substr(prompt,1,60), substr(error,1,80), datetime(created_at, \'unixepoch\'), datetime(finished_at, \'unixepoch\') FROM tasks ORDER BY id DESC LIMIT 15" 2>/dev/null')
print('\n=== AiForge recent tasks ===')
print(out)

# Check recent engine logs
out, _ = run('grep -E "Engine|Client|poll|Task #|submit|timeout|failed|exception|completed|manualRefresh|skip_uri" /tmp/oiioii.log | tail -50')
print('\n=== Recent engine logs ===')
print(out[:3000])

ssh.close()
