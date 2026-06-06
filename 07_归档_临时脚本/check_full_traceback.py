import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Get full log
stdin, stdout, stderr = client.exec_command('sudo journalctl -u aiforge --no-pager -n 150')
full = stdout.read().decode()
idx = full.find("Traceback")
if idx >= 0:
    print(full[idx:idx+3000])

client.close()
