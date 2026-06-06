import paramiko

key_path = r'C:\Users\Administrator\Documents\锤子Aicg\02_腾讯云服务器\keys\ssh_key.pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=15)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    return stdout.read().decode()

# 服务器完整pool.py
print("=== 服务器 pool.py ===")
print(run("cat /home/ubuntu/oiioii/core/pool.py"))

# 数据库schema - 查video_used字段
print("\n=== 数据库 accounts 表结构 ===")
print(run("sqlite3 /home/ubuntu/oiioii/data/oiioii_pool.db '.schema accounts'"))

# 查有几个video_used=0的号
print("\n=== 账号统计 ===")
print(run("sqlite3 /home/ubuntu/oiioii/data/oiioii_pool.db 'SELECT video_used, COUNT(*) FROM accounts WHERE status=\"active\" GROUP BY video_used'"))

# 比较本地和服务器版本差异
print("\n=== 服务器client.py - 完整 ===")
print(run("wc -l /home/ubuntu/oiioii/core/client.py"))

# 服务器engine.py完整
print("\n=== 服务器engine.py行数 ===")
print(run("wc -l /home/ubuntu/oiioii/core/engine.py"))

client.close()