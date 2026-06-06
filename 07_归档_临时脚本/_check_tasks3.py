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

# Use Python to query DB
py_cmd = '''
import sqlite3
conn = sqlite3.connect("/home/ubuntu/oiioii/data/oiioii_pool.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()
# Get recent tasks
rows = cur.execute("SELECT id, task_type, status, account_id, model_name, substr(prompt,1,80), substr(task_id,1,50), substr(error_message,1,100), created_at, finished_at FROM tasks ORDER BY id DESC LIMIT 15").fetchall()
for r in rows:
    print(f"#{r[0]} type={r[1]} status={r[2]} acct=#{r[3]} model={r[4]}")
    print(f"  prompt={r[5]}")
    print(f"  task_id={r[6]} err={r[7]}")
    import time
    ct = time.strftime('%m-%d %H:%M', time.localtime(r[8])) if r[8] else '-'
    ft = time.strftime('%m-%d %H:%M', time.localtime(r[9])) if r[9] else '-'
    print(f"  created={ct} finished={ft}")
    print()
conn.close()
'''

out, err = run(f'python3 -c {repr(py_cmd)}')
print('=== OiioiiPool recent tasks ===')
print(out or err)

# Also check AiForge tasks
py_cmd2 = '''
import sqlite3
conn = sqlite3.connect("/home/ubuntu/aiforge/backend/data/aiforge.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()
rows = cur.execute("SELECT id, user_id, task_type, status, model_name, substr(prompt,1,80), substr(error,1,100), created_at, finished_at FROM tasks ORDER BY id DESC LIMIT 15").fetchall()
for r in rows:
    print(f"#{r[0]} user=#{r[1]} type={r[2]} status={r[3]} model={r[4]}")
    print(f"  prompt={r[5]}")
    print(f"  err={r[6]}")
    import time
    ct = time.strftime('%m-%d %H:%M', time.localtime(r[7])) if r[7] else '-'
    ft = time.strftime('%m-%d %H:%M', time.localtime(r[8])) if r[8] else '-'
    print(f"  created={ct} finished={ft}")
    print()
conn.close()
'''

out2, err2 = run(f'python3 -c {repr(py_cmd2)}')
print('\n=== AiForge recent tasks ===')
print(out2 or err2)

ssh.close()
