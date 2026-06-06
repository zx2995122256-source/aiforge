import paramiko

key_path = r'C:\Users\Administrator\Documents\锤子Aicg\02_腾讯云服务器\keys\ssh_key.pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=15)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    return stdout.read().decode()

# 1. systemd services
aiforge_svc = run("cat /etc/systemd/system/aiforge.service")
oiioii_svc = run("cat /etc/systemd/system/oiioii.service")
nginx_conf = run("cat /etc/nginx/sites-enabled/aiforge 2>/dev/null || cat /etc/nginx/conf.d/default.conf 2>/dev/null || echo 'N/A'")

# Write locally
import os
base = r'C:\Users\Administrator\Documents\锤子Aicg\02_腾讯云服务器'
with open(os.path.join(base, 'aiforge.service'), 'w') as f:
    f.write(aiforge_svc)
with open(os.path.join(base, 'oiioii.service'), 'w') as f:
    f.write(oiioii_svc)
with open(os.path.join(base, 'nginx_aiforge.conf'), 'w') as f:
    f.write(nginx_conf)

# 2. AiForge main.py and config.py from server (for reference)
aiforge_main = run("cat /home/ubuntu/aiforge/backend/main.py")
aiforge_config = run("cat /home/ubuntu/aiforge/backend/config.py")
with open(os.path.join(base, 'aiforge_main.py'), 'w') as f:
    f.write(aiforge_main)
with open(os.path.join(base, 'aiforge_config.py'), 'w') as f:
    f.write(aiforge_config)

# 3. Server info
info = run("echo 'OS: $(cat /etc/os-release | head -1)' ; echo 'Kernel: $(uname -r)' ; echo 'CPU: $(nproc --all) cores' ; echo 'RAM: $(free -h | grep Mem | awk \"{print \\$2}\")' ; echo 'Disk: $(df -h / | tail -1 | awk \"{print \\$3 \\\" / \\\" \\$2 \\\" (\\$5)\\\"}\")'")
with open(os.path.join(base, '服务器信息.txt'), 'w') as f:
    f.write(f"IP: 122.51.205.94\n用户: ubuntu\nSSH密钥: keys/ssh_key.pem\n\n{info}")

print("✅ 服务器配置已导出")
client.close()