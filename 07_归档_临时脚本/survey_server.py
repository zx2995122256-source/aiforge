import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=15)

# 1. 看看服务器上有哪些项目
stdin, stdout, stderr = client.exec_command('ls -la /home/ubuntu/', timeout=10)
print("=== /home/ubuntu/ ===")
print(stdout.read().decode()[:500])

# 2. 看看系统服务
stdin, stdout, stderr = client.exec_command('systemctl list-units --type=service --state=running | grep -E "aiforge|oiioii|nginx|caddy|docker"', timeout=10)
print("\n=== 运行中的服务 ===")
print(stdout.read().decode()[:500])

# 3. 看看端口
stdin, stdout, stderr = client.exec_command('ss -tlnp | grep -E "786|80|443|3000"', timeout=10)
print("\n=== 监听端口 ===")
print(stdout.read().decode()[:500])

# 4. 看看 Nginx 配置
stdin, stdout, stderr = client.exec_command('cat /etc/nginx/sites-enabled/default 2>/dev/null || cat /etc/nginx/conf.d/default.conf 2>/dev/null || nginx -T 2>/dev/null | head -50', timeout=10)
print("\n=== Nginx ===")
print(stdout.read().decode()[:500])

# 5. 看看 AiForge main.py
stdin, stdout, stderr = client.exec_command('head -30 /home/ubuntu/aiforge/backend/main.py', timeout=10)
print("\n=== AiForge main.py ===")
print(stdout.read().decode()[:500])

# 6. 看看 OiioiiPool main.py
stdin, stdout, stderr = client.exec_command('head -30 /home/ubuntu/oiioii/main.py', timeout=10)
print("\n=== OiioiiPool main.py ===")
print(stdout.read().decode()[:500])

client.close()