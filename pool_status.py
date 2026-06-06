import requests, json
r = requests.get("http://localhost:7861/api/pool/status", timeout=15)
data = r.json()
print(f"Total: {data.get('total_accounts')}")
print(f"Active: {data.get('active_accounts')}")
print(f"Reg running: {data.get('continuous_reg_running')}")
print(f"Total points: {data.get('total_points')}")
