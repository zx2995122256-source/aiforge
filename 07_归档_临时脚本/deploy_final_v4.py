import paramiko, tarfile, io

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w:gz') as tar:
    tar.add(r"C:\Users\Administrator\Documents\AiForge\frontend\dist", "dist")
buf.seek(0)

sftp = client.open_sftp()
with sftp.file('/tmp/final.tar.gz', 'wb') as f:
    f.write(buf.getvalue())
sftp.close()
print("Uploaded")

cmds = [
    "rm -rf /home/ubuntu/aiforge/dist && mkdir -p /home/ubuntu/aiforge",
    "tar -xzf /tmp/final.tar.gz -C /home/ubuntu/aiforge",
    "sudo systemctl restart aiforge && sleep 2 && sudo systemctl restart oiioii && sleep 2",
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
    out = stdout.read().decode().strip()
    if out: print(f"  {out[:200]}")

# Verify
print("\n=== VERIFY ===")
vcmds = [
    ("Site", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:7862/"),
    ("Login", "curl -s -X POST http://127.0.0.1:7862/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"xiaye@aiforge.com\",\"password\":\"zx4579561\"}' | python3 -c 'import sys,json;d=json.load(sys.stdin);print(f\"OK role={d[chr(117)+chr(115)+chr(101)+chr(114)][chr(114)+chr(111)+chr(108)+chr(101)]}\")'"),
    ("Srv", "echo 'aiforge='$(sudo systemctl is-active aiforge)' oiioii='$(sudo systemctl is-active oiioii)"),
    ("Assets", '''curl -s -o /dev/null -w "276=%{http_code}" http://127.0.0.1:7862/api/gen/file/276 && curl -s -o /dev/null -w " 277=%{http_code}" http://127.0.0.1:7862/api/gen/file/277 && curl -s -o /dev/null -w " 278=%{http_code}" http://127.0.0.1:7862/api/gen/file/278 && curl -s -o /dev/null -w " 283=%{http_code}" http://127.0.0.1:7862/api/gen/file/283'''),
]

for label, cmd in vcmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    print(f"  [{label}] {stdout.read().decode().strip()[:200]}")

client.close()
print("\n✅ DEPLOYED! http://122.51.205.94")