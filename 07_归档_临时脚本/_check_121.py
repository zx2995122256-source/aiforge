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

script = """import sqlite3
conn = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
cur = conn.cursor()
rows = cur.execute('SELECT id, task_type, status, reference_images, reference_video, substr(prompt,1,60) FROM tasks WHERE id >= 121 ORDER BY id DESC').fetchall()
for r in rows:
    ri = r[3] if r[3] else '(empty)'
    rv = r[4] if r[4] else '(empty)'
    print(f'#{r[0]} {r[1]} {r[2]}')
    print(f'  ref_imgs={ri[:120]}')
    print(f'  ref_vid={rv[:120]}')
    print(f'  prompt={r[5]}')
conn.close()
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/_check_121.py', 'w') as f:
    f.write(script)
sftp.close()

out, err = run('python3 /tmp/_check_121.py')
print(out)

ssh.close()
