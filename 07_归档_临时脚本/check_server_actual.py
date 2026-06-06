import paramiko

key_path = r'C:\Users\Administrator\Documents\锤子Aicg\02_腾讯云服务器\keys\ssh_key.pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=15)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    return stdout.read().decode()

# 1. OiioiiPool db.py - 选号策略
print("=== OiioiiPool core/db.py - get_available ===")
print(run("sed -n '119,134p' /home/ubuntu/oiioii/core/db.py"))

# 2. OiioiiPool engine.py - submit里的prefer_lowest
print("\n=== OiioiiPool core/engine.py - submit中的ensure_available_account ===")
print(run("sed -n '74,82p' /home/ubuntu/oiioii/core/engine.py"))

# 3. OiioiiPool engine.py - 超时设置
print("\n=== OiioiiPool core/engine.py - timeout逻辑 ===")
print(run("sed -n '184,190p' /home/ubuntu/oiioii/core/engine.py"))

# 4. OiioiiPool pool.py - get_available_client 参数
print("\n=== OiioiiPool core/pool.py - get_available_client ===")
print(run("sed -n '41,43p' /home/ubuntu/oiioii/core/pool.py"))

# 5. OiioiiPool api/server.py - 视频上传
print("\n=== OiioiiPool api/server.py - upload_video_ref ===")
print(run("sed -n '105,122p' /home/ubuntu/oiioii/api/server.py"))

# 6. AiForge generate.py - 超时
print("\n=== AiForge api/generate.py - _poll_oiioii最大等待时间 ===")
print(run("sed -n '66,70p' /home/ubuntu/aiforge/backend/api/generate.py"))

# 7. AiForge generate.py - refs路由
print("\n=== AiForge api/generate.py - refs路由是否存在 ===")
print(run("grep -n 'refs' /home/ubuntu/aiforge/backend/api/generate.py | head -10"))

client.close()