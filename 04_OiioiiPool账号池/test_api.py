import urllib.request, json

base = "http://localhost:7861"

# 1. Self register
data = json.dumps({"username":"testuser2","password":"test123456"}).encode()
req = urllib.request.Request(base + "/api/user/self-register", data=data, headers={"Content-Type":"application/json"})
try:
    resp = urllib.request.urlopen(req)
    print("1. Register:", resp.read().decode())
except Exception as e:
    print("1. Register error:", e.read().decode() if hasattr(e,"read") else e)

# 2. Login
data = json.dumps({"username":"testuser2","password":"test123456"}).encode()
req = urllib.request.Request(base + "/api/user/login", data=data, headers={"Content-Type":"application/json"})
resp = urllib.request.urlopen(req)
login = json.loads(resp.read().decode())
token = login.get("token","")
print("2. Login OK, token:", token[:30] + "...")

# 3. Get user info with session token
req = urllib.request.Request(base + "/api/user/info", headers={"Authorization":"Bearer " + token})
resp = urllib.request.urlopen(req)
print("3. User info:", resp.read().decode()[:100])

# 4. Generate redeem codes (admin login first)
data = json.dumps({"username":"admin","password":"admin123"}).encode()
req = urllib.request.Request(base + "/api/user/login", data=data, headers={"Content-Type":"application/json"})
resp = urllib.request.urlopen(req)
admin_login = json.loads(resp.read().decode())
admin_token = admin_login.get("token","")
print("4. Admin login OK")

data = json.dumps({"amount":10,"count":3}).encode()
req = urllib.request.Request(base + "/api/redeem/create", data=data, headers={"Content-Type":"application/json","Authorization":"Bearer " + admin_token})
resp = urllib.request.urlopen(req)
codes = json.loads(resp.read().decode())
print("5. Redeem codes:", json.dumps(codes, indent=2)[:200])

# 6. Use redeem code
if codes.get("codes"):
    code = codes["codes"][0]["code"]
    data = json.dumps({"code":code}).encode()
    req = urllib.request.Request(base + "/api/redeem/use", data=data, headers={"Content-Type":"application/json","Authorization":"Bearer " + token})
    resp = urllib.request.urlopen(req)
    print("6. Redeem result:", resp.read().decode())

# 7. Check balance after redeem
req = urllib.request.Request(base + "/api/user/info", headers={"Authorization":"Bearer " + token})
resp = urllib.request.urlopen(req)
print("7. Balance after redeem:", resp.read().decode()[:100])

# 8. Nginx proxy tests
req = urllib.request.Request("http://localhost/pool/static/user-portal.html")
resp = urllib.request.urlopen(req)
print("8. Nginx user portal:", resp.status)

req = urllib.request.Request("http://localhost/v1/models")
resp = urllib.request.urlopen(req)
print("9. Nginx v1/models:", resp.read().decode()[:60])
