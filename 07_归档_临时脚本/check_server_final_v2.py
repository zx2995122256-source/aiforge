import paramiko, os

key_path = r'C:\Users\Administrator\Documents\锤子Aicg\02_腾讯云服务器\keys\ssh_key.pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=15)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    return stdout.read().decode()

print("=== DB路径 ===")
print(run("find /home/ubuntu/oiioii -name '*.db' -type f"))

print("\n=== 服务器 engine.py 函数列表 ===")
print(run("grep -n 'def ' /home/ubuntu/oiioii/core/engine.py"))

print("\n=== 超时行 ===")
print(run("grep -n 'timeout' /home/ubuntu/oiioii/core/engine.py"))

print("\n=== 服务PID ===")
print(run("ps aux | grep -E 'python3.*oiioii|python3.*aiforge' | grep -v grep"))

client.close()

# Local file sizes
for path, label in [
    (r'C:\Users\Administrator\Documents\锤子Aicg\04_OiioiiPool账号池\core\client.py', '锤子Aicg/client.py'),
    (r'C:\Users\Administrator\Documents\锤子Aicg\04_OiioiiPool账号池\core\engine.py', '锤子Aicg/engine.py'),
    (r'C:\Users\Administrator\Documents\OiioiiPool\core\client.py', '本地原始/client.py'),
    (r'C:\Users\Administrator\Documents\OiioiiPool\core\engine.py', '本地原始/engine.py'),
]:
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"本地 {label}: {size} bytes")
    else:
        print(f"本地 {label}: 不存在")