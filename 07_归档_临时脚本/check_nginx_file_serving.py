import paramiko

key_path = r'C:\Users\Administrator\Documents\锤子Aicg\02_腾讯云服务器\keys\ssh_key.pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=15)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    return stdout.read().decode()

# Nginx配置
print("=== Nginx配置 ===")
print(run("cat /etc/nginx/sites-enabled/aiforge 2>/dev/null || cat /etc/nginx/conf.d/default.conf 2>/dev/null || echo 'N/A'"))

# Nginx主配置
print("\n=== nginx.conf ===")
print(run("cat /etc/nginx/nginx.conf 2>/dev/null | head -30"))

# 文件代理路径 - 检查文件怎么被serve
print("\n=== AiForge generate.py (服务器版本) 文件服务部分 ===")
print(run("sed -n '224,261p' /home/ubuntu/aiforge/backend/api/generate.py"))

# OiioiiPool server.py 下载部分
print("\n=== OiioiiPool /api/task/{id}/download ===")
print(run("sed -n '168,190p' /home/ubuntu/oiioii/api/server.py"))

# 文件实际位置和大小
print("\n=== 输出文件大小示例 ===")
print(run("ls -lh /home/ubuntu/oiioii/data/output/2026-06-02/ | tail -5"))

client.close()