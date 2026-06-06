import paramiko, tarfile, os, io, json

# ─── 需要部署的内容 ───
FRONTEND_DIR = r"C:\Users\Administrator\Documents\AiForge\dist"
BACKEND_FILES = [
    (r"C:\Users\Administrator\Documents\AiForge\backend\main.py", "backend/main.py"),
    (r"C:\Users\Administrator\Documents\AiForge\backend\config.py", "backend/config.py"),
]
BACKEND_DIRS = [
    (r"C:\Users\Administrator\Documents\AiForge\backend\api", "backend/api"),
    (r"C:\Users\Administrator\Documents\AiForge\backend\models", "backend/models"),
    (r"C:\Users\Administrator\Documents\AiForge\backend\core", "backend/core"),
]

OIIOII_DIRS = [
    (r"C:\Users\Administrator\Documents\OiioiiPool\api", "oiioii/api"),
    (r"C:\Users\Administrator\Documents\OiioiiPool\core", "oiioii/core"),
    (r"C:\Users\Administrator\Documents\OiioiiPool\main.py", "oiioii/main.py"),
    (r"C:\Users\Administrator\Documents\OiioiiPool\config.py", "oiioii/config.py"),
    (r"C:\Users\Administrator\Documents\OiioiiPool\requirements.txt", "oiioii/requirements.txt"),
]

# SSH 连接
key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# ─── 创建 tar 包 ───
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w:gz') as tar:
    # 前端
    for root, dirs, files in os.walk(FRONTEND_DIR):
        for f in files:
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, os.path.dirname(FRONTEND_DIR))
            tar.add(fp, rel)
    # 后端文件
    for src, dst in BACKEND_FILES:
        tar.add(src, dst)
    for src, dst in BACKEND_DIRS:
        for root, dirs, files in os.walk(src):
            for f in files:
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, os.path.dirname(src))
                tar.add(fp, os.path.join(dst, rel))
    # OiioiiPool
    for src, dst in OIIOII_DIRS:
        if os.path.isfile(src):
            tar.add(src, dst)
        else:
            for root, dirs, files in os.walk(src):
                for f in files:
                    fp = os.path.join(root, f)
                    rel = os.path.relpath(fp, os.path.dirname(src))
                    tar.add(fp, os.path.join(dst, rel))

buf.seek(0)
print(f"Tar size: {len(buf.getvalue()) / 1024:.1f} KB")

# ─── 上传到服务器 ───
sftp = client.open_sftp()
with sftp.file('/tmp/deploy.tar.gz', 'wb') as f:
    f.write(buf.getvalue())
sftp.close()
print("Uploaded /tmp/deploy.tar.gz")

# ─── 执行部署 ───
commands = [
    # 解压
    "cd /home/ubuntu && tar -xzf /tmp/deploy.tar.gz",
    # 复制前端
    "rm -rf /home/ubuntu/aiforge/dist",
    "cp -r /home/ubuntu/dist /home/ubuntu/aiforge/",
    # 复制后端
    "rm -rf /home/ubuntu/aiforge/backend",
    "cp -r /home/ubuntu/backend /home/ubuntu/aiforge/",
    # 复制 OiioiiPool
    "rm -rf /home/ubuntu/oiioii/__pycache__ /home/ubuntu/oiioii/api/__pycache__ /home/ubuntu/oiioii/core/__pycache__",
    "cp -r /home/ubuntu/oiioii/api /home/ubuntu/oiioii/",
    "cp -r /home/ubuntu/oiioii/core /home/ubuntu/oiioii/",
    "cp /home/ubuntu/oiioii/main.py /home/ubuntu/oiioii/",
    "cp /home/ubuntu/oiioii/config.py /home/ubuntu/oiioii/",
    "cp /home/ubuntu/oiioii/requirements.txt /home/ubuntu/oiioii/",
    # 设置 config.ini
    "cat > /home/ubuntu/oiioii/config.ini << 'CFGEOF'\n[AUTO_REPLENISH]\nenabled = true\nmin_total_points = 50000\nmin_active_accounts = 3\ncheck_interval = 300\nCFGEOF",
    # 重启服务
    "sudo systemctl restart aiforge",
    "sudo systemctl restart oiioii",
    "sleep 3",
]

for cmd in commands:
    print(f">>> {cmd[:80]}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out and out.strip(): print(out.strip()[:200])
    if err and err.strip(): print(f"  ERR: {err.strip()[:200]}")

# ─── 改管理员密码 ───
script = '''
import sqlite3, bcrypt
c = sqlite3.connect("/home/ubuntu/aiforge/backend/data/aiforge.db")
pw = bcrypt.hashpw(b"zx4579561", bcrypt.gensalt()).decode()
c.execute("UPDATE users SET email=?, nickname=?, password=?, is_admin=1 WHERE id=1", ("xiaye", "夏爷", pw))
c.commit()
row = c.execute("SELECT id, email, nickname, is_admin, points FROM users WHERE id=1").fetchone()
print(f"OK: id={row[0]}, email={row[1]}, nickname={row[2]}, admin={row[3]}, points={row[4]}")
c.close()
'''
stdin, stdout, stderr = client.exec_command(f'python3 -c {repr(script)}')
print("PASSWORD:", stdout.read().decode().strip())

# ─── 验证服务 ───
stdin, stdout, stderr = client.exec_command('''curl -s http://127.0.0.1:7862/api/user/admin/stats && echo "---" && curl -s http://127.0.0.1:7861/api/pool/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Pool: {d[\"total_accounts\"]} accounts, {d[\"total_points\"]} points')" && echo "---" && curl -s http://127.0.0.1:7862/ | head -c 100''')
print("VERIFY:", stdout.read().decode()[:500])

client.close()
print("\n===== DEPLOY DONE =====")
