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

# Check recent engine logs for task 408
out, _ = run('grep -E "Task #40[5-9]|Task #41" /tmp/oiioii.log | grep -v "GET /api" | tail -30')
print('=== Task 408 logs ===')
print(out[:3000])

# Check if task 408 is still processing or stuck
script = """import sqlite3, time
conn = sqlite3.connect('/home/ubuntu/oiioii/data/oiioii_pool.db')
cur = conn.cursor()
r = cur.execute('SELECT id, status, task_id, created_at, completed_at FROM tasks WHERE id=408').fetchone()
if r:
    elapsed = time.time() - r[3] if r[3] else 0
    print(f'Task #{r[0]}: status={r[1]} task_id={r[2]} elapsed={int(elapsed)}s')
conn.close()
"""
sftp = ssh.open_sftp()
with sftp.open('/tmp/_check_408.py', 'w') as f:
    f.write(script)
sftp.close()

out, _ = run('python3 /tmp/_check_408.py')
print(f'\n=== Task 408 status ===')
print(out)

# Also check the full recent log (non-polling)
out, _ = run('cat /tmp/oiioii.log | grep -v "GET /api/task" | tail -40')
print('\n=== Recent non-polling logs ===')
print(out[:3000])

ssh.close()
