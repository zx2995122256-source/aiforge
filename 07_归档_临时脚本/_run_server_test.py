import paramiko, time

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

script = r'''
import requests, time, os, base64, struct, zlib

BASE = "http://127.0.0.1:7861"

# 1. Create minimal valid PNG without PIL
def make_png(width, height, r, g, b):
    raw = b""
    for y in range(height):
        raw += b"\x00"  # filter none
        for x in range(width):
            raw += bytes([r, g, b])
    compressed = zlib.compress(raw)
    def chunk(ctype, data):
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    return png

img_bytes = make_png(256, 256, 180, 50, 80)
print(f"Test image: {len(img_bytes)} bytes")

# 2. Upload ref image
r = requests.post(f"{BASE}/api/upload_ref", files={"file": ("test_ref.png", img_bytes)})
print(f"Upload ref: {r.status_code} {r.text[:200]}")
ref_data = r.json()
ref_url = ref_data.get("url", "")
print(f"Ref URL: {ref_url}")

# 3. Find existing video ref
video_ref_url = ""
vidref_dir = "/home/ubuntu/oiioii/data/output/refs/"
if os.path.isdir(vidref_dir):
    vidref_files = [f for f in os.listdir(vidref_dir) if f.startswith("vidref_") and os.path.getsize(os.path.join(vidref_dir, f)) > 100000]
    if vidref_files:
        vf = vidref_files[-1]
        vpath = os.path.join(vidref_dir, vf)
        vsize = os.path.getsize(vpath)
        print(f"Using existing video ref: {vf} ({vsize} bytes)")
        with open(vpath, "rb") as f:
            vdata = f.read()
        r = requests.post(f"{BASE}/api/upload_video_ref", files={"file": (vf, vdata, "video/mp4")})
        print(f"Upload video ref: {r.status_code} {r.text[:200]}")
        vref_data = r.json()
        video_ref_url = vref_data.get("uri", "")
        print(f"Video ref URL: {video_ref_url}")

# 4. Test: Image gen WITH ref
print("\n=== TEST 1: Image gen with ref ===")
r = requests.post(f"{BASE}/api/generate_image", json={
    "prompt": "a cute orange cat sitting on a windowsill, anime style",
    "model": "GPT-Image2",
    "ratio": "1:1",
    "resolution": "1K",
    "reference_images": [ref_url]
})
print(f"Submit: {r.status_code} {r.text[:300]}")
img_task = r.json()
img_task_id = img_task.get("task_id")

if img_task_id:
    for i in range(30):
        time.sleep(5)
        r = requests.get(f"{BASE}/api/task/{img_task_id}", timeout=5)
        t = r.json()
        status = t.get("status", "")
        uri = str(t.get("result_uri", ""))[:50]
        err = str(t.get("error", ""))[:60]
        print(f"  [{i*5}s] task {img_task_id}: status={status} uri={uri} error={err}")
        if status in ("completed", "failed"):
            break

# 5. Test: Video gen WITH ref image (Gemini Omni)
print("\n=== TEST 2: Video gen with ref image (Gemini Omni) ===")
r = requests.post(f"{BASE}/api/generate_video", json={
    "prompt": "a cat walking gracefully in a garden, cinematic, slow motion",
    "model": "Gemini Omni",
    "ratio": "16:9",
    "duration": 6,
    "resolution": "720p",
    "reference_images": [ref_url]
})
print(f"Submit: {r.status_code} {r.text[:300]}")
vid_task = r.json()
vid_task_id = vid_task.get("task_id")

if vid_task_id:
    for i in range(60):
        time.sleep(10)
        r = requests.get(f"{BASE}/api/task/{vid_task_id}", timeout=5)
        t = r.json()
        status = t.get("status", "")
        uri = str(t.get("result_uri", ""))[:50]
        err = str(t.get("error", ""))[:60]
        print(f"  [{i*10}s] task {vid_task_id}: status={status} uri={uri} error={err}")
        if status in ("completed", "failed"):
            break

# 6. Test: Video gen WITH ref video (Gemini Omni)
if video_ref_url:
    print("\n=== TEST 3: Video gen with ref video (Gemini Omni) ===")
    r = requests.post(f"{BASE}/api/generate_video", json={
        "prompt": "a person walking in a forest, cinematic lighting",
        "model": "Gemini Omni",
        "ratio": "16:9",
        "duration": 6,
        "resolution": "720p",
        "reference_video": video_ref_url
    })
    print(f"Submit: {r.status_code} {r.text[:300]}")
    vvid_task = r.json()
    vvid_task_id = vvid_task.get("task_id")

    if vvid_task_id:
        for i in range(60):
            time.sleep(10)
            r = requests.get(f"{BASE}/api/task/{vvid_task_id}", timeout=5)
            t = r.json()
            status = t.get("status", "")
            uri = str(t.get("result_uri", ""))[:50]
            err = str(t.get("error", ""))[:60]
            print(f"  [{i*10}s] task {vvid_task_id}: status={status} uri={uri} error={err}")
            if status in ("completed", "failed"):
                break
else:
    print("\n=== TEST 3: SKIPPED (no video ref available) ===")

# 7. Test: Video gen WITH BOTH
if video_ref_url:
    print("\n=== TEST 4: Video gen with BOTH ref image + ref video (Gemini Omni) ===")
    r = requests.post(f"{BASE}/api/generate_video", json={
        "prompt": "a cat walking in a forest, cinematic, slow motion",
        "model": "Gemini Omni",
        "ratio": "16:9",
        "duration": 6,
        "resolution": "720p",
        "reference_images": [ref_url],
        "reference_video": video_ref_url
    })
    print(f"Submit: {r.status_code} {r.text[:300]}")
    both_task = r.json()
    both_task_id = both_task.get("task_id")

    if both_task_id:
        for i in range(60):
            time.sleep(10)
            r = requests.get(f"{BASE}/api/task/{both_task_id}", timeout=5)
            t = r.json()
            status = t.get("status", "")
            uri = str(t.get("result_uri", ""))[:50]
            err = str(t.get("error", ""))[:60]
            print(f"  [{i*10}s] task {both_task_id}: status={status} uri={uri} error={err}")
            if status in ("completed", "failed"):
                break
else:
    print("\n=== TEST 4: SKIPPED (no video ref available) ===")

print("\n=== ALL TESTS DONE ===")
'''

sftp = ssh.open_sftp()
with sftp.open('/tmp/test_refs_server.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('nohup python3 -u /tmp/test_refs_server.py > /tmp/test_refs_server.log 2>&1 & echo $!')
pid = stdout.read().decode().strip()
print(f"Started test on server, PID: {pid}")
print("Waiting 20s for initial output...")
time.sleep(20)

stdin, stdout, stderr = ssh.exec_command('cat /tmp/test_refs_server.log')
log = stdout.read().decode()
print(log[:3000] if log else "(no output yet)")

ssh.close()
