import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

script = r'''
import requests, sqlite3

BASE = "http://127.0.0.1:7862"
r = requests.post(BASE + "/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 1. AiForge task #37 (with ref video)
r = requests.get(BASE + "/api/gen/task/37", headers=headers, timeout=10)
t = r.json()
print(f"=== Task #37 (带参考视频) ===")
print(f"  status: {t['status']}")
print(f"  result_url: {t.get('result_url', 'N/A')}")
print(f"  prompt: {t.get('prompt','')[:50]}")
url = t.get('result_url', '')
if url:
    r2 = requests.get(BASE + url, timeout=10)
    print(f"  文件可访问: {r2.status_code} ({len(r2.content)} bytes)")
    print(f"  Content-Type: {r2.headers.get('content-type','?')}")

# 2. Check OiioiiPool task #297 (the one with ref)
r = requests.get("http://127.0.0.1:7861/api/task/297", timeout=10)
t2 = r.json()
print(f"\n=== OiioiiPool #297 ===")
print(f"  status: {t2.get('status','?')}")
print(f"  model: {t2.get('model','?')}")
# Check if it has video output
r3 = requests.get("http://127.0.0.1:7861/api/task/297/download", timeout=15)
print(f"  download: {r3.status_code} ({len(r3.content)} bytes)")
if len(r3.content) > 100:
    print(f"  ✅ 视频文件存在!")
else:
    print(f"  内容: {r3.text[:200]}")

# 3. Check OiioiiPool generated files
import subprocess
r = subprocess.run(["find", "/home/ubuntu/oiioii/data/output/", "-name", "*297*", "-o", "-name", "*298*"], capture_output=True, text=True, timeout=10)
print(f"\n=== 生成的文件 ===")
print(r.stdout[:500])

# 4. Task #37 logs
r = subprocess.run(["journalctl", "-u", "aiforge", "--since", "5 min ago", "--no-pager"], capture_output=True, text=True, timeout=10)
for l in r.stdout.split("\n"):
    if "#37" in l and "[Poll]" in l:
        print(f"  {l.strip()[:120]}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/check_video_output.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/check_video_output.py', timeout=15)
print(stdout.read().decode()[:2500])
err = stderr.read().decode()[:300]
if err: print("ERR:", err)

client.close()