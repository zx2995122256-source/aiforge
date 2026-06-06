import requests, json
r = requests.get('http://localhost:7861/api/tasks', timeout=10)
d = r.json()
tasks = d.get('tasks', d if isinstance(d, list) else [])
for t in tasks[-15:]:
    print(f"task {t.get('id')}: status={t.get('status')}, type={t.get('type','')}, model={t.get('model','')}")
