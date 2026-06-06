import urllib.request, json

# Test through AiForge backend (port 7862)
# First need a JWT token
base = "http://localhost:7862"

# Login
data = json.dumps({"email":"xiaye@aiforge.com","password":"zx4579561"}).encode()
req = urllib.request.Request(base + "/api/auth/login", data=data, headers={"Content-Type":"application/json"})
try:
    resp = urllib.request.urlopen(req)
    login = json.loads(resp.read().decode())
    token = login.get("token","")
    print("Login OK, token:", token[:30] + "...")
except Exception as e:
    print("Login error:", e.read().decode() if hasattr(e,"read") else e)
    token = ""

if token:
    # Submit Nano Pro image
    data = json.dumps({"prompt":"a cute cat","model":"Nano Pro","ratio":"1:1","resolution":"1K"}).encode()
    req = urllib.request.Request(base + "/api/gen/image", data=data, headers={"Content-Type":"application/json","Authorization":"Bearer " + token})
    try:
        resp = urllib.request.urlopen(req)
        print("Nano Pro via AiForge:", resp.read().decode())
    except Exception as e:
        err = e.read().decode() if hasattr(e,"read") else str(e)
        print("Nano Pro via AiForge error:", err)

    # Submit Niji7
    data = json.dumps({"prompt":"a cute cat","model":"Niji7","ratio":"1:1","resolution":"1K"}).encode()
    req = urllib.request.Request(base + "/api/gen/image", data=data, headers={"Content-Type":"application/json","Authorization":"Bearer " + token})
    try:
        resp = urllib.request.urlopen(req)
        print("Niji7 via AiForge:", resp.read().decode())
    except Exception as e:
        err = e.read().decode() if hasattr(e,"read") else str(e)
        print("Niji7 via AiForge error:", err)
