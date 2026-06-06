import requests
BASE = "http://localhost:7863"
KEY = "aiforge2026"

# Test exactly what the frontend JS would call
# ak('/dashboard') => /admin/api/dashboard?key=aiforge2026
# But from admin.py's perspective, it's /api/dashboard?key=aiforge2026

# Test users API - check if any user has problematic data
r = requests.get(f"{BASE}/api/users?key={KEY}")
users = r.json()
print(f"Users: {len(users)}")
for u in users:
    if u.get('nickname') is None or u.get('email') is None:
        print(f"  PROBLEM: user {u.get('id')} has null nickname or email")
    # Check for special chars that might break JS
    nn = u.get('nickname', '')
    if "'" in nn or '"' in nn or '\\' in nn or '<' in nn or '>' in nn:
        print(f"  Special chars in nickname: user {u['id']} nickname='{nn}'")

# Test orders
r = requests.get(f"{BASE}/api/orders?key={KEY}")
orders = r.json()
print(f"\nOrders: {len(orders)}")

# Test agents
r = requests.get(f"{BASE}/api/agents?key={KEY}")
agents = r.json()
print(f"\nAgents: {len(agents)}")
for a in agents:
    print(f"  Agent {a.get('id')}: {a.get('email')} invite={a.get('invite_code')}")

# Test dashboard
r = requests.get(f"{BASE}/api/dashboard?key={KEY}")
d = r.json()
print(f"\nDashboard OK: users={d['users']['total']} pool={d.get('pool',{}).get('total_accounts','err')}")
