import paramiko

key = paramiko.RSAKey.from_private_key_file(
    r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=10)

sftp = client.open_sftp()
sftp.put(r'C:\Users\Administrator\Documents\OiioiiPool\core\db.py', '/home/ubuntu/oiioii/core/db.py')
sftp.close()

# Restart to re-run migrations
stdin, stdout, stderr = client.exec_command('sudo systemctl restart oiioii && sleep 2', timeout=15)
out = stdout.read().decode()
err = stderr.read().decode()

# Check video_used distribution
script = """import sqlite3
c = sqlite3.connect('/home/ubuntu/oiioii/data/oiioii_pool.db')
print('video_used分布:')
for r in c.execute('SELECT video_used, COUNT(*), SUM(points_remaining) FROM accounts GROUP BY video_used').fetchall():
    t = '图片池' if r[0] else '视频池'
    print(f'  {t}: {r[1]}个, 总积分{r[2]}')
print()
print('200+分账号:')
for r in c.execute('SELECT id, email, points_remaining, video_used, status FROM accounts WHERE points_remaining>=200').fetchall():
    v = '可视频' if not r[3] else '图片池'
    print(f'  #{r[0]} {r[1]:<30} {r[2]}pts [{v}] {r[4]}')
"""

sftp2 = client.open_sftp()
with sftp2.file('/tmp/check_v2.py', 'w') as f:
    f.write(script)
sftp2.close()

stdin2, stdout2, stderr2 = client.exec_command('python3 /tmp/check_v2.py', timeout=10)
out2 = stdout2.read().decode()
err2 = stderr2.read().decode()
print(out2)
if err2: print(f"ERR: {err2[:300]}")

client.close()
print("✅ 修复完成")