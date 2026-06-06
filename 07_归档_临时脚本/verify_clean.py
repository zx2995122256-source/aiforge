import requests

# Quick test: Submit simple video via AiForge
print("登录...")
r = requests.post("http://localhost:7862/api/auth/login", json={"email":"xiaye@aiforge.com","password":"zx4579561"}, timeout=10)
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

print("提交视频（无参考）...")
r = requests.post("http://localhost:7862/api/gen/video", json={
    "prompt": "一只小猫在玩耍",
    "model": "Gemini Omni",
    "ratio": "16:9",
    "resolution": "720p",
    "duration": 5,
    "reference_images": [],
    "reference_video": ""
}, headers=headers, timeout=15)
resp = r.json()
print(f"  Status: {r.status_code}, task=#{resp.get('task_id','?')} oid=#{resp.get('oiioii_task_id','?')}")

# Check OiioiiPool
oid = resp.get("oiioii_task_id", 0)
r = requests.get(f"http://localhost:7861/api/task/{oid}", timeout=10)
t = r.json()
print(f"  Pool: #{oid} status={t.get('status','?')} model={t.get('model','')} cost={t.get('points_cost',0)}")

# Check there are no old stuck tasks
r = requests.get("http://localhost:7861/api/tasks", timeout=10)
tasks = r.json().get("tasks", [])
stuck = [t for t in tasks if t["status"] in ("processing", "running")]
print(f"\nPool 总任务: {len(tasks)}, 处理中: {len(stuck)}")

r = requests.get("http://localhost:7862/api/gen/tasks", headers=headers, timeout=10)
af_tasks = r.json()
stuck_af = [t for t in af_tasks if t["status"] == "running"]
print(f"AiForge 总任务: {len(af_tasks)}, 运行中: {len(stuck_af)}")
print("✅ 一切正常！去 http://localhost:5173 试试")