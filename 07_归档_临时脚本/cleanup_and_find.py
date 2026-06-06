import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# 1. Find reference videos on disk
stdin, stdout, stderr = client.exec_command('ls -lah /home/ubuntu/oiioii/data/output/refs/ 2>/dev/null | grep -v "^d" | tail -10', timeout=10)
print("=== Reference videos ===")
print(stdout.read().decode()[:500])

# 2. Delete ALL AiForge tasks for user_id=1 (just the DB entries)
stdin, stdout, stderr = client.exec_command(
    '''python3 -c "
import sqlite3
conn = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
cnt = conn.execute('SELECT COUNT(*) FROM tasks WHERE user_id=1').fetchone()[0]
print(f'Found {cnt} tasks for user_id=1')
conn.execute('DELETE FROM tasks WHERE user_id=1')
conn.commit()
conn.close()
print('Deleted all')
" ''',
    timeout=10
)
print(stdout.read().decode()[:200])

# 3. Verify
stdin, stdout, stderr = client.exec_command(
    '''python3 -c "
import sqlite3
conn = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
cnt = conn.execute('SELECT COUNT(*) FROM tasks WHERE user_id=1').fetchone()[0]
print(f'Remaining: {cnt}')
conn.close()
" ''',
    timeout=10
)
print(stdout.read().decode()[:100])

client.close()