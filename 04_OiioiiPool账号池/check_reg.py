import urllib.request, json

r = urllib.request.urlopen("http://localhost:7861/api/pool/status", timeout=5)
s = json.loads(r.read())
accounts = s.get("accounts", [])
print(f"Accounts: {len(accounts)}")

r2 = urllib.request.urlopen("http://localhost:7861/api/pool/register/1780673321781", timeout=5)
print(f"Register job: {json.dumps(json.loads(r2.read()), ensure_ascii=False)}")
