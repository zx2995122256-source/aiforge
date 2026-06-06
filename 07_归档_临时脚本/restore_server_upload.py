import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=15)

# Check what the server currently has
stdin, stdout, stderr = client.exec_command(
    'sed -n "105,118p" /home/ubuntu/oiioii/api/server.py',
    timeout=10
)
print("=== 服务器当前版本 ===")
print(stdout.read().decode()[:300])

# Restore the original upload_video_reference function
script = r'''
with open("/home/ubuntu/oiioii/api/server.py") as f:
    content = f.read()

old = '''async def upload_video_reference(file: UploadFile = File(...)):
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
    public_url = f"http://122.51.205.94/api/gen/refs/{fname}"
    print(f"[Upload] Saved video ref: {fpath} ({len(content)} bytes) -> {public_url}")
    return {"uri": public_url, "filename": fname}'''

new = '''async def upload_video_reference(file: UploadFile = File(...)):
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

if old in content:
    content = content.replace(old, new)
    with open("/home/ubuntu/oiioii/api/server.py", "w") as f:
        f.write(content)
    print("✅ 已恢复原始上传逻辑（走外部API）")
else:
    print("❌ 没找到版本B，检查文件内容...")
    import re
    idx = content.find("upload_video_reference")
    if idx >= 0:
        print(content[idx:idx+500])
    else:
        print("upload_video_reference 函数不存在!")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/restore_upload.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/restore_upload.py', timeout=10)
print(stdout.read().decode()[:500])
err = stderr.read().decode()[:300]
if err: print("ERR:", err)

# Remove the refs route we added to AiForge (no longer needed since we're using hogi://)
stdin, stdout, stderr = client.exec_command(
    '''python3 -c "
with open('/home/ubuntu/aiforge/backend/api/generate.py') as f:
    content = f.read()

# Remove the refs route and REFS_DIR
import re
# Remove from 'REFS_DIR =' to just before '@router.post(\"/upload_ref\")'
old = \"\nREFS_DIR = \\\"/home/ubuntu/oiioii/data/output/refs\\\"\n\n@router.get(\\\"/refs/{filename}\\\")\n\"
idx = content.find(old)
if idx >= 0:
    end = content.find('@router.post(\"/upload_ref\")', idx)
    if end < 0:
        end = idx + 500
    content = content[:idx] + content[end:]
    # Remove duplicate blank lines
    content = content.replace('\\n\\n\\n\\n', '\\n\\n')
    with open('/home/ubuntu/aiforge/backend/api/generate.py', 'w') as f:
        f.write(content)
    print('Removed refs route')
else:
    # Check if REFS_DIR exists
    if 'REFS_DIR' in content:
        print('REFS_DIR found but old string mismatch')
    else:
        print('REFS_DIR not found, nothing to remove')
" ''',
    timeout=10
)
print(stdout.read().decode()[:200])

# Restart services
stdin, stdout, stderr = client.exec_command('sudo systemctl restart oiioii && sleep 3 && sudo systemctl restart aiforge && sleep 2 && echo "restarted"', timeout=15)
print(stdout.read().decode()[:200])

# Test upload
script2 = r'''
import requests, time
# Upload small video
r = requests.post("http://127.0.0.1:7862/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# Test with 5MB
data = b"x" * 5 * 1024 * 1024
print(f"Uploading {len(data)} bytes...")
start = time.time()
r = requests.post("http://127.0.0.1:7862/api/gen/upload_video_ref",
    headers=headers, files={"file": ("test.mp4", data, "video/mp4")}, timeout=60)
print(f"Status: {r.status_code}, {time.time()-start:.1f}s")
resp = r.json()
uri = resp.get("uri", "")
print(f"URI: {uri[:60]}...")
print(f"Expected: hogi://..." if uri.startswith("hogi") else f"Got: {uri[:50]}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_restored.py', 'w') as f:
    f.write(script2)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/test_restored.py', timeout=60)
print("\n=== TEST ===")
print(stdout.read().decode()[:500])

client.close()