import paramiko, time

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

script = r'''
import requests, time, os, struct, zlib

BASE = "http://127.0.0.1:7861"

# 1. Create minimal valid PNG
def make_png(width, height, r, g, b):
    raw = b""
    for y in range(height):
        raw += b"\x00"
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
r = requests.post(f"{BASE}/api/upload_ref", files={"file": ("test_ref.png", img_bytes)})
ref_data = r.json()
ref_url = ref_data.get("url", "")
print(f"Ref URL: {ref_url}")

# 2. Upload video ref
vidref_dir = "/home/ubuntu/oiioii/data/output/refs/"
vidref_files = [f for f in os.listdir(vidref_dir) if f.startswith("vidref_") and os.path.getsize(os.path.join(vidref_dir, f)) > 100000]
video_ref_url = ""
if vidref_files:
    vf = vidref_files[-1]
    vpath = os.path.join(vidref_dir, vf)
    with open(vpath, "rb") as f:
        vdata = f.read()
    r = requests.post(f"{BASE}/api/upload_video_ref", files={"file": (vf, vdata, "video/mp4")})
    vref_data = r.json()
    video_ref_url = vref_data.get("uri", "")
    print(f"Video ref URL: {video_ref_url}")

# 3. Test: Video gen WITH ref video (Gemini Omni) - THE KEY TEST
if video_ref_url:
    print("\n=== TEST: Video gen with ref video (Gemini Omni) ===")
    r = requests.post(f"{BASE}/api/generate_video", json={
        "prompt": "a person walking in a forest, cinematic lighting",
        "model": "Gemini Omni",
        "ratio": "16:9",
        "duration": 6,
        "resolution": "720p",
        "reference_video": video_ref_url
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

# 4. Test: Video gen WITH BOTH ref image + ref video
if video_ref_url:
    print("\n=== TEST: Video gen with BOTH ref image + ref video (Gemini Omni) ===")
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

print("\n=== ALL TESTS DONE ===")
'''

sftp = ssh.open_sftp()
with sftp.open('/tmp/test_videoref_fix.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('nohup python3 -u /tmp/test_videoref_fix.py > /tmp/test_videoref_fix.log 2>&1 & echo $!')
pid = stdout.read().decode().strip()
print(f"Started test, PID: {pid}")
print("Waiting 30s for initial output...")
time.sleep(30)

stdin, stdout, stderr = ssh.exec_command('cat /tmp/test_videoref_fix.log')
log = stdout.read().decode()
print(log[:3000] if log else "(no output yet)")

ssh.close()
