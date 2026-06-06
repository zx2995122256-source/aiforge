import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=10)

cmds = [
    'echo "=== BACKEND MAIN.PY (server) ===" && wc -l /home/ubuntu/aiforge/backend/main.py',
    'echo "=== FRONTEND INDEX (server) ===" && cat /home/ubuntu/aiforge/dist/index.html | head -5',
    'echo "=== FRONTEND ASSETS (server) ===" && ls -la /home/ubuntu/aiforge/dist/assets/',
    'echo "=== BACKEND FILES (server) ===" && find /home/ubuntu/aiforge/backend -name "*.py" | sort',
    'echo "=== config.py server ===" && cat /home/ubuntu/aiforge/backend/config.py',
]

for cmd in cmds:
    print(f'{cmd.split("&&")[-1].strip()}')  # just show the label
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out: print(out[:1000])
    if err: print(f'ERR: {err[:200]}')

client.close()