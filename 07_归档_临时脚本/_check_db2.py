import paramiko

key = paramiko.RSAKey.from_private_key_file(
    r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=10)

cmds = [
    "echo '=== point_logs schema ===' && python3 -c \"import sqlite3;c=sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db');c.execute('PRAGMA table_info(point_logs)');[print(x) for x in c.fetchall()]\"",
    "echo '=== tasks schema ===' && python3 -c \"import sqlite3;c=sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db');c.execute('PRAGMA table_info(tasks)');[print(x) for x in c.fetchall()]\"",
    "echo '=== point_logs data ===' && python3 -c \"import sqlite3;c=sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db');r=c.execute('SELECT * FROM point_logs LIMIT 10').fetchall();[print(x) for x in r]\"",
    "echo '=== tasks data ===' && python3 -c \"import sqlite3;c=sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db');r=c.execute('SELECT * FROM tasks LIMIT 10').fetchall();[print(x) for x in r]\"",
    "echo '=== 是否有旧数据库备份 ===' && find /tmp -name 'aiforge*' -type f 2>/dev/null",
    "echo '=== 历史数据备份 ===' && ls -la /home/ubuntu/aiforge/backend_backup/ 2>/dev/null || echo '无备份目录'",
]

for cmd in cmds:
    out, err, _ = None, None, None
    try:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
        out = stdout.read().decode()
        err = stderr.read().decode()
    except Exception as e:
        out = f"ERROR: {e}"
    if out: print(out[:2000])
    if err: print(f"ERR: {err[:300]}")

client.close()