import paramiko, tarfile, io

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Package frontend + backend
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w:gz') as tar:
    tar.add(r"C:\Users\Administrator\Documents\AiForge\frontend\dist", "dist")
    tar.add(r"C:\Users\Administrator\Documents\AiForge\backend\api\generate.py", "backend/api/generate.py")
buf.seek(0)

sftp = client.open_sftp()
with sftp.file('/tmp/deploy_timeout_fix.tar.gz', 'wb') as f:
    f.write(buf.getvalue())
sftp.close()
print("Uploaded")

# Deploy
cmds = [
    "rm -rf /tmp/df && mkdir -p /tmp/df && tar -xzf /tmp/deploy_timeout_fix.tar.gz -C /tmp/df",
    "cp /tmp/df/backend/api/generate.py /home/ubuntu/aiforge/backend/api/generate.py",
    "rm -rf /home/ubuntu/aiforge/dist && mkdir -p /home/ubuntu/aiforge && cp -r /tmp/df/dist /home/ubuntu/aiforge/dist",
    "sudo systemctl restart aiforge && sleep 3",
]
for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
    out = stdout.read().decode().strip()
    if out: print(out[:200])

# Test
script = r'''
import requests, time

BASE = "http://127.0.0.1:7862"

# Login
r = requests.post(BASE + "/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# Verify the reference video URL is accessible
ref_url = "http://122.51.205.94/api/gen/refs/vidref_1780291543_8719f3fa.mp4"
r = requests.get(ref_url, timeout=10)
print(f"Ref video accessible: {r.status_code} ({len(r.content)} bytes)")

# Submit the task with reference video
print("\nSubmitting video with ref...")
payload = {
    "prompt": "生成一只小猫",
    "model": "Gemini Omni",
    "ratio": "16:9",
    "resolution": "720p",
    "duration": 5,
    "reference_images": [],
    "reference_video": ref_url
}
r = requests.post(BASE + "/api/gen/video", json=payload, headers=headers, timeout=15)
print(f"Submit: {r.status_code}")
resp = r.json()
print(f"Task: #{resp.get('task_id','?')}, OiioiiPool: #{resp.get('oiioii_task_id','?')}")
print(f"Status: {resp.get('status','?')}")

# Check after 10 seconds
time.sleep(10)
r2 = requests.get(BASE + f"/api/gen/task/{resp['task_id']}", headers=headers, timeout=10)
print(f"\nAfter 10s: status={r2.json().get('status','?')}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/submit_ref.py', 'w') as f:
    f.write(script)
sftp.close()

print("\n=== Deploy & Submit ===")
stdin, stdout, stderr = client.exec_command('python3 /tmp/submit_ref.py', timeout=60)
print(stdout.read().decode()[:1000])
err = stderr.read().decode()[:500]
if err: print("ERR:", err)

client.close()