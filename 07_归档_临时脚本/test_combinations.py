import paramiko

key_path = r'C:\Users\Administrator\Documents\xwechat_files\wxid_1m6tbo4n26m522_0a13\msg\file\2026-06\xiaye(1).pem'
key = paramiko.RSAKey.from_private_key_file(key_path)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('122.51.205.94', username='ubuntu', pkey=key, timeout=15)

script = r'''
import sys, requests, base64, time, sqlite3
sys.path.insert(0, "/home/ubuntu/oiioii")
from config import SUPABASE_URL, SUPABASE_ANON_KEY, API_BASE

conn = sqlite3.connect("/home/ubuntu/oiioii/data/oiioii_pool.db")
row = conn.execute("SELECT email, password FROM accounts WHERE status='active' LIMIT 1").fetchone()
conn.close()
email, password = row[0], row[1]

def get_session():
    s = requests.Session()
    r = s.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        json={"email": email, "password": password, "gotrue_meta_security": {}},
        headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"}, timeout=15)
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r2 = s.post(f"{API_BASE}/workspace/workspace_list", json={"data": {"limit": 10}}, headers=h, timeout=15)
    ws = r2.json().get("data", {}).get("workspaces", [])
    if ws:
        h["x-workspace-id"] = ws[0].get("workspaceId", "")
    s.headers.update(h)
    return s, token

# First test: Upload a video file and get a hogi URI
s, token = get_session()
print("=== Upload 500KB video to get hogi URI ===")
data = b"x" * 500 * 1024
b64 = base64.b64encode(data).decode("ascii")
r = s.post(f"{API_BASE}/res/upload_file", json={"fileBlob": b64, "fileType": "video/mp4"}, timeout=60)
video_hogi = r.json().get("data", {}).get("uri", "")
print(f"Video hogi URI: {video_hogi[:50]}")

# Upload a small image
s2, token2 = get_session()
print("\n=== Upload 10KB image to get hogi URI ===")
img_data = b"x" * 10 * 1024
b64 = base64.b64encode(img_data).decode("ascii")
r = s2.post(f"{API_BASE}/res/upload_file", json={"fileBlob": b64, "fileType": "image/png"}, timeout=60)
img_hogi = r.json().get("data", {}).get("uri", "")
print(f"Image hogi URI: {img_hogi[:50]}")

# Test 1: Submit video generation with ONLY videoUrl
print("\n=== Test 1: videoUrl only ===")
body1 = {
    "workspaceId": s.headers.get("x-workspace-id", ""),
    "prompt": "a cat walking",
    "mcpMethodName": "generate_video_gemini_omni",
    "ratio": "16:9",
    "aspectRatio": "16:9",
    "duration": 5,
    "resolution": "720p",
    "videoUrl": video_hogi
}
r1 = s.post(f"{API_BASE}/media/video_generate/submit", json=body1, timeout=30)
print(f"Status: {r1.status_code}")
print(f"Response: {r1.text[:200]}")

# Test 2: Submit with BOTH images and videoUrl
print("\n=== Test 2: images + videoUrl ===")
body2 = {**body1, "images": [img_hogi]}
r2 = s.post(f"{API_BASE}/media/video_generate/submit", json=body2, timeout=30)
print(f"Status: {r2.status_code}")
print(f"Response: {r2.text[:200]}")

# Test 3: Submit with images only
print("\n=== Test 3: images only ===")
body3 = {**body1, "images": [img_hogi]}
del body3["videoUrl"]
r3 = s.post(f"{API_BASE}/media/video_generate/submit", json=body3, timeout=30)
print(f"Status: {r3.status_code}")
print(f"Response: {r3.text[:200]}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_combinations.py', 'w') as f:
    f.write(script)
sftp.close()

print("Testing different combinations...")
stdin, stdout, stderr = client.exec_command('python3 /tmp/test_combinations.py', timeout=120)
print(stdout.read().decode()[:2000])
err = stderr.read().decode()[:500]
if err: print("ERR:", err)

client.close()