import paramiko

key = paramiko.RSAKey.from_private_key_file(
    r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=10)

# Check video_used distribution
script = """import sqlite3
c = sqlite3.connect('/home/ubuntu/oiioii/data/oiioii_pool.db')
print('=== video_used 分布 ===')
for r in c.execute('SELECT video_used, COUNT(*) as cnt, SUM(points_remaining) as pts FROM accounts GROUP BY video_used').fetchall():
    v = '已用于视频' if r[0] else '等待视频'
    print(f'  {v}: {r[1]} 个, 总积分={r[2]}')
print()
print('=== 200+分 账号 ===')
for r in c.execute('SELECT id, email, points_remaining, video_used FROM accounts WHERE points_remaining >= 200 ORDER BY points_remaining DESC LIMIT 10').fetchall():
    v = '可生视频' if not r[3] else '已用完'
    print(f'  #{r[0]} {r[1]:<30} {r[2]}pts [{v}]')
print()
print('=== 完整状态 ===')
for r in c.execute('SELECT video_used, status, COUNT(*) FROM accounts GROUP BY video_used, status').fetchall():
    v = '视频池' if not r[0] else '图片池'
    print(f'  [{v}] {r[1]}: {r[2]} 个')
c.close()
"""

sftp = client.open_sftp()
with sftp.file('/tmp/check_video_used.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/check_video_used.py', timeout=10)
out = stdout.read().decode()
err = stderr.read().decode()
print(out)
if err: print(f"ERR: {err[:300]}")
client.close()