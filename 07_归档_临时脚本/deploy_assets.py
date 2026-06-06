import paramiko, tarfile, io

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Package frontend + backend
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w:gz') as tar:
    tar.add(r"C:\Users\Administrator\Documents\AiForge\frontend\dist", "dist")
    tar.add(r"C:\Users\Administrator\Documents\AiForge\backend\api\generate.py", "backend/api/generate.py")
    tar.add(r"C:\Users\Administrator\Documents\AiForge\backend\config.py", "backend/config.py")
buf.seek(0)

sftp = client.open_sftp()
with sftp.file('/tmp/deploy_assets.tar.gz', 'wb') as f:
    f.write(buf.getvalue())
sftp.close()
print("Uploaded")

# Deploy
cmds = [
    "rm -rf /tmp/deploy_assets && mkdir -p /tmp/deploy_assets && tar -xzf /tmp/deploy_assets.tar.gz -C /tmp/deploy_assets",
    # Frontend
    "rm -rf /home/ubuntu/aiforge/dist && cp -r /tmp/deploy_assets/dist /home/ubuntu/aiforge/dist",
    # Backend generate.py  
    "cp /tmp/deploy_assets/backend/api/generate.py /home/ubuntu/aiforge/backend/api/generate.py",
    "cp /tmp/deploy_assets/backend/config.py /home/ubuntu/aiforge/backend/config.py",
    # Fix nested dirs
    "rm -rf /home/ubuntu/aiforge/backend/api/api 2>/dev/null",
    # Restart
    "sudo systemctl restart aiforge && sleep 3 && sudo systemctl restart oiioii && sleep 2",
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(f"  {out[:200]}")
    if err: print(f"  ERR: {err[:100]}")

# Verify
print("\n=== VERIFY ===")
vcmds = [
    ("Site", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:7862/"),
    ("Login", "curl -s -X POST http://127.0.0.1:7862/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"xiaye@aiforge.com\",\"password\":\"zx4579561\"}' | python3 -c 'import sys,json;d=json.load(sys.stdin);print(f\"OK role={d[chr(117)+chr(115)+chr(101)+chr(114)][chr(114)+chr(111)+chr(108)+chr(101)]}\")'"),
    ("Services", "echo 'aiforge='$(sudo systemctl is-active aiforge)' oiioii='$(sudo systemctl is-active oiioii)"),
    ("Assets", '''curl -s -o /dev/null -w "img1=%{http_code}" http://127.0.0.1:7862/api/gen/file/271 && curl -s -o /dev/null -w " img2=%{http_code}" http://127.0.0.1:7862/api/gen/file/272 && curl -s -o /dev/null -w " img3=%{http_code}" http://127.0.0.1:7862/api/gen/file/273 && curl -s -o /dev/null -w " vid=%{http_code}" http://127.0.0.1:7862/api/gen/file/275'''),
]

for label, cmd in vcmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    print(f"  [{label}] {stdout.read().decode().strip()[:200]}")

client.close()
print("\n✅ ALL DONE!")