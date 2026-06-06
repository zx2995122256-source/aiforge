import paramiko, tarfile, io, os

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Package frontend dist
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w:gz') as tar:
    tar.add(r"C:\Users\Administrator\Documents\AiForge\frontend\dist", "dist")
buf.seek(0)

sftp = client.open_sftp()
with sftp.file('/tmp/frontend_final.tar.gz', 'wb') as f:
    f.write(buf.getvalue())
sftp.close()
print("Uploaded")

cmds = [
    "rm -rf /tmp/dist && tar -xzf /tmp/frontend_final.tar.gz -C /tmp",
    "rm -rf /home/ubuntu/aiforge/dist",
    "cp -r /tmp/dist /home/ubuntu/aiforge/dist",
    "sudo systemctl restart aiforge && sleep 2",
    "sudo systemctl restart oiioii && sleep 2",
]

for cmd in cmds:
    print(f"  {cmd[:60]}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(f"    {out[:200]}")
    if err: print(f"    ERR: {err[:200]}")

# Verify
ver_cmds = [
    ("Website", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:7862/"),
    ("Login", """curl -s -X POST http://127.0.0.1:7862/api/auth/login -H "Content-Type: application/json" -d '{"email":"xiaye@aiforge.com","password":"zx4579561"}' | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'OK role={d[chr(117)+chr(115)+chr(101)+chr(114)][chr(114)+chr(111)+chr(108)+chr(101)]} pts={d[chr(117)+chr(115)+chr(101)+chr(114)][chr(112)+chr(111)+chr(105)+chr(110)+chr(116)+chr(115)]}')" """),
    ("Services", "echo 'AiForge='$(sudo systemctl is-active aiforge)' Oiioii='$(sudo systemctl is-active oiioii)"),
    ("Assets", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:7862/api/gen/file/271 && curl -s -o /dev/null -w ' %{http_code}' http://127.0.0.1:7862/api/gen/file/272 && curl -s -o /dev/null -w ' %{http_code}' http://127.0.0.1:7862/api/gen/file/273 && curl -s -o /dev/null -w ' %{http_code}' http://127.0.0.1:7862/api/gen/file/275"),
]

print("\n=== VERIFY ===")
for label, cmd in ver_cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    res = stdout.read().decode().strip()[:200]
    print(f"  [{label}] {res}")

client.close()
print("\n✅ ALL DONE!")