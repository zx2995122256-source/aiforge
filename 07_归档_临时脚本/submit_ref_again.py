import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

script = r'''
import requests, time

BASE = "http://127.0.0.1:7862"
r = requests.post(BASE + "/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# Check tasks list
r = requests.get(BASE + "/api/gen/tasks", headers=headers, timeout=10)
tasks = r.json()
print(f"当前任务数: {len(tasks)}")
for t in tasks[-5:]:
    print(f"  #{t['id']} {t.get('task_type','')} {t.get('status','')} ref_video={'✅' if t.get('reference_video') else '❌'} | {t.get('prompt','')[:30]}")

# Re-submit with reference video
ref_url = "http://122.51.205.94/api/gen/refs/vidref_1780291543_8719f3fa.mp4"
print(f"\n参考视频URL: {ref_url}")

# Verify ref accessible
r = requests.get(ref_url, timeout=10)
print(f"参考视频可访问: {r.status_code} ({len(r.content)} bytes)")

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
print(f"\n提交结果: {r.status_code}")
resp = r.json()
print(f"  task_id: #{resp.get('task_id','?')}")
print(f"  oiioii_task_id: #{resp.get('oiioii_task_id','?')}")
print(f"  status: {resp.get('status','?')}")

# Check OiioiiPool
oid = resp.get('oiioii_task_id', 0)
r2 = requests.get(f"http://127.0.0.1:7861/api/task/{oid}", timeout=10)
print(f"\nOiioiiPool #{oid}: {r2.json().get('status','?')}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/submit_with_ref.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/submit_with_ref.py', timeout=30)
print(stdout.read().decode()[:1500])
err = stderr.read().decode()[:300]
if err: print("ERR:", err)

client.close()