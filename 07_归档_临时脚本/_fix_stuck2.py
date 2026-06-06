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

# Fix AiForge stuck tasks
script = """import sqlite3
conn = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
cur = conn.cursor()
cur.execute("UPDATE tasks SET status='failed' WHERE status='running'")
conn.commit()
print(f'Updated {cur.rowcount} row(s)')
conn.close()
"""
sftp = ssh.open_sftp()
with sftp.open('/tmp/_fix_af.py', 'w') as f:
    f.write(script)
sftp.close()

out, _ = run('python3 /tmp/_fix_af.py')
print(f'AiForge stuck tasks fixed: {out}')

ssh.close()
