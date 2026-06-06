import paramiko

key = paramiko.RSAKey.from_private_key_file(
    r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=10)

# 找所有数据库文件
cmds = [
    'echo "=== 查找所有数据库 ===" && find /home/ubuntu -name "*.db" -type f 2>/dev/null',
    'echo "=== 查找.aiforge.db备份 ===" && find /home/ubuntu -name "aiforge.db*" -type f 2>/dev/null',
    'echo "=== data目录 ===" && ls -la /home/ubuntu/aiforge/backend/data/',
    'echo "=== 查看是否有备份目录残留 ===" && ls -la /home/ubuntu/aiforge/',
    'echo "=== 检查旧版本备份 ===" && find /tmp -name "*.tar.gz" -mtime -1 2>/dev/null',
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    out = stdout.read().decode()
    err = stderr.read().decode()
    label = cmd.split('&&')[0].replace('echo "=== ','').replace(' ==="','')
    print(f"【{label}】")
    if out: print(out[:500])
    if err: print(f"  ERR: {err[:200]}")

client.close()