import paramiko, time

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

script = r'''
import requests, time, os, struct, zlib

BASE = "http://127.0.0.1:7861"

# Create test image
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
print(f"Ref URL: {ref_url}")

# Test 1: Video gen WITH ref image (Gemini Omni)
print("\n=== TEST: Video gen with ref image (Gemini Omni) ===")
r = requests.post(f"{BASE}/api/generate_video", json={
    "prompt": "a cat walking in a garden, cinematic, slow motion",
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

print("\n=== DONE ===")
'''

sftp = ssh.open_sftp()
with sftp.open('/tmp/test_final.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('nohup python3 -u /tmp/test_final.py > /tmp/test_final.log 2>&1 & echo $!')
pid = stdout.read().decode().strip()
print(f"Started test, PID: {pid}")
time.sleep(10)

stdin, stdout, stderr = ssh.exec_command('cat /tmp/test_final.log')
log = stdout.read().decode()
print(log[:1000] if log else "(no output yet)")

ssh.close()
