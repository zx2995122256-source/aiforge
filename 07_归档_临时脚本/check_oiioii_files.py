import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check OiioiiPool task output_files mapping
stdin, stdout, stderr = client.exec_command('''python3 -c "
import sqlite3, json
c = sqlite3.connect('/home/ubuntu/oiioii/data/oiioii_pool.db')
# Get tasks with their output files
rows = c.execute('SELECT id, oiioii_task_id, output_files, task_type, model FROM tasks WHERE output_files IS NOT NULL AND output_files != \\\"\\\" ORDER BY id DESC LIMIT 15').fetchall()
for r in rows:
    out = str(r[2] or '')[:100]
    print(f'PoolTask {r[0]}: oiioii_id={r[1]}, type={r[3]}, files={out}')
c.close()
" ''')
print("=== OIIOII POOL TASKS ===")
print(stdout.read().decode()[:1500])

# Also check the OiioiiPool's /api/task/{id}/download endpoint
stdin, stdout, stderr = client.exec_command(
    'curl -s -D - http://127.0.0.1:7861/api/task/275/download 2>&1 | head -20', timeout=10
)
print("\n=== DOWNLOAD HEADERS ===")
print(stdout.read().decode()[:500])

client.close()