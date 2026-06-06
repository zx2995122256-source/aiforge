import paramiko

key = paramiko.RSAKey.from_private_key_file(
    r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=10)

# 看完整文件结构
cmds = [
    "find /home/ubuntu/aiforge -maxdepth 3 -type d | sort",
    "ls -la /home/ubuntu/aiforge/frontend/dist/index.html 2>/dev/null || echo '没有 frontend/dist'",
    "ls -la /home/ubuntu/aiforge/dist/index.html 2>/dev/null || echo '没有 dist'",
    # 检查旧dist和frontend动态（main.py中有hardcode指向frontend/dist）
    "find /home/ubuntu -maxdepth 4 -name 'index.html' -path '*/dist/*' 2>/dev/null",
    # 检查进程实际使用的文件
    "cat /home/ubuntu/aiforge/backend/main.py | grep -n 'FRONTEND_DIR\\|frontend\\|dist'",
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out: print(f"{out[:2000]}")
    if err: print(f"ERR: {err[:300]}")

client.close()