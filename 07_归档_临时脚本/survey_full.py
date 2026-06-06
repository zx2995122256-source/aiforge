import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=15)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    return stdout.read().decode()

# 1. 服务器文件结构
print("=== SERVER: /home/ubuntu/ 目录树 ===")
print(run("find /home/ubuntu/ -maxdepth 3 -type f | head -80"))

# 2. 服务列表
print("\n=== SERVER: systemd 服务 ===")
print(run("ls -la /etc/systemd/system/ | grep -E 'aiforge|oiioii|nginx'"))

# 3. Oiioii 服务文件
print("\n=== SERVER: oiioii.service ===")
print(run("cat /etc/systemd/system/oiioii.service"))

# 4. AiForge 服务文件
print("\n=== SERVER: aiforge.service ===")
print(run("cat /etc/systemd/system/aiforge.service"))

# 5. Oiioii 完整文件列表
print("\n=== SERVER: /home/ubuntu/oiioii/ 文件树 ===")
print(run("find /home/ubuntu/oiioii/ -type f | sort"))

# 6. AiForge 完整文件列表
print("\n=== SERVER: /home/ubuntu/aiforge/ 文件树 ===")
print(run("find /home/ubuntu/aiforge/ -type f | sort"))

# 7. 端口和 Nginx
print("\n=== SERVER: 监听端口 ===")
print(run("ss -tlnp | grep -v '127.0.0.53'"))

# 8. 防火墙
print("\n=== SERVER: 防火墙 ===")
print(run("sudo ufw status 2>/dev/null || echo 'ufw not active'"))

# 9. Nginx
print("\n=== SERVER: Nginx ===")
print(run("nginx -t 2>&1"))
print(run("ls /etc/nginx/sites-enabled/ 2>/dev/null; cat /etc/nginx/sites-enabled/default 2>/dev/null || cat /etc/nginx/conf.d/default.conf 2>/dev/null"))

# 10. SSH key
print("\n=== LOCAL: SSH key 路径 ===")
print(r"C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem")

client.close()