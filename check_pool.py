import requests, json
r = requests.get("http://localhost:7861/api/pool/status")
d = r.json()
print(f"Total accounts: {d['total_accounts']}")
print(f"Active: {d['active_accounts']}")
print(f"Total points: {d['total_points']}")
print(f"Continuous reg running: {d['continuous_reg_running']}")

# Check recent registration logs
r2 = requests.get("http://localhost:7861/api/pool/registration-logs")
d2 = r2.json()
logs = d2.get("logs", d2.get("recent_logs", []))
print(f"\nRecent registration logs ({len(logs)} total):")
for l in (logs[-10:] if logs else []):
    t = l.get("time", "?")[:19]
    s = l.get("status", "?")
    e = l.get("email", "?")[:30]
    err = l.get("error", "")[:80]
    print(f"  {t} {s} {e} {err}")
