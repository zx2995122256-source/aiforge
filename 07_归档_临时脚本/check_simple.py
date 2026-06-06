import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

script = r'''
import sqlite3, time

print("=== AiForge tasks ===")
conn = sqlite3.connect("/home/ubuntu/aiforge/backend/data/aiforge.db")
rows = conn.execute("SELECT id, task_type, status, oiioii_task_id, prompt, result_url FROM tasks WHERE user_id=1 ORDER BY id DESC LIMIT 10").fetchall()
for r in rows:
    has_result = "✅有结果" if r[5] else "❌无结果"
    print(f"  #{r[0]} {r[1]:5} {r[2]:10} oid={r[3]} {has_result} | {r[4][:40]}")
conn.close()

print("\n=== OiioiiPool processing ===")
conn2 = sqlite3.connect("/home/ubuntu/oiioii/data/oiioii_pool.db")
rows2 = conn2.execute("SELECT id, task_type, status, prompt FROM tasks WHERE status IN ('processing','pending','running') ORDER BY id DESC LIMIT 10").fetchall()
for r in rows2:
    print(f"  #{r[0]} {r[1]:5} {r[2]:10} | {r[3][:40]}")
conn2.close()
'''

sftp = client.open_sftp()
with sftp.file('/tmp/check_simple.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/check_simple.py', timeout=15)
print(stdout.read().decode()[:1500])

client.close()