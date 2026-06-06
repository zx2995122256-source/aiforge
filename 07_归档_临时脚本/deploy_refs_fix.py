import paramiko, tarfile, io

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Package
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w:gz') as tar:
    tar.add(r"C:\Users\Administrator\Documents\AiForge\frontend\dist", "dist")
    tar.add(r"C:\Users\Administrator\Documents\AiForge\backend\api\generate.py", "backend/api/generate.py")
buf.seek(0)

sftp = client.open_sftp()
with sftp.file('/tmp/fix_refs.tar.gz', 'wb') as f:
    f.write(buf.getvalue())
sftp.close()
print("Uploaded")

# Deploy
cmds = [
    "rm -rf /tmp/fr && mkdir -p /tmp/fr && tar -xzf /tmp/fix_refs.tar.gz -C /tmp/fr",
    "cp /tmp/fr/backend/api/generate.py /home/ubuntu/aiforge/backend/api/generate.py",
    "rm -rf /home/ubuntu/aiforge/dist && cp -r /tmp/fr/dist /home/ubuntu/aiforge/dist",
    "sudo systemctl restart aiforge && sleep 3",
]
for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
    out = stdout.read().decode().strip()
    if out: print(out[:200])

# Test refs
script = r'''
import requests
# Test refs route
r = requests.get("http://127.0.0.1:7862/api/gen/refs/vidref_1780291543_8719f3fa.mp4", timeout=10)
print(f"Refs route: {r.status_code}, {len(r.content)} bytes")
if len(r.content) > 10000:
    print("✅ Refs serve correctly!")

# Also test the submitted task #37
r2 = requests.post("http://127.0.0.1:7862/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r2.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

r3 = requests.get("http://127.0.0.1:7862/api/gen/task/37", headers=headers, timeout=10)
print(f"\nTask #37: {r3.json().get('status','?')}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_refs.py', 'w') as f:
    f.write(script)
sftp.close()

print("\n=== Verify ===")
stdin, stdout, stderr = client.exec_command('python3 /tmp/test_refs.py', timeout=15)
print(stdout.read().decode()[:500])

# Also submit a quick task without ref to show speed
script2 = r'''
import requests, time
BASE = "http://127.0.0.1:7862"
r = requests.post(BASE + "/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# Submit without ref
r = requests.post(BASE + "/api/gen/video", json={
    "prompt": "一只可爱的橘猫在阳光下打哈欠",
    "model": "Gemini Omni",
    "ratio": "16:9", "resolution": "720p", "duration": 5,
    "reference_images": [], "reference_video": ""
}, headers=headers, timeout=15)
print(f"\nNo-ref video: status={r.json().get('status','?')} task_id=#{r.json().get('task_id','?')}")

# Wait a bit
time.sleep(15)
r2 = requests.get(BASE + f"/api/gen/task/{r.json()['task_id']}", headers=headers, timeout=10)
print(f"After 15s: {r2.json().get('status','?')}")
if r2.json().get('status') == 'completed':
    print(f"  Result: {r2.json().get('result_url','?')}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_no_ref.py', 'w') as f:
    f.write(script2)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/test_no_ref.py', timeout=60)
print(stdout.read().decode()[:500])

client.close()