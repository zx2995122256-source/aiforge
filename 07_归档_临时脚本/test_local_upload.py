import requests

# Test local OiioiiPool upload_video_ref directly
data = b"x" * 1024 * 1024  # 1MB
r = requests.post("http://localhost:7861/api/upload_video_ref",
    files={"file": ("test.mp4", data, "video/mp4")},
    timeout=30)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:200]}")

if r.status_code == 200:
    print("✅ Local upload works!")
else:
    print("❌ Still failing")