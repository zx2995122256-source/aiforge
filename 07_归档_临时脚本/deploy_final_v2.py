import paramiko, tarfile, io, os

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# ─── Package frontend ───
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w:gz') as tar:
    tar.add(r"C:\Users\Administrator\Documents\AiForge\frontend\dist", "dist")
    # Also add favicon separately
    tar.add(r"C:\Users\Administrator\Documents\AiForge\frontend\public\favicon.svg", "favicon.svg")
buf.seek(0)

sftp = client.open_sftp()
with sftp.file('/tmp/frontend.tar.gz', 'wb') as f:
    f.write(buf.getvalue())
sftp.close()
print("✅ Frontend packaged and uploaded")

# ─── Execute deployment ───
cmds = [
    # Extract frontend
    "rm -rf /tmp/frontend_extract && mkdir -p /tmp/frontend_extract && tar -xzf /tmp/frontend.tar.gz -C /tmp/frontend_extract",
    # Copy to aiforge
    "rm -rf /home/ubuntu/aiforge/dist && cp -r /tmp/frontend_extract/dist /home/ubuntu/aiforge/dist",
    # Copy favicon
    "cp /tmp/frontend_extract/favicon.svg /home/ubuntu/aiforge/dist/ 2>/dev/null",
    # Fix backend structure (in case previous deploy broke it)
    "rm -rf /home/ubuntu/aiforge/backend/api/api /home/ubuntu/aiforge/backend/core/core /home/ubuntu/aiforge/backend/models/models 2>/dev/null; echo 'cleaned'",
    # Verify generate.py has correct cost calc
    "grep 'res_scale' /home/ubuntu/aiforge/backend/api/generate.py && echo 'cost calc OK'",
    # Verify main.py has pool_watcher
    "grep '_pool_watcher' /home/ubuntu/aiforge/backend/main.py && echo 'watcher OK'",
    # Ensure oiioii config.ini has auto-replenish
    "grep 'enabled = true' /home/ubuntu/oiioii/config.ini && echo 'config OK'",
    # Restart services
    "sudo systemctl restart aiforge",
    "sleep 3",
    "sudo systemctl restart oiioii",
    "sleep 3",
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(f"  {out[:200]}")
    if err: print(f"  ERR: {err[:200]}")

# ─── Fix admin password ───
sftp = client.open_sftp()
with sftp.file('/tmp/fix_admin.py', 'w') as f:
    f.write("""
import sqlite3, hashlib, time
c = sqlite3.connect("/home/ubuntu/aiforge/backend/data/aiforge.db")
pw = hashlib.sha256(b"zx4579561").hexdigest()
now = time.time()
# Remove old and insert fresh admin
c.execute("DELETE FROM users WHERE id=1")
c.execute("INSERT INTO users (id,email,password_hash,nickname,points,role,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
          (1, "xiaye@aiforge.com", pw, "夏爷", 99999, "admin", now, now))
c.commit()
c.execute("UPDATE users SET role='admin' WHERE id=1")
c.commit()
for row in c.execute("SELECT id,email,nickname,role,points FROM users"):
    print(f"User: {row}")
c.close()
""")
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/fix_admin.py', timeout=10)
print("PWD:", stdout.read().decode().strip()[:200])

# ─── Verify everything ───
ver_cmds = [
    ("Website", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:7862/"),
    ("Models API", '''curl -s http://127.0.0.1:7862/api/gen/models | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'{len(d.get(chr(118)+chr(105)+chr(100)+chr(101)+chr(111),{}))} video, {len(d.get(chr(105)+chr(109)+chr(97)+chr(103)+chr(101),{}))} image models')" '''),
    ("Pool", '''curl -s http://127.0.0.1:7861/api/pool/status | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'{d[chr(116)+chr(111)+chr(116)+chr(97)+chr(108)+chr(95)+chr(97)+chr(99)+chr(99)+chr(111)+chr(117)+chr(110)+chr(116)+chr(115)]} accounts, {d[chr(116)+chr(111)+chr(116)+chr(97)+chr(108)+chr(95)+chr(112)+chr(111)+chr(105)+chr(110)+chr(116)+chr(115)]} points')" '''),
    ("Login", '''curl -s -X POST http://127.0.0.1:7862/api/auth/login -H "Content-Type: application/json" -d '{"email":"xiaye@aiforge.com","password":"zx4579561"}' | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'OK: role={d[chr(117)+chr(115)+chr(101)+chr(114)][chr(114)+chr(111)+chr(108)+chr(101)]}, points={d[chr(117)+chr(115)+chr(101)+chr(114)][chr(112)+chr(111)+chr(105)+chr(110)+chr(116)+chr(115)]}')" '''),
    ("Services", "sudo systemctl is-active aiforge && sudo systemctl is-active oiioii"),
    ("Image Gen Test", '''TOKEN=$(curl -s -X POST http://127.0.0.1:7862/api/auth/login -H "Content-Type: application/json" -d '{"email":"xiaye@aiforge.com","password":"zx4579561"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])"); curl -s -X POST http://127.0.0.1:7862/api/gen/image -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{"prompt":"test","model":"Flux","ratio":"1:1","resolution":"1K","reference_images":[]}' | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'Image gen: task_id={d.get(chr(116)+chr(97)+chr(115)+chr(107)+chr(95)+chr(105)+chr(100),\"?\")}, cost={d.get(chr(99)+chr(111)+chr(115)+chr(116),\"?\")}')" '''),
]

print("\n=== VERIFICATION ===")
for label, cmd in ver_cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    res = stdout.read().decode().strip()[:300]
    print(f"  [{label}] {res}")

client.close()
print("\n✅ DEPLOY COMPLETE!")