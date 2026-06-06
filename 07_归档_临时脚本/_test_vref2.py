import paramiko, time

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

# Submit video gen with video ref directly via API
script = r'''
import requests, time

BASE = "http://127.0.0.1:7861"

video_ref_url = "/output/refs/vidref_1780353007_909.mp4"

print("=== TEST: Video gen with ref video (Gemini Omni) ===")
r = requests.post(f"{BASE}/api/generate_video", json={
    "prompt": "a person walking in a forest, cinematic lighting",
    "model": "Gemini Omni",
    "ratio": "16:9",
    "duration": 6,
    "resolution": "720p",
    "reference_video": video_ref_url
})
print(f"Submit: {r.status_code} {r.text[:200]}")
vid_task = r.json()
vid_task_id = vid_task.get("task_id")

if vid_task_id:
    for i in range(36):
        time.sleep(10)
        r = requests.get(f"{BASE}/api/task/{vid_task_id}", timeout=5)
        t = r.json()
        status = t.get("status", "")
        uri = str(t.get("result_uri", ""))[:50]
        err = str(t.get("error", ""))[:60]
        print(f"  [{i*10}s] task {vid_task_id}: status={status} uri={uri} error={err}")
        if status in ("completed", "failed"):
            break

print("\n=== DONE ===")
'''

sftp = ssh.open_sftp()
with sftp.open('/tmp/test_vref2.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('nohup python3 -u /tmp/test_vref2.py > /tmp/test_vref2.log 2>&1 & echo $!')
pid = stdout.read().decode().strip()
print(f"Started, PID: {pid}")
time.sleep(10)

stdin, stdout, stderr = ssh.exec_command('cat /tmp/test_vref2.log')
log = stdout.read().decode()
print(log[:500] if log else "(no output yet)")

ssh.close()
