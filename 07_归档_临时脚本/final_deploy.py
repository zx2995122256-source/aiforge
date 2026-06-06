import paramiko, tarfile, io, os

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# 1. Upload frontend
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w:gz') as tar:
    tar.add(r"C:\Users\Administrator\Documents\AiForge\frontend\dist", "frontend/dist")

buf.seek(0)
sftp = client.open_sftp()
with sftp.file('/tmp/frontend.tar.gz', 'wb') as f:
    f.write(buf.getvalue())
sftp.close()

# 2. Deploy frontend
cmds = [
    "rm -rf /home/ubuntu/frontend",
    "tar -xzf /tmp/frontend.tar.gz -C /home/ubuntu/",
    "rm -rf /home/ubuntu/aiforge/dist",
    "cp -r /home/ubuntu/frontend/dist /home/ubuntu/aiforge/",
    # Fix leftover nested dirs
    "rm -rf /home/ubuntu/aiforge/backend/api/api /home/ubuntu/aiforge/backend/core/core /home/ubuntu/aiforge/backend/models/models 2>/dev/null; echo cleaned",
    # Restart services
    "sudo systemctl restart aiforge",
    "sleep 3",
    "sudo systemctl restart oiioii",
    "sleep 2",
]

for cmd in cmds:
    print(f">>> {cmd[:80]}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out.strip(): print(out.strip()[:300])
    if err.strip(): print(f"  ERR: {err.strip()[:300]}")

# 3. Change password 
pw_cmd = """python3 -c "
import sqlite3, bcrypt, json
c = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
pw = bcrypt.hashpw(b'zx4579561', bcrypt.gensalt()).decode()
c.execute('UPDATE users SET email=?, nickname=?, password=?, is_admin=1 WHERE id=1', ('xiaye', '夏爷', pw))
c.commit()
r = c.execute('SELECT id, email, nickname, is_admin, points FROM users WHERE id=1').fetchone()
print(json.dumps({'id':r[0],'email':r[1],'nickname':r[2],'admin':bool(r[3]),'points':r[4]}))
c.close()
"'''
stdin, stdout, stderr = client.exec_command(pw_cmd, timeout=10)
print("PWD:", stdout.read().decode().strip(), stderr.read().decode().strip()[:300])

# 4. Verify
ver_cmds = [
    "curl -s http://127.0.0.1:7862/ | head -c 100",
    "curl -s http://127.0.0.1:7862/api/gen/models | python3 -c \"import sys,json; d=json.load(sys.stdin); print('Models OK:', len(list(d.get('video',{}).keys())), 'video,', len(list(d.get('image',{}).keys())), 'image models')\"",
    "curl -s http://127.0.0.1:7861/api/pool/status | python3 -c \"import sys,json; d=json.load(sys.stdin); print(f'Pool: {d[chr(116)+chr(111)+chr(116)+chr(97)+chr(108)+chr(95)+chr(97)+chr(99)+chr(99)+chr(111)+chr(117)+chr(110)+chr(116)+chr(115)]} accounts, {d[chr(116)+chr(111)+chr(116)+chr(97)+chr(108)+chr(95)+chr(112)+chr(111)+chr(105)+chr(110)+chr(116)+chr(115)]} points')\"",
    "sudo systemctl is-active aiforge",
    "sudo systemctl is-active oiioii",
]

for cmd in ver_cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    print(f"VERIFY: {stdout.read().decode().strip()[:200]}")

client.close()
print("===== ALL DONE =====")
