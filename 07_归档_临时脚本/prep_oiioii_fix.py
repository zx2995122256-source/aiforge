import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key)

# 1. Modify OiioiiPool upload_video_reference — save to disk
new_func = '''
import os, time, hashlib, shutil

OUTPUT_DIR = "/home/ubuntu/oiioii/data/output"
REFS_DIR = os.path.join(OUTPUT_DIR, "refs")
os.makedirs(REFS_DIR, exist_ok=True)

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
    print(f"[Upload] saved video ref: {fpath} ({len(content)} bytes)")
    return {"uri": f"/api/output/refs/{fname}", "filename": fname}
'''

# Read the file to find exact position
stdin, stdout, stderr = client.exec_command(
    'grep -n "async def upload_video_reference\|async def upload_reference" /home/ubuntu/oiioii/api/server.py',
    timeout=10
)
print("Function definitions found:")
print(stdout.read().decode()[:500])

# Get line numbers
stdin, stdout, stderr = client.exec_command(
    '''python3 -c "
with open('/home/ubuntu/oiioii/api/server.py') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if 'async def upload_video_reference' in l:
        print(f'upload_video_reference starts at line {i+1}')
    if 'async def upload_reference' in l:
        print(f'upload_reference starts at line {i+1}')
" ''',
    timeout=10
)
print(stdout.read().decode()[:500])

# Read the full server.py
stdin, stdout, stderr = client.exec_command('wc -l /home/ubuntu/oiioii/api/server.py', timeout=10)
total_lines = int(stdout.read().decode().strip().split()[0])
print(f"Total lines: {total_lines}")

client.close()