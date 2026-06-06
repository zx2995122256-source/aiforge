import requests

# Check OiioiiPool status  
r = requests.get("http://localhost:7861/api/pool/status", timeout=10)
data = r.json()
print(f"Active accounts: {data.get('active_accounts', 0)}")
print(f"Total points: {data.get('total_points', 0)}")

# Check task #263
r = requests.get("http://localhost:7861/api/task/263", timeout=10)
print(f"\nTask #263: {r.text[:200]}")

# Check recent tasks
r = requests.get("http://localhost:7861/api/tasks", timeout=10)
tasks = r.json().get("tasks", [])[-5:]
for t in tasks:
    print(f"  #{t['id']} {t.get('task_type','')} {t.get('status','')} model={t.get('model','')}")