import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

sftp = client.open_sftp()
with sftp.file('/tmp/check_pool.sh', 'w') as f:
    f.write('#!/bin/bash\ncurl -s http://127.0.0.1:7861/api/status 2>/dev/null | python3 -m json.tool 2>/dev/null || curl -s http://127.0.0.1:7861/api/pool/status 2>/dev/null | python3 -m json.tool')
sftp.close()

stdin, stdout, stderr = client.exec_command('bash /tmp/check_pool.sh')
print(stdout.read().decode()[:3000])
client.close()