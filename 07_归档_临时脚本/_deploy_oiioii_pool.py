import paramiko, tarfile, io

key = paramiko.RSAKey.from_private_key_file(
    r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=10)

LOCAL_OIIOII = r'C:\Users\Administrator\Documents\OiioiiPool'

# 打包 OiioiiPool core + api + config
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w:gz') as tar:
    tar.add(f'{LOCAL_OIIOII}/core', 'core')
    tar.add(f'{LOCAL_OIIOII}/api', 'api')
    tar.add(f'{LOCAL_OIIOII}/config.py', 'config.py')
buf.seek(0)

print("=== 上传 OiioiiPool 新代码 ===")
sftp = client.open_sftp()
with sftp.file('/tmp/oiioii_update.tar.gz', 'wb') as f:
    f.write(buf.getvalue())
sftp.close()

cmds = [
    # Backup old code
    "cp -r /home/ubuntu/oiioii/core /home/ubuntu/oiioii/core_bak",
    "cp /home/ubuntu/oiioii/config.py /home/ubuntu/oiioii/config_bak.py",
    # Deploy new code
    "tar -xzf /tmp/oiioii_update.tar.gz -C /home/ubuntu/oiioii",
    # Cleanup backup
    "rm -rf /home/ubuntu/oiioii/core_bak /home/ubuntu/oiioii/config_bak.py",
    # Restart
    "sudo systemctl restart oiioii && sleep 3",
    "echo '=== status ===' && sudo systemctl status oiioii --no-pager | head -4",
]

print("=== 部署 ===")
for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out: print(out[:500])
    if err: print(f"ERR: {err[:200]}")

print("=== 验证 ===")
vcmd = "curl -s http://127.0.0.1:7861/api/pool/status | python3 -c 'import sys,json;d=json.load(sys.stdin);print(f\"total={d[chr(116)+chr(111)+chr(116)+chr(97)+chr(108)+chr(95)+chr(97)+chr(99)+chr(99)+chr(111)+chr(117)+chr(110)+chr(116)+chr(115)]} active={d[chr(97)+chr(99)+chr(116)+chr(105)+chr(118)+chr(101)+chr(95)+chr(97)+chr(99)+chr(99)+chr(111)+chr(117)+chr(110)+chr(116)+chr(115)]}\")'"
stdin, stdout, stderr = client.exec_command(vcmd, timeout=10)
out = stdout.read().decode()
print(out[:200] if out else "")
client.close()

print("✅ 部署完成！")