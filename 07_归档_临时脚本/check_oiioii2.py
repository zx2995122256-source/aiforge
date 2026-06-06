import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

sftp = client.open_sftp()
with sftp.file('/tmp/check_pool2.sh', 'w') as f:
    f.write('curl -s http://127.0.0.1:7861/models 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps({k:v for k,v in d.items() if k in [\'total_points\',\'total_accounts\',\'active_accounts\',\'error\']}, indent=2))"\n')
    f.write('curl -s http://127.0.0.1:7861/api/models 2>/dev/null | head -c 200\n')
    f.write('echo ---\n')
    f.write('curl -s http://127.0.0.1:7861/ 2>/dev/null | head -c 200\n')
sftp.close()

stdin, stdout, stderr = client.exec_command('bash /tmp/check_pool2.sh')
print(stdout.read().decode()[:3000])
print('STDERR:', stderr.read().decode()[:500])
client.close()