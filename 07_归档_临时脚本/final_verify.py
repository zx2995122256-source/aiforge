import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

sftp = client.open_sftp()
with sftp.file('/tmp/chpass2.py', 'w') as f:
    f.write('''
import sqlite3, bcrypt
c = sqlite3.connect("/home/ubuntu/aiforge/backend/data/aiforge.db")
pw = bcrypt.hashpw(b"zx4579561", bcrypt.gensalt()).decode()
c.execute("UPDATE users SET email=?, nickname=?, password=?, is_admin=1 WHERE id=1", ("xiaye", "XiaYe", pw))
c.commit()
r = c.execute("SELECT id, email, nickname, is_admin, points FROM users WHERE id=1").fetchone()
print("OK: id=%d email=%s nickname=%s admin=%d points=%d" % r)
c.close()
''')
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/chpass2.py', timeout=10)
print(stdout.read().decode().strip())
print("ERR:", stderr.read().decode().strip()[:200])

# Final full verify
stdin, stdout, stderr = client.exec_command('''
echo "=== Website ==="
curl -s http://127.0.0.1:7862/ | head -c 50
echo
echo "=== Models ==="
curl -s http://127.0.0.1:7862/api/gen/models | python3 -c "import sys,json; d=json.load(sys.stdin); v=list(d.get('video',{}).keys())[:5]; i=list(d.get('image',{}).keys())[:5]; print('Video:', v); print('Image:', i)"
echo "=== Pool ==="
curl -s http://127.0.0.1:7861/api/pool/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Accounts: {d[\"total_accounts\"]}, Active: {d[\"active_accounts\"]}, Points: {d[\"total_points\"]}')"
echo "=== Config check ==="
grep "POOL_MIN_TOTAL" /home/ubuntu/aiforge/backend/config.py
grep "res_scale" /home/ubuntu/aiforge/backend/api/generate.py
cat /home/ubuntu/oiioii/config.ini
''')
print(stdout.read().decode()[:1500])

client.close()