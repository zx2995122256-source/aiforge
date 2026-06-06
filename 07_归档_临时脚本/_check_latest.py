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

# Check recent tasks in AiForge DB
script = """import sqlite3, time
conn = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
cur = conn.cursor()
rows = cur.execute('SELECT id, task_type, status, model, substr(prompt,1,60), oiioii_task_id, substr(result_url,1,80), datetime(created_at, "unixepoch","localtime"), datetime(finished_at, "unixepoch","localtime") FROM tasks ORDER BY id DESC LIMIT 5').fetchall()
for r in rows:
    elapsed = int(time.time() - r[7].timestamp()) if r[7] else 0
    print(f'#{r[0]} {r[1]} {r[2]} model={r[3]}')
    print(f'  prompt={r[4]}')
    print(f'  oiioii_id={r[5]} result={r[6]}')
    print(f'  created={r[7]} finished={r[8]}')
conn.close()
"""
sftp = ssh.open_sftp()
with sftp.open('/tmp/_check_latest.py', 'w') as f:
    f.write(script)
sftp.close()

out, err = run('python3 /tmp/_check_latest.py')
print('=== AiForge latest tasks ===')
print(out)

# Check OiioiiPool tasks
script2 = """import sqlite3, time
conn = sqlite3.connect('/home/ubuntu/oiioii/data/oiioii_pool.db')
cur = conn.cursor()
rows = cur.execute('SELECT id, task_type, status, account_id, model_name, substr(prompt,1,60), substr(task_id,1,50), substr(error_message,1,100), datetime(created_at, "unixepoch","localtime") FROM tasks ORDER BY id DESC LIMIT 5').fetchall()
for r in rows:
    print(f'#{r[0]} {r[1]} {r[2]} acct=#{r[3]} model={r[4]}')
    print(f'  prompt={r[5]}')
    print(f'  task_id={r[6]} err={r[7]}')
    print(f'  created={r[8]}')
conn.close()
"""
with sftp.open('/tmp/_check_pool.py', 'w') as f:
    f.write(script2)
sftp.close()

out2, err2 = run('python3 /tmp/_check_pool.py')
print('\n=== OiioiiPool latest tasks ===')
print(out2)

# Check OiioiiPool logs
out3, _ = run('cat /tmp/oiioii.log | grep -v "GET /api/task" | tail -30')
print('\n=== OiioiiPool recent logs ===')
print(out3[:2000])

# Check AiForge service log
out4, _ = run('sudo journalctl -u aiforge --since "3 min ago" --no-pager | grep -v "GET /api/gen/task" | tail -20')
print('\n=== AiForge recent logs ===')
print(out4[:1500])

ssh.close()
