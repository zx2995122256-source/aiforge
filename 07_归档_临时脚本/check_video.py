import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# 1. Check actual video file size
stdin, stdout, stderr = client.exec_command('ls -lh /home/ubuntu/oiioii/data/output/2026-06-01/*.mp4 2>/dev/null | head -5')
print("=== VIDEO FILES ===")
print(stdout.read().decode()[:500])

# 2. Check how proxy works - what URL is the video requesting?
stdin, stdout, stderr = client.exec_command('''python3 -c "
import sqlite3
c = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
# Find the latest completed video with task_id
rows = c.execute('SELECT id, oiioii_task_id, user_id, status FROM tasks WHERE task_type=\\'video\\' AND status=\\'completed\\' ORDER BY id DESC LIMIT 5').fetchall()
for r in rows:
    print(f'id={r[0]}, oiioii_id={r[1]}, user={r[2]}, {r[3]}')
c.close()
" ''')
print("\n=== LATEST VIDEOS ===")
print(stdout.read().decode()[:500])

# 3. Check OiioiiPool's file serving mechanism
stdin, stdout, stderr = client.exec_command('curl -s -o /dev/null -w "%{http_code} %{speed_download}" http://127.0.0.1:7861/api/task/275/download', timeout=15)
print(f"\n=== OiioiiPool direct download speed: {stdout.read().decode()[:200]}")

# 4. Check AiForge backend proxy speed
stdin, stdout, stderr = client.exec_command(
    """curl -s -X POST http://127.0.0.1:7862/api/auth/login -H "Content-Type: application/json" -d '{"email":"xiaye@aiforge.com","password":"zx4579561"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])" """,
    timeout=10
)
token = stdout.read().decode().strip()

stdin, stdout, stderr = client.exec_command(
    f'curl -s -o /dev/null -w "%{{http_code}} %{{speed_download}} %{{size_download}}" -H "Authorization: Bearer {token}" http://127.0.0.1:7862/api/gen/file/275', timeout=15
)
print(f"AiForge proxy download: {stdout.read().decode()[:200]}")

# 5. Check response header sizes  
stdin, stdout, stderr = client.exec_command(
    f'curl -s -D - -o /dev/null -H "Authorization: Bearer {token}" http://127.0.0.1:7862/api/gen/file/275 2>&1 | head -30', timeout=15
)
print(f"\n=== HEADERS ===")
print(stdout.read().decode()[:500])

client.close()