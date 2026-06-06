import paramiko
import time

KEY_PATH = r"C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem"
HOST = "122.51.205.94"
USER = "ubuntu"

script = r'''#!/usr/bin/env python3
"""
Full test: upload reference image + video, submit Gemini Omni with each, monitor results
"""
import requests, time, json, base64, os, io

API = "http://localhost:7861"
AI_API = "http://localhost:7862"  # AiForge backend

# Step 1: Create a simple test image and upload via AiForge proxy (which has the URL fix)
# Actually, upload direct to OiioiiPool API for consistency
print("=== Step 1: Create & upload reference image ===")

# Create a simple gradient test PNG
import struct, zlib

def create_test_png(w=256, h=256):
    """Create a simple gradient PNG"""
    raw = b""
    for y in range(h):
        for x in range(w):
            r = x % 256
            g = y % 256
            b = (x + y) % 256
            raw += bytes([r, g, b])
    
    def chunk(ctype, data):
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw_compressed = zlib.compress(raw)
    
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", raw_compressed)
    png += chunk(b"IEND", b"")
    return png

png_data = create_test_png()
print(f"  Created test PNG: {len(png_data)} bytes")

# Upload via OiioiiPool API directly
r = requests.post(f"{API}/api/upload_ref", files={"file": ("test_ref.png", png_data, "image/png")}, timeout=30)
if r.status_code == 200:
    upload_result = r.json()
    ref_url = upload_result.get("url", "")
    ref_filename = upload_result.get("filename", "")
    print(f"  Upload OK: url={ref_url} filename={ref_filename}")
else:
    print(f"  Upload FAILED: {r.status_code} {r.text[:100]}")
    ref_url = ""

# Step 2: Create test video (or skip video if ffmpeg not available)
print("\n=== Step 2: Check video ref capability ===")

# Check if ffmpeg exists
r = requests.get(f"{API}/api/models", timeout=10)
models = r.json()
gemini = models.get("video", {}).get("Gemini Omni", {})
print(f"  Gemini Omni video_ref: {gemini.get('video_ref', False)}")
print(f"  Gemini Omni ref_max: {gemini.get('ref_max', 0)}")

# Try to create a small test video using ffmpeg
video_ref_url = ""
import subprocess
ffmpeg_result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True)
if ffmpeg_result.returncode == 0:
    print("  ffmpeg available, creating test video...")
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=256x256:d=2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "/tmp/test_ref_video.mp4"
    ], capture_output=True)
    
    if os.path.exists("/tmp/test_ref_video.mp4"):
        with open("/tmp/test_ref_video.mp4", "rb") as f:
            video_data = f.read()
        r = requests.post(f"{API}/api/upload_video_ref", files={"file": ("test_ref.mp4", video_data, "video/mp4")}, timeout=60)
        if r.status_code == 200:
            vr = r.json()
            video_ref_url = vr.get("uri", "")
            print(f"  Video upload OK: uri={video_ref_url}")
        else:
            print(f"  Video upload FAILED: {r.status_code} {r.text[:100]}")
else:
    print("  ffmpeg not available, skipping video ref test")

# Step 3: Submit Gemini tasks
print("\n=== Step 3: Submit Gemini Omni tests ===")

test_cases = []

# Test 1: Reference image only
if ref_url:
    test_cases.append({
        "name": "with_image_ref",
        "body": {
            "prompt": "A serene mountain lake at sunrise, cinematic, reference image style test",
            "model": "Gemini Omni",
            "ratio": "16:9",
            "resolution": "720p",
            "duration": 5,
            "reference_images": [ref_url],
            "reference_video": ""
        }
    })
    print(f"  Test 1 - with_image_ref: {ref_url}")

# Test 2: Reference video only
if video_ref_url:
    test_cases.append({
        "name": "with_video_ref",
        "body": {
            "prompt": "A serene mountain lake at sunrise, cinematic, reference video style test",
            "model": "Gemini Omni",
            "ratio": "16:9",
            "resolution": "720p",
            "duration": 5,
            "reference_images": [],
            "reference_video": video_ref_url
        }
    })
    print(f"  Test 2 - with_video_ref: {video_ref_url}")

# Test 3: Reference image + video
if ref_url and video_ref_url:
    test_cases.append({
        "name": "with_both_refs",
        "body": {
            "prompt": "A serene mountain lake at sunrise, cinematic, both refs test",
            "model": "Gemini Omni",
            "ratio": "16:9",
            "resolution": "720p",
            "duration": 5,
            "reference_images": [ref_url],
            "reference_video": video_ref_url
        }
    })
    print(f"  Test 3 - with_both_refs")

# Also submit a plain (no ref) test for comparison
test_cases.append({
    "name": "no_ref",
    "body": {
        "prompt": "A serene mountain lake at sunrise, cinematic, no ref test",
        "model": "Gemini Omni",
        "ratio": "16:9",
        "resolution": "720p",
        "duration": 5,
        "reference_images": [],
        "reference_video": ""
    }
})
print("  Test 4 - no_ref (baseline)")

# Submit all
task_ids = {}
for tc in test_cases:
    r = requests.post(f"{API}/api/generate_video", json=tc["body"], timeout=30)
    if r.status_code == 200:
        tid = r.json().get("task_id", 0)
        task_ids[tc["name"]] = tid
        print(f"  Submitted {tc['name']} -> task #{tid}")
    else:
        print(f"  FAILED {tc['name']}: {r.status_code} {r.text[:200]}")
    time.sleep(0.5)

# Step 4: Monitor
print(f"\n=== Step 4: Monitor ({len(task_ids)} tasks, checking every 30s for 10 min) ===")
for m in range(20):
    time.sleep(30)
    all_done = True
    elapsed = (m + 1) * 30
    for name, tid in task_ids.items():
        r = requests.get(f"{API}/api/task/{tid}", timeout=10)
        t = r.json()
        s = t["status"]
        e = t.get("error", "")[:60]
        ru = str(t.get("result_uri", ""))[:50]
        if s == "completed":
            print(f"[{elapsed}s] {name}: COMPLETED uri={ru}")
        elif s == "failed":
            print(f"[{elapsed}s] {name}: FAILED err={e}")
        elif m % 2 == 0:
            print(f"[{elapsed}s] {name}: still {s}")
        if s not in ("completed", "failed"):
            all_done = False
    if all_done:
        print("All tasks finished!")
        break

# Step 5: Final report
print(f"\n{'='*60}")
print("FINAL RESULTS")
print(f"{'='*60}")
for name, tid in task_ids.items():
    r = requests.get(f"{API}/api/task/{tid}", timeout=10)
    t = r.json()
    lp = t.get("local_path", "")
    print(f"{name:20s} | #{tid:4d} | {t['status']:10s} | err={t.get('error','')[:60]} | local={lp[:40] if lp else 'N/A'}")

print("\nDone!")
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, key_filename=KEY_PATH, timeout=15)

sftp = ssh.open_sftp()
with sftp.open("/tmp/test_refs_full.py", "w") as f:
    f.write(script)
sftp.close()

print("=== Running full ref test (image + video refs, ~10 min) ===")
stdin, stdout, stderr = ssh.exec_command("python3 /tmp/test_refs_full.py 2>&1")

# Read output in real-time
import sys
while True:
    line = stdout.readline(4096)
    if not line:
        break
    print(line, end="")
    sys.stdout.flush()

err = stderr.read().decode().strip()
if err:
    print(f"STDERR: {err[:500]}")

ssh.close()
print("\n=== Test complete ===")