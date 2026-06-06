import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check OiioiiPool DB schema
stdin, stdout, stderr = client.exec_command('''python3 -c "
import sqlite3
c = sqlite3.connect('/home/ubuntu/oiioii/data/oiioii_pool.db')
# Get schema
tables = c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
for t in tables:
    print(f'Table: {t[0]}')
    cols = c.execute(f'PRAGMA table_info({t[0]})').fetchall()
    for col in cols:
        print(f'  - {col[1]} ({col[2]})')
c.close()
" ''')
print(stdout.read().decode()[:1000])

# Check output files list
stdin, stdout, stderr = client.exec_command('ls -la /home/ubuntu/oiioii/data/output/2026-06-01/ | tail -15')
print("\n=== OUTPUT FILES ===")
print(stdout.read().decode()[:800])

# Check OiioiiPool API for task 275
stdin, stdout, stderr = client.exec_command('curl -s http://127.0.0.1:7861/api/task/275 2>/dev/null | head -c 500')
print("\n=== TASK 275 ===")
print(stdout.read().decode()[:500])

client.close()