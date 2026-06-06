import paramiko

key_path = r'C:\Users\Administrator\Documents\锤子Aicg\02_腾讯云服务器\keys\ssh_key.pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=15)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    return stdout.read().decode()

# 服务器完整关键函数
print("=== 服务器: get_available (db.py) ===")
print(run("grep -A 20 'def get_available' /home/ubuntu/oiioii/core/db.py"))

print("\n=== 服务器: submit (engine.py) ===")
print(run("grep -A 40 'def submit' /home/ubuntu/oiioii/core/engine.py | head -45"))

print("\n=== 服务器: _ensure_available_account ===")
print(run("grep -A 15 'def _ensure_available_account' /home/ubuntu/oiioii/core/engine.py"))

print("\n=== 服务器: _run_task timeout===")
print(run("grep -A 10 'timeout = ' /home/ubuntu/oiioii/core/engine.py"))

client.close()