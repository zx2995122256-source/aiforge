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

script = """import sqlite3, time

print('=== OiioiiPool recent tasks ===')
conn = sqlite3.connect('/home/ubuntu/oiioii/data/oiioii_pool.db')
cur = conn.cursor()
rows = cur.execute('SELECT id, task_type, status, account_id, model_name, substr(prompt,1,80), substr(task_id,1,50), substr(error_message,1,100), created_at, completed_at, ref_image_urls FROM tasks ORDER BY id DESC LIMIT 15').fetchall()
for r in rows:
    ct = time.strftime('%m-%d %H:%M', time.localtime(r[8])) if r[8] else '-'
    ft = time.strftime('%m-%d %H:%M', time.localtime(r[9])) if r[9] else '-'
    refs = r[10][:60] if r[10] else ''
    print(f'#{r[0]} type={r[1]} status={r[2]} acct=#{r[3]} model={r[4]}')
    print(f'  prompt={r[5]}')
    print(f'  task_id={r[6]} err={r[7]}')
    print(f'  created={ct} completed={ft} refs={refs}')
conn.close()

print()
print('=== AiForge recent tasks ===')
conn = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
cur = conn.cursor()
rows = cur.execute('SELECT id, user_id, task_type, status, model, substr(prompt,1,80), substr(result_url,1,80), oiioii_task_id, created_at, finished_at FROM tasks ORDER BY id DESC LIMIT 15').fetchall()
for r in rows:
    ct = time.strftime('%m-%d %H:%M', time.localtime(r[8])) if r[8] else '-'
    ft = time.strftime('%m-%d %H:%M', time.localtime(r[9])) if r[9] else '-'
    print(f'#{r[0]} user=#{r[1]} type={r[2]} status={r[3]} model={r[4]}')
    print(f'  prompt={r[5]}')
    print(f'  result={r[6]} oiioii_id={r[7]}')
    print(f'  created={ct} finished={ft}')
conn.close()
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/_query_tasks2.py', 'w') as f:
    f.write(script)
sftp.close()

out, err = run('python3 /tmp/_query_tasks2.py')
print(out)
if err:
    print(f'ERR: {err[:300]}')

ssh.close()
