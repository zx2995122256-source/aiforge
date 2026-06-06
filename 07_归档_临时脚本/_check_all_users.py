import paramiko

key = paramiko.RSAKey.from_private_key_file(
    r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=10)

# Write script to server
sftp = client.open_sftp()
script = """import sqlite3
c = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
c.row_factory = sqlite3.Row

print('=== 所有用户 ===')
for r in c.execute('SELECT * FROM users').fetchall():
    print(dict(r))

print('\\n=== point_logs 全部 ===')
for r in c.execute('SELECT * FROM point_logs').fetchall():
    print(dict(r))

print('\\n=== tasks 全部 ===')
for r in c.execute('SELECT * FROM tasks ORDER BY id DESC').fetchall():
    print(dict(r))

c.close()
"""

with sftp.file('/tmp/dump_db.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/dump_db.py', timeout=15)
out = stdout.read().decode()
err = stderr.read().decode()
print(out)
if err:
    print(f"ERR: {err[:500]}")
client.close()