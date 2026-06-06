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

script = """import sqlite3, json, sys
sys.path.insert(0, '/home/ubuntu/aiforge/backend')
from models.db import create_task, _get_conn

tid = create_task(2, 'image', 'GPT-Image2', 'test prompt with refs', 10, 999, 
                  reference_images='["http://example.com/img1.png"]', 
                  reference_video='http://example.com/vid1.mp4')
print(f'Created test task #{tid}')

conn = _get_conn()
row = conn.execute('SELECT reference_images, reference_video FROM tasks WHERE id=?', (tid,)).fetchone()
print(f'ref_imgs=[{row[0]}]')
print(f'ref_vid=[{row[1]}]')

# Also check what dict(row) returns
row2 = conn.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone()
d = dict(row2)
print(f'dict keys: {list(d.keys())}')
print(f'dict ref_imgs: {d.get("reference_images","MISSING")}')
print(f'dict ref_vid: {d.get("reference_video","MISSING")}')

conn.execute('DELETE FROM tasks WHERE id=?', (tid,))
conn.commit()
conn.close()
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/_test_create2.py', 'w') as f:
    f.write(script)
sftp.close()

out, err = run('python3 /tmp/_test_create2.py')
print(out)
if err:
    print(f'ERR: {err[:500]}')

ssh.close()
