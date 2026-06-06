import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check the actual structure
stdin, stdout, stderr = client.exec_command('find /home/ubuntu/aiforge/backend -name "*.py" | sort')
print("Backend files:")
print(stdout.read().decode()[:1000])

# Restore from git or the old structure
stdin, stdout, stderr = client.exec_command('ls /home/ubuntu/aiforge.backup 2>/dev/null && echo "HAS BACKUP" || echo "NO BACKUP"')
print("\nBackup check:", stdout.read().decode()[:100])

client.close()