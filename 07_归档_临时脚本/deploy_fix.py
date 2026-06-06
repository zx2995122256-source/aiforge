import paramiko, tarfile, io, os

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Check extracted files
stdin, stdout, stderr = client.exec_command('ls -la /home/ubuntu/ && echo "===" && ls -la /home/ubuntu/dist/ 2>/dev/null | head -5 && echo "===" && ls -la /home/ubuntu/backend/ 2>/dev/null | head -5')
print(stdout.read().decode()[:1000])

# Fix file structure: move everything to right places
commands = [
    "ls /home/ubuntu/dist/ | head -3",
    # Move frontend to aiforge
    "rm -rf /home/ubuntu/aiforge/dist",
    "mv /home/ubuntu/dist /home/ubuntu/aiforge/dist",
    # Move backend to aiforge  
    "rm -rf /home/ubuntu/aiforge/backend",
    "mv /home/ubuntu/backend /home/ubuntu/aiforge/backend",
    # The Oiioii files are under /home/ubuntu/oiioii/, we already overwrote them
    "ls /home/ubuntu/oiioii/main.py 2>/dev/null && echo 'oiioii main OK'",
    # Set config.ini
    "printf '[AUTO_REPLENISH]\nenabled = true\nmin_total_points = 50000\nmin_active_accounts = 3\ncheck_interval = 300\n' > /home/ubuntu/oiioii/config.ini",
    "cat /home/ubuntu/oiioii/config.ini",
    # Check generate.py has new cost calc
    "grep '_calc_video_cost' /home/ubuntu/aiforge/backend/api/generate.py",
    "grep 'res_scale' /home/ubuntu/aiforge/backend/api/generate.py",
    # Check main.py has pool_watcher
    "grep '_pool_watcher' /home/ubuntu/aiforge/backend/main.py",
    "grep 'POOL_MIN_TOTAL' /home/ubuntu/aiforge/backend/config.py",
    # Restart services
    "sudo systemctl restart aiforge",
    "sleep 2",
    "sudo systemctl restart oiioii",
    "sleep 2",
]

for cmd in commands:
    print(f">>> {cmd[:80]}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out.strip(): print(out.strip()[:300])
    if err.strip(): print(f"  ERR: {err.strip()[:200]}")

# ─── Change password ───
pw_script = "import sqlite3, bcrypt; c = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db'); pw = bcrypt.hashpw(b'zx4579561', bcrypt.gensalt()).decode(); c.execute('UPDATE users SET email=?, nickname=?, password=?, is_admin=1 WHERE id=1', ('xiaye', '夏爷', pw)); c.commit(); r = c.execute('SELECT id,email,nickname,is_admin FROM users WHERE id=1').fetchone(); print(f'id={r[0]} email={r[1]} nickname={r[2]} admin={r[3]}'); c.close()"
stdin, stdout, stderr = client.exec_command(f'python3 -c "{pw_script}"')
print("PWD:", stdout.read().decode().strip())

# ─── Verify ───
ver_cmds = [
    "curl -s http://127.0.0.1:7862/api/user/admin/stats",
    "curl -s http://127.0.0.1:7861/api/pool/status | python3 -c \"import sys,json; d=json.load(sys.stdin); print(f'Pool: {d[chr(34)+chr(116)+chr(111)+chr(116)+chr(97)+chr(108)+chr(95)+chr(97)+chr(99)+chr(99)+chr(111)+chr(117)+chr(110)+chr(116)+chr(115)+chr(34)]} accounts, {d[chr(34)+chr(116)+chr(111)+chr(116)+chr(97)+chr(108)+chr(95)+chr(112)+chr(111)+chr(105)+chr(110)+chr(116)+chr(115)+chr(34)]} points')\"",
    "curl -s http://127.0.0.1:7862/api/gen/models | python3 -c \"import sys,json; d=json.load(sys.stdin); print('Models OK:', list(d.get('video',{}).keys())[:5])\"",
]

for cmd in ver_cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    print(stdout.read().decode()[:300])

client.close()
print("===== DONE =====")
