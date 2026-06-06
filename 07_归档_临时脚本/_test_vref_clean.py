import paramiko, time

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

script = r'''
import sqlite3, requests, json, sys, time, base64

conn = sqlite3.connect('/home/ubuntu/oiioii/data/oiioii_pool.db')
cur = conn.execute("SELECT email, password, workspace_id FROM accounts WHERE email='oiio_6bd9u2nkyi1r@wshu.net'")
email, password, workspace_id = cur.fetchone()

SPB_URL = "https://spb.oiioii.ai"
SPB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVndnV6ZXN0eXlwYm1jZnVycmJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEyMTU4NTEsImV4cCI6MjA3Njc5MTg1MX0.Z1qdxtK0PLF5NV1yXrI9s_W2Hurdxo143DBzuUuajh0"
API = "https://api.oiioii.ai"

s = requests.Session()
r = s.post(f"{SPB_URL}/auth/v1/token?grant_type=password", json={"email": email, "password": password}, headers={"apikey": SPB_KEY}, timeout=15)
token = r.json().get("access_token", "")
headers = {"Authorization": f"Bearer {token}"}

# Get current assets as skip set
r = s.post(f"{API}/workspace/workspace_list", json={"data": {"limit": 10}}, headers=headers, timeout=15)
ws = r.json().get("data", {}).get("workspaces", [])
known_uris = set()
for w in ws:
    for a in w.get("workspaceDocument", {}).get("assetList", []):
        known_uris.add(a.get("uri", ""))
print(f"Known URIs before: {known_uris}")

# Upload test video
vpath = "/home/ubuntu/oiioii/data/output/refs/vidref_1780293719_d86f3b01.mp4"
with open(vpath, "rb") as f:
    vdata = f.read()
b64 = base64.b64encode(vdata).decode("ascii")
r = s.post(f"{API}/res/upload_file", json={"fileBlob": b64, "fileType": "video/mp4"}, headers=headers, timeout=60)
video_uri = r.json().get("data", {}).get("uri", "")
print(f"Uploaded video ref: {video_uri}")
known_uris.add(video_uri)  # also skip the uploaded ref

# Submit video gen with video ref
gen_body = {
    "workspaceId": workspace_id,
    "prompt": "a cat walking in a garden, cinematic",
    "mcpMethodName": "generate_video_gemini_omni",
    "ratio": "16:9",
    "aspectRatio": "16:9",
    "duration": 6,
    "resolution": "720p",
    "videoUrl": video_uri
}
r = s.post(f"{API}/media/video_generate/submit", json=gen_body, headers=headers, timeout=30)
resp = r.json()
task_id = resp.get("taskId", "")
print(f"Submitted: taskId={task_id} success={resp.get('success')} manualRefresh={resp.get('manualRefreshRequired')}")

# Poll for NEW assets
print("\n=== Polling for NEW video ===")
for i in range(30):
    time.sleep(10)
    elapsed = (i+1) * 10
    
    r = s.post(f"{API}/workspace/workspace_list", json={"data": {"limit": 10}}, headers=headers, timeout=15)
    ws = r.json().get("data", {}).get("workspaces", [])
    all_uris = set()
    for w in ws:
        for a in w.get("workspaceDocument", {}).get("assetList", []):
            all_uris.add(a.get("uri", ""))
    
    new_uris = all_uris - known_uris
    new_videos = [u for u in new_uris if "video" in u]
    
    print(f"  [{elapsed}s] total={len(all_uris)} known={len(known_uris)} new={len(new_uris)} new_videos={len(new_videos)}")
    
    if new_videos:
        print(f"  FOUND NEW VIDEO: {new_videos[0][:60]}")
        break
    
    if elapsed >= 300:
        print("  Timeout after 300s")
        break

conn.close()
'''

sftp = ssh.open_sftp()
with sftp.open('/tmp/test_vref_clean.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('nohup python3 -u /tmp/test_vref_clean.py > /tmp/test_vref_clean.log 2>&1 & echo $!')
pid = stdout.read().decode().strip()
print(f"Started, PID: {pid}")

ssh.close()
