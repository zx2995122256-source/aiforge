import paramiko, time

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

script = r'''
import requests, time, os, struct, zlib

BASE = "http://127.0.0.1:7861"

# Upload video ref
vpath = "/home/ubuntu/oiioii/data/output/refs/vidref_1780293719_d86f3b01.mp4"
with open(vpath, "rb") as f:
    vdata = f.read()
r = requests.post(f"{BASE}/api/upload_video_ref", files={"file": ("test_vref.mp4", vdata, "video/mp4")})
video_ref_url = r.json().get("uri", "")
print(f"Video ref URL: {video_ref_url}")

# Upload image ref
def make_png(w, h, r, g, b):
    raw = b""
    for y in range(h):
        raw += b"\x00"
        for x in range(w):
            raw += bytes([r, g, b])
    import zlib as z
    compressed = z.compress(raw)
    import struct as s
    def chunk(ctype, data):
        c = ctype + data
        return s.pack(">I", len(data)) + c + s.pack(">I", z.crc32(c) & 0xffffffff)
    ihdr = s.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    return png

img_bytes = make_png(256, 256, 180, 50, 80)
r = requests.post(f"{BASE}/api/upload_ref", files={"file": ("test_ref.png", img_bytes)})
ref_url = r.json().get("url", "")
print(f"Image ref URL: {ref_url}")

# Test 1: Video gen with video ref only
print("\n=== TEST 1: Video gen with video ref ===")
r = requests.post(f"{BASE}/api/generate_video", json={
    "prompt": "a cat walking in a garden, cinematic, slow motion",
    "model": "Gemini Omni",
    "ratio": "16:9",
    "duration": 6,
    "resolution": "720p",
    "reference_video": video_ref_url
})
print(f"Submit: {r.status_code} {r.text[:200]}")
t1 = r.json().get("task_id")

# Test 2: Video gen with BOTH image ref + video ref
print("\n=== TEST 2: Video gen with BOTH refs ===")
r = requests.post(f"{BASE}/api/generate_video", json={
    "prompt": "a cat walking in a forest, cinematic, slow motion",
    "model": "Gemini Omni",
    "ratio": "16:9",
    "duration": 6,
    "resolution": "720p",
    "reference_images": [ref_url],
    "reference_video": video_ref_url
})
print(f"Submit: {r.status_code} {r.text[:200]}")
t2 = r.json().get("task_id")

# Poll both
for i in range(36):
    time.sleep(10)
    elapsed = (i+1) * 10
    for tid, name in [(t1, "video_ref"), (t2, "both_refs")]:
        if tid:
            r = requests.get(f"{BASE}/api/task/{tid}", timeout=5)
            t = r.json()
            status = t.get("status", "")
            uri = str(t.get("result_uri", ""))[:40]
            err = str(t.get("error", ""))[:40]
            print(f"  [{elapsed}s] {name}({tid}): {status} uri={uri} err={err}")
            if status in ("completed", "failed"):
                if name == "video_ref":
                    t1 = None
                else:
                    t2 = None
    if not t1 and not t2:
        break

print("\n=== ALL TESTS DONE ===")
'''

sftp = ssh.open_sftp()
with sftp.open('/tmp/test_all_refs.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('nohup python3 -u /tmp/test_all_refs.py > /tmp/test_all_refs.log 2>&1 & echo $!')
pid = stdout.read().decode().strip()
print(f"Started, PID: {pid}")

ssh.close()
