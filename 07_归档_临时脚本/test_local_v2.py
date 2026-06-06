import urllib.request, urllib.error, io

data = b"x" * 1024 * 1024

boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
body = io.BytesIO()

def w(s): body.write(s.encode())

w("------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n")
w("Content-Disposition: form-data; name=\"file\"; filename=\"test.mp4\"\r\n")
w("Content-Type: video/mp4\r\n\r\n")
body.write(data)
w("\r\n")
w("------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n")

req = urllib.request.Request(
    "http://localhost:7861/api/upload_video_ref",
    data=body.getvalue(),
    headers={"Content-Type": "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW"}
)
try:
    resp = urllib.request.urlopen(req, timeout=30)
    print(f"Status: {resp.status}")
    print(f"Response: {resp.read().decode()[:200]}")
except urllib.error.HTTPError as e:
    print(f"Status: {e.code}")
    print(f"Response: {e.read().decode()[:200]}")
