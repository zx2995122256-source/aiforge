import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check server config.ini
stdin, stdout, stderr = client.exec_command('cat /home/ubuntu/oiioii/config.ini 2>/dev/null')
print("Config.ini:")
print(stdout.read().decode()[:2000])

# Check pool.py for watcher logic
stdin, stdout, stderr = client.exec_command('grep -n "watcher\|auto_register\|POOL_MIN\|MIN_POINTS\|replenish\|sleep(30\|while True\|_watcher\|_loop" /home/ubuntu/oiioii/core/pool.py 2>/dev/null | head -30')
print("\nPool watcher:")
print(stdout.read().decode()[:1000])

client.close()