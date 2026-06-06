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

# Find all .db files
out, _ = run('find /home/ubuntu -name "*.db" 2>/dev/null')
print('=== All .db files ===')
print(out)

# Check the OiioiiPool DB path from config
out, _ = run('grep -r "DB_PATH" /home/ubuntu/oiioii/config.py 2>/dev/null')
print('\n=== OiioiiPool DB_PATH config ===')
print(out)

# Check the AiForge DB path from config
out, _ = run('grep -r "DB_PATH" /home/ubuntu/aiforge/backend/config.py 2>/dev/null')
print('\n=== AiForge DB_PATH config ===')
print(out)

# Try the actual DB files
out, _ = run('sqlite3 /home/ubuntu/oiioii/data/oiioii_pool.db ".tables" 2>&1')
print('\n=== oiioii_pool.db tables ===')
print(out)

# Try listing data dir
out, _ = run('ls -la /home/ubuntu/oiioii/data/')
print('\n=== oiioii data dir ===')
print(out)

out, _ = run('ls -la /home/ubuntu/aiforge/backend/data/')
print('\n=== aiforge data dir ===')
print(out)

# Try direct query with error output
out, err = run('sqlite3 /home/ubuntu/aiforge/backend/data/aiforge.db "SELECT count(*) FROM tasks" 2>&1')
print(f'\n=== AiForge task count: {out} err={err} ===')

out, err = run('sqlite3 /home/ubuntu/oiioii/data/oiioii_pool.db "SELECT count(*) FROM tasks" 2>&1')
print(f'\n=== OiioiiPool task count: {out} err={err} ===')

# Check what the running process has open
out, _ = run('sudo ls -la /proc/528215/fd/ 2>/dev/null | grep db | head -5')
print(f'\n=== Open DB files for PID 528215 ===')
print(out)

ssh.close()
