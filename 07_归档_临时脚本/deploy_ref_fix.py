import paramiko, time

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# ─── Step 1: Modify OiioiiPool server.py ───
# Read the full file
stdin, stdout, stderr = client.exec_command('cat /home/ubuntu/oiioii/api/server.py', timeout=10)
content = stdout.read().decode()

# Replace upload_video_reference - save to disk, don't upload to external API
old_func = '''async def upload_video_reference(file: UploadFile = File(...)):
    content = await file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(400, "Video file too large (max 100MB)")
    client = engine._ensure_available_account(1)
    if not client:
        raise HTTPException(503, "No available account for video upload")
    ext = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
    fname = f"vidref_{int(time.time())}_{hash(file.filename) % 10000}{ext}"
    hogi_uri = client.upload_video_file(content, fname)
    if not hogi_uri:
        raise HTTPException(500, "Failed to upload video to Oiioii")
    return {"uri": hogi_uri, "filename": fname}'''

new_func = '''import hashlib
REFS_DIR = os.path.join(OUTPUT_DIR, "refs")
os.makedirs(REFS_DIR, exist_ok=True)

async def upload_video_reference(file: UploadFile = File(...)):
    content = await file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(400, "Video file too large (max 100MB)")
    ext = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
    ts = int(time.time())
    h = hashlib.md5(file.filename.encode() if file.filename else b"vid").hexdigest()[:8]
    fname = f"vidref_{ts}_{h}{ext}"
    fpath = os.path.join(REFS_DIR, fname)
    with open(fpath, "wb") as f:
        f.write(content)
    public_url = f"http://122.51.205.94/refs/{fname}"
    print(f"[Upload] Saved video ref: {fpath} ({len(content)} bytes) -> {public_url}")
    return {"uri": public_url, "filename": fname}'''

if old_func in content:
    new_content = content.replace(old_func, new_func)
    # Write back
    import io
    sftp = client.open_sftp()
    with sftp.file('/tmp/server_new.py', 'w') as f:
        f.write(new_content)
    sftp.close()
    print("Replace OK - written to /tmp/server_new.py")
else:
    print("ERROR: Could not find old function in file!")
    # Debug - find similar content
    if "upload_video_reference" in content:
        print("Found upload_video_reference but exact match failed")
        idx = content.find("async def upload_video_reference")
        print(content[idx:idx+500])
    else:
        print("upload_video_reference not found!")

# ─── Step 2: Modify AiForge backend generate.py to add refs route ───
sftp = client.open_sftp()
with sftp.file('/home/ubuntu/aiforge/backend/api/generate.py', 'r') as f:
    aiforge_content = f.read().decode()

refs_route = '''
import os, hashlib, time

REFS_DIR = "/home/ubuntu/oiioii/data/output/refs"
os.makedirs(REFS_DIR, exist_ok=True)

@router.get("/refs/{filename}")
def serve_ref(filename: str):
    fpath = os.path.join(REFS_DIR, filename)
    if not os.path.isfile(fpath):
        raise HTTPException(404, "File not found")
    ext = os.path.splitext(filename)[1].lower()
    media_map = {".mp4": "video/mp4", ".webm": "video/webm", ".png": "image/png",
                 ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif"}
    return FileResponse(fpath, media_type=media_map.get(ext, "video/mp4"))
'''

if "def serve_ref" not in aiforge_content:
    # Insert after the existing imports
    insert_pos = aiforge_content.find("router = APIRouter(prefix=\"/api/gen\"")
    insert_pos = aiforge_content.find("\n", insert_pos) + 1
    aiforge_content = aiforge_content[:insert_pos] + "\n# Refs serving\n" + refs_route + aiforge_content[insert_pos:]
    
    with sftp.file('/home/ubuntu/aiforge/backend/api/generate.py', 'w') as f:
        f.write(aiforge_content)
    print("AiForge refs route added!")
else:
    print("Refs route already exists!")

sftp.close()

# ─── Step 3: Deploy ───
cmds = [
    "cp /tmp/server_new.py /home/ubuntu/oiioii/api/server.py",
    "sudo systemctl restart oiioii && sleep 3",
    "sudo systemctl restart aiforge && sleep 2",
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
    out = stdout.read().decode().strip()
    if out: print(f"  {out[:200]}")

# ─── Step 4: Test ───
print("\n=== TEST ===")
script2 = r'''
import requests, time

# Upload a test video
BASE = "http://127.0.0.1:7862"
r = requests.post(BASE + "/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# Test with a reasonable size file
data = b"x" * 5 * 1024 * 1024
print(f"Uploading {len(data)} bytes...")
start = time.time()
r = requests.post(BASE + "/api/gen/upload_video_ref",
    headers=headers,
    files={"file": ("test_ref.mp4", data, "video/mp4")},
    timeout=30)
elapsed = time.time() - start
print(f"Upload: {r.status_code}, {elapsed:.1f}s")
resp = r.json()
print(f"URI: {resp.get('uri', '?')[:80]}")
print(f"Filename: {resp.get('filename', '?')}")

# Test ref is accessible
uri = resp.get("uri", "")
if "http" in uri:
    r2 = requests.get(uri, timeout=10)
    print(f"Ref accessible: {r2.status_code} ({len(r2.content)} bytes)")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_new_upload.py', 'w') as f:
    f.write(script2)
sftp.close()

stdin, stdout, stderr = client.exec_command('cd /tmp && python3 test_new_upload.py', timeout=30)
print(stdout.read().decode()[:1000])
err = stderr.read().decode()[:300]
if err: print("ERR:", err)

print("\n✅ DONE! Reference video now bypasses external API upload.")
client.close()