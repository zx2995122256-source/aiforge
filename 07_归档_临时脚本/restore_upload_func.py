import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# Find position to insert (after upload_ref, before generate_image)
stdin, stdout, stderr = client.exec_command(
    'grep -n "def generate_image\|upload_ref\|upload_video_ref" /home/ubuntu/oiioii/api/server.py',
    timeout=10
)
print("Key markers:")
print(stdout.read().decode()[:300])

# Read the full file
stdin, stdout, stderr = client.exec_command('cat /home/ubuntu/oiioii/api/server.py', timeout=10)
content = stdout.read().decode()

# Find where to insert - after upload_ref function (before generate_image)
# Find @app.post("/api/generate_image") 
marker = '\n@app.post("/api/generate_image")'
idx = content.find(marker)

if idx == -1:
    # Try finding def generate_image
    idx = content.find('def generate_image')
    if idx > 0:
        idx = content.rfind('\n', 0, idx)

if idx > 0:
    new_func = '''
@app.post("/api/upload_video_ref")
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
    return {"uri": public_url, "filename": fname}

'''
    content = content[:idx] + new_func + content[idx:]
    
    sftp = client.open_sftp()
    with sftp.file('/home/ubuntu/oiioii/api/server.py', 'w') as f:
        f.write(content)
    sftp.close()
    print(f"Inserted upload_video_reference before line {content[:idx].count(chr(10)) + 1}")
else:
    print("ERROR: Could not find insertion point")

# Restart
stdin, stdout, stderr = client.exec_command('sudo systemctl restart oiioii && sleep 3 && sudo systemctl is-active oiioii', timeout=15)
print(f"oiioii: {stdout.read().decode().strip()}")

# Test
script = r'''
import requests, time
# Test upload_video_ref
r = requests.post("http://127.0.0.1:7862/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}
data = b"x" * 5 * 1024 * 1024
print(f"Uploading {len(data)} bytes...")
start = time.time()
r = requests.post("http://127.0.0.1:7862/api/gen/upload_video_ref",
    headers=headers, files={"file": ("test.mp4", data, "video/mp4")}, timeout=30)
print(f"Status: {r.status_code}, {time.time()-start:.1f}s")
print(f"Response: {r.text[:200]}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_final.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/test_final.py', timeout=30)
print("\n=== TEST ===")
print(stdout.read().decode()[:500])

client.close()