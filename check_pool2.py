import requests, json
r = requests.get("http://localhost:7861/api/pool/status")
d = r.json()
print(f"total={d['total_accounts']} active={d['active_accounts']} points={d['total_points']} reg_running={d['continuous_reg_running']}")
