import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check running processes
stdin, stdout, stderr = client.exec_command('ps aux | grep -v grep | grep -E "oiioii|python" | head -20')
print("Processes:")
print(stdout.read().decode()[:2000])

# Check if OiioiiPool is actually running
stdin, stdout, stderr = client.exec_command('curl -s http://127.0.0.1:7861/api/accounts 2>/dev/null | head -c 500')
print("Accounts endpoint:")
print(stdout.read().decode()[:500])

# Check databases
stdin, stdout, stderr = client.exec_command('ls -la /home/ubuntu/oiioii/data/ 2>/dev/null')
print("Oiioii data:")
print(stdout.read().decode()[:500])

# Check if there's a config file
stdin, stdout, stderr = client.exec_command('cat /home/ubuntu/oiioii/config.py 2>/dev/null | head -30')
print("Oiioii config:")
print(stdout.read().decode()[:1000])

client.close()