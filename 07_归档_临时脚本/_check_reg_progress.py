import paramiko
import time
import json

KEY_PATH = r"C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem"
HOST = "122.51.205.94"
USER = "ubuntu"

JOB_ID = "1780318376429"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, key_filename=KEY_PATH, timeout=15)

# Check job progress
stdin, stdout, _ = ssh.exec_command(f"curl -s http://localhost:7861/api/pool/register/{JOB_ID}")
print(f"=== Job status ===")
print(stdout.read().decode().strip())

# Check current DB stats
stdin, stdout, _ = ssh.exec_command('''python3 -c "
import sqlite3
db = sqlite3.connect('/home/ubuntu/oiioii/data/oiioii_pool.db')
active = db.execute('SELECT COUNT(*) FROM accounts WHERE status=\"active\"').fetchone()[0]
total = db.execute('SELECT COUNT(*) FROM accounts').fetchone()[0]
pts = db.execute('SELECT COALESCE(SUM(points_remaining),0) FROM accounts').fetchone()[0]
video = db.execute('SELECT COUNT(*) FROM accounts WHERE status=\"active\" AND video_used=0 AND points_remaining>=200').fetchone()[0]
image = db.execute('SELECT COUNT(*) FROM accounts WHERE status=\"active\" AND video_used=1').fetchone()[0]
newest = db.execute('SELECT email, points_remaining FROM accounts ORDER BY id DESC LIMIT 3').fetchall()
print(f'Total: {total}')
print(f'Active: {active}')
print(f'Total points: {pts}')
print(f'Video pool: {video}')
print(f'Image pool: {image}')
if newest:
    print(f'Newest accounts:')
    for e, p in newest:
        print(f'  {e} pts={p}')
db.close()
"''')
print(f"\n=== Database stats ===")
print(stdout.read().decode())

ssh.close()

print("\n注册已经在后台跑了，预计50-100分钟完成。")
print("需要我过一会儿再查进度吗？")