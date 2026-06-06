import paramiko

key_path = r'C:\Users\Administrator\Documents\ssh_key.pem'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('122.51.205.94', username='ubuntu', key_filename=key_path, timeout=15)

script = r'''
import sqlite3, requests, json, sys, time, base64

conn = sqlite3.connect('/home/ubuntu/oiioii/data/oiioii_pool.db')

# Use the account that has assetList and works for image ref
cur = conn.execute("SELECT email, password, workspace_id FROM accounts WHERE email='oiio_6bd9u2nkyi1r@wshu.net'")
email, password, workspace_id = cur.fetchone()
print(f"Account: {email}")
print(f"Workspace: {workspace_id}")

SPB_URL = "https://spb.oiioii.ai"
SPB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVndnV6ZXN0eXlwYm1jZnVycmJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEyMTU4NTEsImV4cCI6MjA3Njc5MTg1MX0.Z1qdxtK0PLF5NV1yXrI9s_W2Hurdxo143DBzuUuajh0"
API = "https://api.oiioii.ai"

s = requests.Session()
r = s.post(f"{SPB_URL}/auth/v1/token?grant_type=password", json={"email": email, "password": password}, headers={"apikey": SPB_KEY}, timeout=15)
token = r.json().get("access_token", "")
headers = {"Authorization": f"Bearer {token}"}

# 1. Upload a test video to get hogi URI
print("\n=== Upload test video ===")
vpath = "/home/ubuntu/oiioii/data/output/refs/vidref_1780293719_d86f3b01.mp4"
with open(vpath, "rb") as f:
    vdata = f.read()
b64 = base64.b64encode(vdata).decode("ascii")
body = {"fileBlob": b64, "fileType": "video/mp4"}
r = s.post(f"{API}/res/upload_file", json=body, headers=headers, timeout=60)
resp = r.json()
video_uri = resp.get("data", {}).get("uri", "")
print(f"Upload result: {resp.get('code')} uri={video_uri}")

# 2. Submit video gen WITH video ref - print full request body
print("\n=== Submit video gen with videoUrl ===")
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
print(f"Request body: {json.dumps(gen_body, indent=2)[:500]}")

r = s.post(f"{API}/media/video_generate/submit", json=gen_body, headers=headers, timeout=30)
resp = r.json()
print(f"Response: {json.dumps(resp, indent=2)[:500]}")

task_id = resp.get("taskId", "")
manual = resp.get("manualRefreshRequired", False)
print(f"taskId={task_id} manualRefresh={manual}")

if task_id:
    # 3. Poll for result - check both async_tasks and workspace
    print("\n=== Polling ===")
    for i in range(30):
        time.sleep(10)
        elapsed = (i+1) * 10
        
        # Check async_tasks
        r = s.get(f"{API}/media/canvas_async_tasks/sync", headers=headers, timeout=15)
        async_tasks = r.json().get("data", {}).get("tasks", [])
        
        # Check workspace
        r = s.post(f"{API}/workspace/workspace_list", json={"data": {"limit": 10}}, headers=headers, timeout=15)
        ws = r.json().get("data", {}).get("workspaces", [])
        assets = []
        for w in ws:
            al = w.get("workspaceDocument", {}).get("assetList", [])
            assets.extend(al)
        
        new_videos = [a for a in assets if a.get("type") == "video" and a.get("uri", "") != video_uri]
        
        print(f"  [{elapsed}s] async_tasks={len(async_tasks)} total_assets={len(assets)} new_videos={len(new_videos)}")
        
        if new_videos:
            print(f"  FOUND: {new_videos[0].get('uri', '')[:60]}")
            break
        
        # Check async_tasks for our task
        for t in async_tasks:
            if task_id in t.get("task_id", ""):
                print(f"  async_task: status={t.get('status')} uri={t.get('result_payload',{}).get('uri','')[:50]}")
        
        if elapsed >= 300:
            print("  Giving up after 300s")
            break

conn.close()
'''

sftp = ssh.open_sftp()
with sftp.open('/tmp/test_direct_api.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('nohup python3 -u /tmp/test_direct_api.py > /tmp/test_direct_api.log 2>&1 & echo $!')
pid = stdout.read().decode().strip()
print(f"Started, PID: {pid}")
time.sleep(15)

stdin, stdout, stderr = ssh.exec_command('cat /tmp/test_direct_api.log')
log = stdout.read().decode()
print(log[:2000] if log else "(no output yet)")

ssh.close()
