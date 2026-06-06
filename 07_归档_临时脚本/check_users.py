import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

sftp = client.open_sftp()
with sftp.file('/tmp/chpass3.py', 'w') as f:
    f.write("""
import sqlite3, bcrypt
c = sqlite3.connect("/home/ubuntu/aiforge/backend/data/aiforge.db")
print("=== Current users ===")
for row in c.execute("SELECT id, email, role, is_admin FROM users"):
    print(row)
c.close()
""")
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/chpass3.py', timeout=10)
print(stdout.read().decode()[:500])
print("ERR:", stderr.read().decode()[:200])

client.close()