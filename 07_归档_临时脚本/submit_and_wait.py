import paramiko, time

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=15)

script = r'''
import requests, time

BASE = "http://127.0.0.1:7862"
r = requests.post(BASE + "/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 1. Check ref video
ref_url = "http://122.51.205.94/api/gen/refs/vidref_1780291543_8719f3fa.mp4"
r = requests.get(ref_url, timeout=10)
print(f"参考视频: {r.status_code} ({len(r.content)} bytes)")

# 2. Submit with ref
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
resp = r.json()
print(f"\n提交: task_id=#{resp.get('task_id','?')} oid=#{resp.get('oiioii_task_id','?')} status={resp.get('status','?')}")

oid = resp.get("oiioii_task_id", 0)

# 3. Wait for it
for i in range(30):
    time.sleep(5)
    r = requests.get(f"http://127.0.0.1:7861/api/task/{oid}", timeout=10)
    ps = r.json().get("status", "?")
    r2 = requests.get(BASE + f"/api/gen/task/{resp['task_id']}", headers=headers, timeout=10)
    ai = r2.json().get("status", "?")
    result = r2.json().get("result_url", "")
    print(f"  [{i*5+5}s] Pool={ps:10} Ai={ai:10} result={'✅' if result else '❌'}")
    if ps == "completed":
        # Get the file
        r3 = requests.get(BASE + f"/api/gen/file/{oid}", timeout=10)
        print(f"  ✅ 视频生成完成! {r3.status_code} ({len(r3.content)} bytes)")
        # Save a copy
        with open("/tmp/ref_video_result.mp4", "wb") as f:
            f.write(r3.content)
        print(f"  ✅ 已保存到 /tmp/ref_video_result.mp4")
        break

print("\n=== 最新任务 ===")
r = requests.get(BASE + "/api/gen/tasks", headers=headers, timeout=10)
for t in r.json()[-3:]:
    ref = "✅ref" if t.get("reference_video") else "❌"
    print(f"  #{t['id']} {t['status']:10} {ref} | {t.get('prompt','')[:30]}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/submit_wait_ref.py', 'w') as f:
    f.write(script)
sftp.close()

print("正在提交带参考视频的任务并等待完成...")
stdin, stdout, stderr = client.exec_command('python3 /tmp/submit_wait_ref.py', timeout=300)
out = stdout.read().decode()
err = stderr.read().decode()
print(out[:3000])
if err: print("ERR:", err[:500])

# Download the result
sftp = client.open_sftp()
try:
    with sftp.file('/tmp/ref_video_result.mp4', 'rb') as f:
        result = f.read()
    with open(r'C:\Users\Administrator\Documents\ref_video_result.mp4', 'wb') as f:
        f.write(result)
    print(f"\n✅ 视频已下载到 C:\\Users\\Administrator\\Documents\\ref_video_result.mp4 ({len(result)} bytes)")
except Exception as e:
    print(f"\n下载结果: {e}")

sftp.close()
client.close()