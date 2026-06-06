import paramiko, tarfile, io

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Package
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w:gz') as tar:
    tar.add(r"C:\Users\Administrator\Documents\AiForge\frontend\dist", "dist")
    tar.add(r"C:\Users\Administrator\Documents\AiForge\backend\api\generate.py", "backend/api/generate.py")
buf.seek(0)

sftp = client.open_sftp()
with sftp.file('/tmp/video_fix.tar.gz', 'wb') as f:
    f.write(buf.getvalue())
sftp.close()
print("Uploaded")

# Deploy
cmds = [
    "rm -rf /tmp/vf && mkdir -p /tmp/vf && tar -xzf /tmp/video_fix.tar.gz -C /tmp/vf",
    "rm -rf /home/ubuntu/aiforge/dist && cp -r /tmp/vf/dist /home/ubuntu/aiforge/dist",
    "cp /tmp/vf/backend/api/generate.py /home/ubuntu/aiforge/backend/api/generate.py",
    "rm -rf /home/ubuntu/aiforge/backend/api/api 2>/dev/null",
    "sudo systemctl restart aiforge && sleep 3 && sudo systemctl restart oiioii && sleep 2",
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
    out = stdout.read().decode().strip()
    if out: print(f"  {out[:200]}")

# Verify
print("\n=== VERIFY ===")
vcmds = [
    ("Site", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:7862/"),
    ("Login", "curl -s -X POST http://127.0.0.1:7862/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"xiaye@aiforge.com\",\"password\":\"zx4579561\"}' | python3 -c 'import sys,json;d=json.load(sys.stdin);print(f\"OK\")'"),
    ("Srv", "echo 'ai='$(sudo systemctl is-active aiforge)' oi='$(sudo systemctl is-active oiioii)"),
    ("Img271", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:7862/api/gen/file/271"),
    ("Img276", "curl -s -o /dev/null -w ' %{http_code}' http://127.0.0.1:7862/api/gen/file/276"),
    ("Vid275", "curl -s -o /dev/null -w ' %{http_code}' http://127.0.0.1:7862/api/gen/file/275"),
    ("VidSpeed", "time curl -s -o /dev/null -w '%%{speed_download}' http://127.0.0.1:7862/api/gen/file/275 2>&1 | tail -1"),
]

for label, cmd in vcmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    print(f"  [{label}] {stdout.read().decode().strip()[:150]}")

client.close()
print("\n✅ DONE! http://122.51.205.94")