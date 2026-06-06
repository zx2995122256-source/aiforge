import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

sftp = client.open_sftp()
with sftp.file('/tmp/check.py', 'w') as f:
    f.write('import sqlite3\nc = sqlite3.connect("/home/ubuntu/aiforge/backend/data/aiforge.db")\nr = c.execute("SELECT id, email, role FROM users")\nfor row in r:\n    print(row)\nc.close()\n')
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/check.py')
print("USERS:", stdout.read().decode())
print("ERR:", stderr.read().decode())

client.close()
