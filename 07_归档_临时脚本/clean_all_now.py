import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=15)

script = r'''
import sqlite3

# 1. Delete all AiForge tasks
conn = sqlite3.connect("/home/ubuntu/aiforge/backend/data/aiforge.db")
cnt1 = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
conn.execute("DELETE FROM tasks")
conn.commit()
conn.close()
print(f"AiForge: 删除了 {cnt1} 个任务")

# 2. Delete processing OiioiiPool tasks
conn2 = sqlite3.connect("/home/ubuntu/oiioii/data/oiioii_pool.db")
cnt2 = conn2.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('processing','pending','running')").fetchone()[0]
conn2.execute("DELETE FROM tasks WHERE status IN ('processing','pending','running')")
conn2.commit()
conn2.close()
print(f"OiioiiPool: 删除了 {cnt2} 个处理中的任务")

# 3. Also clear completed if any just in case
conn3 = sqlite3.connect("/home/ubuntu/oiioii/data/oiioii_pool.db")
cnt3 = conn3.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
print(f"OiioiiPool 剩余: {cnt3} 个（已完成的）")
conn3.close()
'''

sftp = client.open_sftp()
with sftp.file('/tmp/clean_all_now.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/clean_all_now.py', timeout=10)
print(stdout.read().decode()[:500])

client.close()