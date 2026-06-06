import paramiko, tarfile, io

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w:gz') as tar:
    tar.add(r"C:\Users\Administrator\Documents\AiForge\frontend\dist", "dist")
    tar.add(r"C:\Users\Administrator\Documents\AiForge\backend\api\generate.py", "backend/api/generate.py")
buf.seek(0)

sftp = client.open_sftp()
with sftp.file('/tmp/promo.tar.gz', 'wb') as f:
    f.write(buf.getvalue())
sftp.close()
print("Uploaded")

cmds = [
    "rm -rf /tmp/promo && mkdir -p /tmp/promo && tar -xzf /tmp/promo.tar.gz -C /tmp/promo",
    "rm -rf /home/ubuntu/aiforge/dist && cp -r /tmp/promo/dist /home/ubuntu/aiforge/dist",
    "cp /tmp/promo/backend/api/generate.py /home/ubuntu/aiforge/backend/api/generate.py",
    "sudo systemctl restart aiforge && sleep 3",
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
    out = stdout.read().decode().strip()
    if out: print(f"  {out[:200]}")

# Verify
print("\n=== VERIFY ===")
vcmds = [
    ("Site", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:7862/"),
    ("Cost", '''curl -s -X POST http://127.0.0.1:7862/api/auth/login -H "Content-Type: application/json" -d '{"email":"xiaye@aiforge.com","password":"zx4579561"}' | python3 -c "import sys,json;t=json.load(sys.stdin)['token'];print(t[:10])" && curl -s -X POST http://127.0.0.1:7862/api/gen/video -H "Content-Type: application/json" -H "Authorization: Bearer $(curl -s -X POST http://127.0.0.1:7862/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"xiaye@aiforge.com\",\"password\":\"zx4579561\"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)[\"token\"])')" -d '{"prompt":"test","model":"Vidu Q2","ratio":"16:9","resolution":"1080p","duration":10,"reference_images":[],"reference_video":""}' | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'cost={d.get(chr(99)+chr(111)+chr(115)+chr(116),\"?\")}')"'''),
]

for label, cmd in vcmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    print(f"  [{label}] {stdout.read().decode().strip()[:200]}")

client.close()
print("\n✅ DONE!")