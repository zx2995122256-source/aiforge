import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

sftp = client.open_sftp()
with sftp.file('/tmp/chpass4.py', 'w') as f:
    f.write("""
import sqlite3, bcrypt
c = sqlite3.connect("/home/ubuntu/aiforge/backend/data/aiforge.db")
print("=== Schema ===")
for row in c.execute("PRAGMA table_info(users)"):
    print(row)
print("=== Users ===")
for row in c.execute("SELECT id, email, nickname, role, points FROM users"):
    print(row)
c.close()
""")
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/chpass4.py', timeout=10)
print(stdout.read().decode()[:1000])
print("ERR:", stderr.read().decode()[:200])

client.close()