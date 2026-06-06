import requests

# Check OiioiiPool task #263 detail
r = requests.get("http://localhost:7861/api/task/263", timeout=10)
t = r.json()
print(f"Task #263: {t['status']} model={t.get('model','?')} cost={t.get('points_cost',0)}")
print(f"  Prompt: {t.get('prompt','')[:40]}")
print(f"  Result: {t.get('result_uri','')[:40]}")

# Check AiForge side
r2 = requests.post("http://localhost:7862/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r2.json()["token"]
headers = {"Authorization": f"Bearer {token}"}
r3 = requests.get("http://localhost:7862/api/gen/tasks", headers=headers, timeout=10)
for t in r3.json():
    print(f"  AF#{t['id']} {t['status']:10} oid={t.get('oiioii_task_id',0)} | {t.get('prompt','')[:25]}")

# Check what the Pool is actually doing - is the account working?
r4 = requests.get("http://localhost:7861/api/pool/status", timeout=10)
status = r4.json()
print(f"\nPool: {status.get('active_accounts',0)} accounts, {status.get('total_points',0)} pts")