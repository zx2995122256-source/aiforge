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

script = """import sqlite3, json
conn = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
cur = conn.cursor()
rows = cur.execute('SELECT id, task_type, status, reference_images, reference_video, substr(prompt,1,60) FROM tasks ORDER BY id DESC LIMIT 15').fetchall()
for r in rows:
    ri = r[3] if r[3] else ''
    rv = r[4] if r[4] else ''
    print(f'#{r[0]} {r[1]} {r[2]} ref_imgs=[{ri[:100]}] ref_vid=[{rv[:100]}] prompt={r[5]}')
conn.close()
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/_check_new.py', 'w') as f:
    f.write(script)
sftp.close()

out, err = run('python3 /tmp/_check_new.py')
print(out)

ssh.close()
