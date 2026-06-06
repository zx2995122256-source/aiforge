import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=15)

restore_script = r'''
with open("/home/ubuntu/oiioii/api/server.py") as f:
    content = f.read()

import re

# Find the current upload_video_reference function
pattern = r'async def upload_video_reference.*?(?=\n@app\.post|\n\Z)'
match = re.search(pattern, content, re.DOTALL)
if match:
    old_func = match.group(0)
    print("Found function, replacing...")
    
    new_func = """async def upload_video_reference(file: UploadFile = File(...)):
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
    return {"uri": hogi_uri, "filename": fname}"""
    
    content = content.replace(old_func, new_func)
    with open("/home/ubuntu/oiioii/api/server.py", "w") as f:
        f.write(content)
    print("OK - restored original upload_video_reference")
else:
    print("Function not found!")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/restore_upload_v2.py', 'w') as f:
    f.write(restore_script)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/restore_upload_v2.py', timeout=10)
print(stdout.read().decode()[:500])
err = stderr.read().decode()[:300]
if err: print("ERR:", err)

# Verify
stdin, stdout, stderr = client.exec_command('sed -n "105,118p" /home/ubuntu/oiioii/api/server.py', timeout=10)
print("\n=== After restore ===")
print(stdout.read().decode()[:300])

# Restart
stdin, stdout, stderr = client.exec_command('sudo systemctl restart oiioii && sleep 3 && echo "restarted"', timeout=15)
print(stdout.read().decode()[:100])

client.close()