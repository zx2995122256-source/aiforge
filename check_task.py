import requests, json
r = requests.get("http://localhost:7861/api/task/509", timeout=15)
d = r.json()
print(f"Status: {d.get('status')}")
if d.get('local_path'):
    print(f"File: {d['local_path']}")
if d.get('error'):
    print(f"Error: {d['error']}")
