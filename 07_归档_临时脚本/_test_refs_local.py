import requests, time, os, base64, io
from PIL import Image, ImageDraw, ImageFont

BASE = "http://127.0.0.1:7861"

img = Image.new("RGB", (512, 512), (180, 50, 80))
draw = ImageDraw.Draw(img)
draw.rectangle([50, 50, 462, 462], outline=(255, 200, 100), width=8)
draw.text((180, 220), "TEST", fill=(255, 255, 200))
buf = io.BytesIO()
img.save(buf, format="PNG")
img_bytes = buf.getvalue()

r = requests.post(f"{BASE}/api/upload_ref", files={"file": ("test_ref.png", img_bytes)})
print("Upload ref:", r.status_code, r.text)
ref_data = r.json()
ref_url = ref_data.get("url", "")
print("Ref URL:", ref_url)

print("\n--- Submit image gen with ref ---")
r = requests.post(f"{BASE}/api/generate_image", json={
    "prompt": "a cute cat, anime style",
    "model": "GPT-Image2",
    "ratio": "1:1",
    "resolution": "1K",
    "reference_images": [ref_url]
})
print("Submit img result:", r.status_code, r.text[:300])
img_task = r.json()
img_task_id = img_task.get("task_id")

if img_task_id:
    for i in range(30):
        time.sleep(5)
        r = requests.get(f"{BASE}/api/task/{img_task_id}", timeout=5)
        t = r.json()
        print(f"  [{i*5}s] img task {img_task_id}: status={t['status']} uri={str(t.get('result_uri',''))[:50]} error={str(t.get('error',''))[:50]}")
        if t['status'] in ('completed', 'failed'):
            break

print("\n--- Submit video gen with ref ---")
r = requests.post(f"{BASE}/api/generate_video", json={
    "prompt": "a cat walking in a garden, slow motion, cinematic",
    "model": "Gemini Omni",
    "ratio": "16:9",
    "duration": 6,
    "resolution": "720p",
    "reference_images": [ref_url]
})
print("Submit vid result:", r.status_code, r.text[:300])
vid_data = r.json()
vid_task_id = vid_data.get("task_id")

if vid_task_id:
    for i in range(60):
        time.sleep(10)
        r = requests.get(f"{BASE}/api/task/{vid_task_id}", timeout=5)
        t = r.json()
        print(f"  [{i*10}s] vid task {vid_task_id}: status={t['status']} uri={str(t.get('result_uri',''))[:50]} error={str(t.get('error',''))[:50]}")
        if t['status'] in ('completed', 'failed'):
            break

print("\n=== Final known uris from refs_dir ===")
import glob
refs = glob.glob(os.path.join(os.path.dirname(BASE.replace('http://127.0.0.1:7861', '')), 'data', 'output', 'refs', '*'))
if not refs:
    refs = glob.glob(r'C:\Users\Administrator\Documents\OiioiiPool\data\output\refs\*')
for f in refs:
    print(f"  {os.path.basename(f)} ({os.path.getsize(f)} bytes)")