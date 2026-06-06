import urllib.request, json

base = "http://localhost:7861"

# Test Nano Pro image generation
data = json.dumps({"prompt":"a cute cat","model":"Nano Pro","ratio":"1:1","resolution":"1K"}).encode()
req = urllib.request.Request(base + "/api/generate_image", data=data, headers={"Content-Type":"application/json"})
try:
    resp = urllib.request.urlopen(req)
    print("Nano Pro:", resp.read().decode())
except Exception as e:
    print("Nano Pro error:", e.read().decode() if hasattr(e,"read") else e)

# Test Nano 2
data = json.dumps({"prompt":"a cute cat","model":"Nano 2","ratio":"1:1","resolution":"1K"}).encode()
req = urllib.request.Request(base + "/api/generate_image", data=data, headers={"Content-Type":"application/json"})
try:
    resp = urllib.request.urlopen(req)
    print("Nano 2:", resp.read().decode())
except Exception as e:
    print("Nano 2 error:", e.read().decode() if hasattr(e,"read") else e)

# Test Niji7
data = json.dumps({"prompt":"a cute cat","model":"Niji7","ratio":"1:1","resolution":"1K"}).encode()
req = urllib.request.Request(base + "/api/generate_image", data=data, headers={"Content-Type":"application/json"})
try:
    resp = urllib.request.urlopen(req)
    print("Niji7:", resp.read().decode())
except Exception as e:
    print("Niji7 error:", e.read().decode() if hasattr(e,"read") else e)
