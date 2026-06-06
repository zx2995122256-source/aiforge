import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

sftp = client.open_sftp()
sftp.put(r'C:\Users\Administrator\Documents\oiioii_v3.tar.gz', '/tmp/oiioii_v3.tar.gz')
sftp.close()

commands = [
    'rm -rf /home/ubuntu/oiioii/core /home/ubuntu/oiioii/api /home/ubuntu/oiioii/config.py /home/ubuntu/oiioii/main.py',
    'tar -xzf /tmp/oiioii_v3.tar.gz -C /home/ubuntu/oiioii',
    'sudo systemctl restart oiioii',
    'sleep 2',
    'sudo systemctl status oiioii --no-pager | head -5',
    'curl -s http://127.0.0.1:7861/api/models | python3 -c "import sys,json; d=json.load(sys.stdin); print(\'video models:\', list(d.get(\'video\',{}).keys())); print(\'image models:\', list(d.get(\'image\',{}).keys()))"',
]

for cmd in commands:
    print(f'>>> {cmd[:80]}')
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out: print(out.strip()[:300])
    if err: print(f'STDERR: {err.strip()[:200]}')
    print('---')

client.close()
print('Done!')
