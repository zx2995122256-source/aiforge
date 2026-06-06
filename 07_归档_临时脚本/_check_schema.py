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

# First get the schema
script = """import sqlite3

print('=== OiioiiPool tasks schema ===')
conn = sqlite3.connect('/home/ubuntu/oiioii/data/oiioii_pool.db')
cur = conn.cursor()
schema = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks'").fetchone()
print(schema[0] if schema else 'NO TABLE')
conn.close()

print()
print('=== AiForge tasks schema ===')
conn = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
cur = conn.cursor()
schema = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks'").fetchone()
print(schema[0] if schema else 'NO TABLE')
conn.close()
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/_query_schema.py', 'w') as f:
    f.write(script)
sftp.close()

out, err = run('python3 /tmp/_query_schema.py')
print(out)
if err:
    print(f'ERR: {err[:300]}')

ssh.close()
