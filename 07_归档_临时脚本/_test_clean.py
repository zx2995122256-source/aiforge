import paramiko, time

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

script = r'''
import requests, time, os, struct, zlib, json

BASE = "http://127.0.0.1:7861"

# 1. Use an EXISTING real ref image (the ones from your actual usage)
refs_dir = "/home/ubuntu/oiioii/data/output/refs/"
ref_images = [f for f in os.listdir(refs_dir) if f.startswith("ref_") and f.endswith(".png") and os.path.getsize(os.path.join(refs_dir, f)) > 50000]
if ref_images:
    latest_ref = ref_images[-1]
    ref_path = os.path.join(refs_dir, latest_ref)
    ref_size = os.path.getsize(ref_path)
    print(f"Using real ref image: {latest_ref} ({ref_size} bytes)")
    
    # Re-upload it to get a fresh URL
    with open(ref_path, "rb") as f:
        ref_data = f.read()
    r = requests.post(f"{BASE}/api/upload_ref", files={"file": (latest_ref, ref_data)})
    print(f"Upload: {r.status_code}")
    ref_url = r.json().get("url", "")
    print(f"Ref URL: {ref_url}")
else:
    print("No real ref images found!")
    exit(1)

# 2. Test: Image gen WITH ref - specific prompt to verify reference is used
print("\n=== TEST 1: Image gen with ref (should look like the ref) ===")
r = requests.post(f"{BASE}/api/generate_image", json={
    "prompt": "same character, same outfit, standing pose, white background",
    "model": "GPT-Image2",
    "ratio": "1:1",
    "resolution": "1K",
    "reference_images": [ref_url]
})
print(f"Submit: {r.status_code} {r.text[:200]}")
img_task = r.json()
img_task_id = img_task.get("task_id")

if img_task_id:
    for i in range(24):
        time.sleep(5)
        r = requests.get(f"{BASE}/api/task/{img_task_id}", timeout=5)
        t = r.json()
        status = t.get("status", "")
        uri = str(t.get("result_uri", ""))[:50]
        err = str(t.get("error", ""))[:60]
        print(f"  [{i*5}s] task {img_task_id}: status={status} uri={uri} error={err}")
        if status in ("completed", "failed"):
            break

# 3. Test: Video gen WITH ref image (Gemini Omni) - simple prompt
print("\n=== TEST 2: Video gen with ref image (Gemini Omni) ===")
r = requests.post(f"{BASE}/api/generate_video", json={
    "prompt": "the character slowly turns to face the camera, cinematic lighting",
    "model": "Gemini Omni",
    "ratio": "16:9",
    "duration": 6,
    "resolution": "720p",
    "reference_images": [ref_url]
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

# 4. Test: Video gen WITHOUT ref (baseline - should complete fast)
print("\n=== TEST 3: Video gen WITHOUT ref (baseline) ===")
r = requests.post(f"{BASE}/api/generate_video", json={
    "prompt": "a cat walking in a garden, cinematic, slow motion",
    "model": "Gemini Omni",
    "ratio": "16:9",
    "duration": 6,
    "resolution": "720p"
})
print(f"Submit: {r.status_code} {r.text[:200]}")
base_task = r.json()
base_task_id = base_task.get("task_id")

if base_task_id:
    for i in range(36):
        time.sleep(10)
        r = requests.get(f"{BASE}/api/task/{base_task_id}", timeout=5)
        t = r.json()
        status = t.get("status", "")
        uri = str(t.get("result_uri", ""))[:50]
        err = str(t.get("error", ""))[:60]
        print(f"  [{i*10}s] task {base_task_id}: status={status} uri={uri} error={err}")
        if status in ("completed", "failed"):
            break

print("\n=== ALL TESTS DONE ===")
'''

sftp = ssh.open_sftp()
with sftp.open('/tmp/test_clean.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('nohup python3 -u /tmp/test_clean.py > /tmp/test_clean.log 2>&1 & echo $!')
pid = stdout.read().decode().strip()
print(f"Started clean test, PID: {pid}")
time.sleep(15)

stdin, stdout, stderr = ssh.exec_command('cat /tmp/test_clean.log')
log = stdout.read().decode()
print(log[:2000] if log else "(no output yet)")

ssh.close()
