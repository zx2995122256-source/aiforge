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
    return s

# Upload a small image
s = get_session()
img_data = b"x" * 10 * 1024
b64 = base64.b64encode(img_data).decode("ascii")
r = s.post(f"{API_BASE}/res/upload_file", json={"fileBlob": b64, "fileType": "image/png"}, timeout=60)
img_hogi = r.json().get("data", {}).get("uri", "")
print(f"Image hogi: {img_hogi[:50]}")
print(f"Image data base64 size: {len(b64)} bytes")

# Test: Use a PUBLIC HTTP URL as videoUrl (like our tunnel)
# First upload same data to see if external API can fetch from URL
print("\n=== Test: HTTP URL as videoUrl (simulating tunnel) ===")
# Create a simple file server... actually use a known public URL
test_video_url = "https://www.w3schools.com/html/mov_bbb.mp4"  # public small mp4

body = {
    "workspaceId": s.headers.get("x-workspace-id", ""),
    "prompt": "a cat walking",
    "mcpMethodName": "generate_video_gemini_omni",
    "ratio": "16:9",
    "aspectRatio": "16:9",
    "duration": 5,
    "resolution": "720p",
    "videoUrl": test_video_url,
    "images": [img_hogi]
}
r = s.post(f"{API_BASE}/media/video_generate/submit", json=body, timeout=30)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:200]}")

# Test with a hogi:// video URL + images
s2 = get_session()
print("\n=== Test: hogi video URL + images ===")
video_data = b"x" * 500 * 1024
vb64 = base64.b64encode(video_data).decode("ascii")
r2 = s2.post(f"{API_BASE}/res/upload_file", json={"fileBlob": vb64, "fileType": "video/mp4"}, timeout=60)
vid_hogi = r2.json().get("data", {}).get("uri", "")
print(f"Video hogi: {vid_hogi[:50]}")

body2 = {
    "workspaceId": s2.headers.get("x-workspace-id", ""),
    "prompt": "a cat walking",
    "mcpMethodName": "generate_video_gemini_omni",
    "ratio": "16:9",
    "aspectRatio": "16:9",
    "duration": 5,
    "resolution": "720p",
    "videoUrl": vid_hogi,
    "images": [img_hogi]
}
r2 = s2.post(f"{API_BASE}/media/video_generate/submit", json=body2, timeout=30)
print(f"Status: {r2.status_code}")
print(f"Response: {r2.text[:200]}")
'''

sftp = client.open_sftp()
with sftp.file('/tmp/test_http_url.py', 'w') as f:
    f.write(script)
sftp.close()

print("Testing HTTP URL as videoUrl...")
stdin, stdout, stderr = client.exec_command('python3 /tmp/test_http_url.py', timeout=120)
print(stdout.read().decode()[:2000])
err = stderr.read().decode()[:500]
if err: print("ERR:", err)

client.close()