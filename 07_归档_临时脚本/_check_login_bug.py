import paramiko

key = paramiko.RSAKey.from_private_key_file(
    r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=10)

# 检查login前端的built文件 - 看看是否有隐藏的登录逻辑
cmds = [
    "grep -l 'shareholder\|SH267924\|auto.*login\|debug' /home/ubuntu/aiforge/dist/assets/*.js 2>/dev/null | head -5",
    # 检查localStorage中登录相关的key
    "grep -o \"'[^']*token'\\|\"[^\"]*token\"\" /home/ubuntu/aiforge/dist/assets/index-*.js 2>/dev/null | head -10",
    # 看看有没有auto login的逻辑
    "grep -o 'localStorage.*login\\|autoLogin\\|auto_login' /home/ubuntu/aiforge/dist/assets/*.js 2>/dev/null | head -10",
    # 检查最近生成的任务 - 看看谁在用
    "python3 -c \"import sqlite3;c=sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db');r=c.execute('SELECT id, user_id, type, prompt, status, created_at FROM tasks ORDER BY id DESC LIMIT 5').fetchall();[print(x) for x in r]\"",
    # 检查用户2的活动
    "python3 -c \"import sqlite3;c=sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db');r=c.execute('SELECT user_id, COUNT(*) as cnt, SUM(points) as total_pts FROM point_logs GROUP BY user_id').fetchall();[print(f'user#{x[0]}: {x[1]}条记录, {x[2]}积分') for x in r]\"",
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out: print(f"{out[:2000]}")
    if err: print(f"ERR: {err[:300]}")

client.close()