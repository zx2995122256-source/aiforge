import paramiko, tarfile, io, os

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# ─── Package everything ───
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w:gz') as tar:
    # Frontend dist
    tar.add(r"C:\Users\Administrator\Documents\AiForge\frontend\dist", "aiforge/dist")
    # Favicon
    tar.add(r"C:\Users\Administrator\Documents\AiForge\frontend\public\favicon.svg", "aiforge/favicon.svg")
    # Backend files (only the ones we changed)
    tar.add(r"C:\Users\Administrator\Documents\AiForge\backend\api\generate.py", "backend/api/generate.py")
    tar.add(r"C:\Users\Administrator\Documents\AiForge\backend\api\auth.py", "backend/api/auth.py")
    tar.add(r"C:\Users\Administrator\Documents\AiForge\backend\main.py", "backend/main.py")
    tar.add(r"C:\Users\Administrator\Documents\AiForge\backend\config.py", "backend/config.py")
    tar.add(r"C:\Users\Administrator\Documents\AiForge\backend\models\db.py", "backend/models/db.py")
buf.seek(0)

sftp = client.open_sftp()
with sftp.file('/tmp/deploy.tar.gz', 'wb') as f:
    f.write(buf.getvalue())
sftp.close()
print("✅ All files packaged")

# ─── Deploy ───
cmds = [
    # Extract
    "rm -rf /tmp/deploy_extract && mkdir -p /tmp/deploy_extract && tar -xzf /tmp/deploy.tar.gz -C /tmp/deploy_extract",
    # Frontend
    "rm -rf /home/ubuntu/aiforge/dist && cp -r /tmp/deploy_extract/aiforge/dist /home/ubuntu/aiforge/dist",
    "cp /tmp/deploy_extract/aiforge/favicon.svg /home/ubuntu/aiforge/dist/ 2>/dev/null",
    # Backend files
    "cp /tmp/deploy_extract/backend/api/generate.py /home/ubuntu/aiforge/backend/api/generate.py",
    "cp /tmp/deploy_extract/backend/api/auth.py /home/ubuntu/aiforge/backend/api/auth.py",
    "cp /tmp/deploy_extract/backend/main.py /home/ubuntu/aiforge/backend/main.py",
    "cp /tmp/deploy_extract/backend/config.py /home/ubuntu/aiforge/backend/config.py",
    "cp /tmp/deploy_extract/backend/models/db.py /home/ubuntu/aiforge/backend/models/db.py",
    # Fix nested dirs
    "rm -rf /home/ubuntu/aiforge/backend/api/api /home/ubuntu/aiforge/backend/core/core /home/ubuntu/aiforge/backend/models/models 2>/dev/null",
    # Verify critical files
    "grep 'res_scale' /home/ubuntu/aiforge/backend/api/generate.py && echo '✅ cost calc'",
    "grep '_pool_watcher' /home/ubuntu/aiforge/backend/main.py && echo '✅ watcher'",
    "grep 'POOL_MIN_TOTAL' /home/ubuntu/aiforge/backend/config.py && echo '✅ config'",
    # Auto-replenish config
    "cat > /home/ubuntu/oiioii/config.ini << 'CFGEOF'\n[AUTO_REPLENISH]\nenabled = true\nmin_total_points = 50000\nmin_active_accounts = 3\ncheck_interval = 300\nCFGEOF",
    # Restart
    "sudo systemctl restart aiforge && sleep 3 && sudo systemctl restart oiioii && sleep 3",
]

for cmd in cmds:
    print(f"  RUN: {cmd[:80]}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(f"    {out[:300]}")
    if err: print(f"    ERR: {err[:200]}")

# ─── Fix admin ───
sftp = client.open_sftp()
with sftp.file('/tmp/fix_admin.py', 'w') as f:
    f.write("""
import sqlite3, hashlib, time
c = sqlite3.connect("/home/ubuntu/aiforge/backend/data/aiforge.db")
pw = hashlib.sha256(b"zx4579561").hexdigest()
now = time.time()
c.execute("DELETE FROM users WHERE id=1")
c.execute("INSERT INTO users (id,email,password_hash,nickname,points,role,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
          (1, "xiaye@aiforge.com", pw, "夏爷", 99999, "admin", now, now))
c.commit()
for row in c.execute("SELECT id,email,nickname,role,points FROM users"):
    print(f"User: {row}")
c.close()
""")
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/fix_admin.py', timeout=10)
print(f"  PWD: {stdout.read().decode().strip()[:200]}")
err = stderr.read().decode().strip()
if err: print(f"  PWD ERR: {err[:200]}")

# ─── Full verify ───
print("\n=== VERIFICATION ===")
ver_cmds = [
    ("Website", '''curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:7862/'''),
    ("Models", '''curl -s http://127.0.0.1:7862/api/gen/models | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'{len(list(d.get(chr(118)+chr(105)+chr(100)+chr(101)+chr(111),{}).keys()))} video, {len(list(d.get(chr(105)+chr(109)+chr(97)+chr(103)+chr(101),{}).keys()))} image')"'''),
    ("Pool", '''curl -s http://127.0.0.1:7861/api/pool/status | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'{d[chr(116)+chr(111)+chr(116)+chr(97)+chr(108)+chr(95)+chr(97)+chr(99)+chr(99)+chr(111)+chr(117)+chr(110)+chr(116)+chr(115)]} acc, {d[chr(116)+chr(111)+chr(116)+chr(97)+chr(108)+chr(95)+chr(112)+chr(111)+chr(105)+chr(110)+chr(116)+chr(115)]} pts')"'''),
    ("Login", '''curl -s -X POST http://127.0.0.1:7862/api/auth/login -H "Content-Type: application/json" -d '{"email":"xiaye@aiforge.com","password":"zx4579561"}' | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'role={d[chr(117)+chr(115)+chr(101)+chr(114)][chr(114)+chr(111)+chr(108)+chr(101)]} pts={d[chr(117)+chr(115)+chr(101)+chr(114)][chr(112)+chr(111)+chr(105)+chr(110)+chr(116)+chr(115)]}')"'''),
    ("Services", '''echo "aiforge=$(sudo systemctl is-active aiforge) oiioii=$(sudo systemctl is-active oiioii)"'''),
    ("Gen Img", '''TOKEN=$(curl -s -X POST http://127.0.0.1:7862/api/auth/login -H "Content-Type: application/json" -d '{"email":"xiaye@aiforge.com","password":"zx4579561"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])"); curl -s -X POST http://127.0.0.1:7862/api/gen/image -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{"prompt":"test","model":"Flux","ratio":"1:1","resolution":"1K","reference_images":[]}' | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'task={d.get(chr(116)+chr(97)+chr(115)+chr(107)+chr(95)+chr(105)+chr(100),\"?\")} cost={d.get(chr(99)+chr(111)+chr(115)+chr(116),\"?\")}')"'''),
    ("Gen Vid", '''TOKEN=$(curl -s -X POST http://127.0.0.1:7862/api/auth/login -H "Content-Type: application/json" -d '{"email":"xiaye@aiforge.com","password":"zx4579561"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])"); curl -s -X POST http://127.0.0.1:7862/api/gen/video -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{"prompt":"test","model":"Vidu Q2","ratio":"16:9","resolution":"720p","duration":5,"reference_images":[],"reference_video":""}' | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'task={d.get(chr(116)+chr(97)+chr(115)+chr(107)+chr(95)+chr(105)+chr(100),\"?\")} cost={d.get(chr(99)+chr(111)+chr(115)+chr(116),\"?\")}')"'''),
]

for label, cmd in ver_cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    res = stdout.read().decode().strip()[:200]
    print(f"  [{label}] {res}")

client.close()
print("\n✅ ALL DONE!")