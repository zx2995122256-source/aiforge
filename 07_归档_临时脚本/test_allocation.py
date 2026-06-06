import requests

# Login
r = requests.post("http://localhost:7862/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# Check status
r = requests.get("http://localhost:7861/api/pool/status", timeout=10)
s = r.json()
print(f"Pool: {s.get('active_accounts',0)} accounts, {s.get('total_points',0)} pts")

# Submit image first - should use low-point account
print("\n=== 提交图片（应该用低分号）===")
r = requests.post("http://localhost:7862/api/gen/image", json={
    "prompt": "a cute cat", "model": "GPT-Image2", "ratio": "1:1", "resolution": "1K"
}, headers=headers, timeout=15)
print(f"  status={r.status_code} task=#{r.json().get('task_id','?')}")

# Submit video - should use high-point account
print("\n=== 提交视频（应该用高分号）===")
r = requests.post("http://localhost:7862/api/gen/video", json={
    "prompt": "a cat walking", "model": "Gemini Omni", "ratio": "16:9",
    "resolution": "720p", "duration": 5
}, headers=headers, timeout=15)
print(f"  status={r.status_code} task=#{r.json().get('task_id','?')}")