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

# Mark task 408 as failed (polling thread was lost on restart)
script = """import sqlite3
conn = sqlite3.connect('/home/ubuntu/oiioii/data/oiioii_pool.db')
cur = conn.cursor()
cur.execute("UPDATE tasks SET status='failed', error_message='Service restarted, polling thread lost' WHERE id=408 AND status='processing'")
conn.commit()
print(f'Updated {cur.rowcount} row(s)')
conn.close()
"""
sftp = ssh.open_sftp()
with sftp.open('/tmp/_fix_408.py', 'w') as f:
    f.write(script)
sftp.close()

out, _ = run('python3 /tmp/_fix_408.py')
print(f'Task 408: {out}')

# Also fix AiForge task 120 and 117 (stuck in running)
script2 = """import sqlite3
conn = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
cur = conn.cursor()
cur.execute("UPDATE tasks SET status='failed' WHERE status='running' AND id IN (117, 120)")
conn.commit()
print(f'Updated {cur.rowcount} AiForge row(s)')
conn.close()
"""
with sftp.open('/tmp/_fix_aiforge.py', 'w') as f:
    f.write(script2)
sftp.close()

out, _ = run('python3 /tmp/_fix_aiforge.py')
print(f'AiForge stuck tasks: {out}')

# Also refund points for task 408
script3 = """import sqlite3
conn = sqlite3.connect('/home/ubuntu/oiioii/data/oiioii_pool.db')
cur = conn.cursor()
r = cur.execute('SELECT account_id, points_cost FROM tasks WHERE id=408').fetchone()
if r:
    print(f'Account #{r[0]} cost={r[1]}')
    cur.execute('UPDATE accounts SET points = points + ? WHERE id = ?', (r[1], r[0]))
    conn.commit()
    print('Refunded')
conn.close()
"""
with sftp.open('/tmp/_refund_408.py', 'w') as f:
    f.write(script3)
sftp.close()

out, _ = run('python3 /tmp/_refund_408.py')
print(f'Refund: {out}')

ssh.close()
