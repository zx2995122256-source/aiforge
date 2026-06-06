import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check how generate_video in engine.py handles reference_video
stdin, stdout, stderr = client.exec_command(
    'grep -n -A 15 "def generate_video\|reference_video" /home/ubuntu/oiioii/core/engine.py 2>/dev/null | head -60',
    timeout=10
)
print("=== engine.py generate_video ===")
print(stdout.read().decode()[:2000])

# Also check the pool handler for generate_video  
stdin, stdout, stderr = client.exec_command(
    'grep -n -A 20 "def generate_video\|reference_video" /home/ubuntu/oiioii/core/pool.py 2>/dev/null | head -60',
    timeout=10
)
print("\n=== pool.py generate_video ===")
print(stdout.read().decode()[:2000])

client.close()