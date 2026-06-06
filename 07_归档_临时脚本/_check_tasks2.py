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

# Check DB tables
out, _ = run('sqlite3 /home/ubuntu/oiioii/data/oiioii_pool.db ".tables"')
print('=== OiioiiPool tables ===')
print(out)

out, _ = run('sqlite3 /home/ubuntu/aiforge/backend/data/aiforge.db ".tables"')
print('\n=== AiForge tables ===')
print(out)

# Check schema
out, _ = run('sqlite3 /home/ubuntu/oiioii/data/oiioii_pool.db ".schema tasks" 2>/dev/null')
print('\n=== OiioiiPool tasks schema ===')
print(out)

out, _ = run('sqlite3 /home/ubuntu/aiforge/backend/data/aiforge.db ".schema tasks" 2>/dev/null')
print('\n=== AiForge tasks schema ===')
print(out)

# Try with correct column names
out, _ = run('sqlite3 /home/ubuntu/oiioii/data/oiioii_pool.db "SELECT * FROM tasks ORDER BY rowid DESC LIMIT 3" 2>/dev/null')
print('\n=== OiioiiPool tasks (raw) ===')
print(out[:2000])

out, _ = run('sqlite3 /home/ubuntu/aiforge/backend/data/aiforge.db "SELECT * FROM tasks ORDER BY rowid DESC LIMIT 3" 2>/dev/null')
print('\n=== AiForge tasks (raw) ===')
print(out[:2000])

# Also check recent logs
out, _ = run('cat /tmp/oiioii.log | grep -v "GET /api/task" | tail -30')
print('\n=== OiioiiPool log (no polling) ===')
print(out[:2000])

ssh.close()
