import urllib.request, json
resp = urllib.request.urlopen("http://localhost:7861/api/models")
d = json.loads(resp.read().decode())
print("IMAGE:", list(d.get("image", {}).keys()))
print("VIDEO:", list(d.get("video", {}).keys()))
