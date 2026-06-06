import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

stdin, stdout, stderr = client.exec_command('''python3 -c "
import sqlite3
c = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
# Get all tasks with their oiioii_task_ids
rows = c.execute('SELECT id, oiioii_task_id, task_type, model, status FROM tasks ORDER BY id DESC LIMIT 10').fetchall()
for r in rows:
    print(f'AiForgeTask {r[0]}: oiioii_id={r[1]}, type={r[2]}, model={r[3]}, status={r[4]}')
c.close()
" ''')
print(stdout.read().decode()[:1000])

client.close()