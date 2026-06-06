import requests, json

s = requests.Session()
r = s.post("http://localhost:7862/api/auth/login", json={"email": "sci_test@aiforge.ai", "password": "sci2025pw"}, timeout=10)
if r.status_code == 200:
    tok = r.json()["token"]
    r2 = s.get("http://localhost:7862/api/project/10", headers={"Authorization": f"Bearer {tok}"}, timeout=10)
    if r2.status_code == 200:
        d = r2.json()
        print("segments:", len(d.get("segments", [])))
        print("assets:", len(d.get("assets", [])))
        print("phase:", d.get("phase"))
        results = d.get("results", {})
        for ph in ("phase2", "phase3", "phase4"):
            items = results.get(ph, [])
            done = sum(1 for x in items if x.get("status") == "completed")
            fail = sum(1 for x in items if x.get("status") in ("failed", "timeout"))
            print(f"  {ph}: {done}/{len(items)} done, {fail} fail")
    else:
        print("GET failed:", r2.status_code, r2.text[:200])
else:
    print("Login failed:", r.status_code, r.text[:200])