#!/usr/bin/env python3
import sys, os, time, json, requests, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "OiioiiPool"))

from core.client import OiioiiClient
from config import VIDEO_MODELS_DIRECT, API_BASE

DB_PATH = os.path.join(os.path.dirname(__file__), "OiioiiPool", "data", "oiioii_pool.db")
if not os.path.exists(DB_PATH):
    DB_PATH = os.path.join(os.path.dirname(__file__), "OiioiiPool", "oiioii_pool.db")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("=" * 80)
print("1. Gemini Omni 任务统计")
print("=" * 80)
cur = conn.cursor()
cur.execute("SELECT status, COUNT(*) as cnt, AVG(points_cost) as avg_cost FROM tasks WHERE model_name='Gemini Omni' GROUP BY status")
for r in cur.fetchall():
    print(f"  {r['status']}: {r['cnt']} tasks, avg_cost={r['avg_cost']:.0f}")

print("\n" + "=" * 80)
print("2. 账号状态")
print("=" * 80)
cur.execute("SELECT id, email, points, video_used, status, workspace_id FROM accounts ORDER BY id LIMIT 10")
accts = cur.fetchall()
for a in accts:
    print(f"  #{a['id']} {a['email'][:30]} pts={a['points']} video_used={a['video_used']} status={a['status']} ws={str(a['workspace_id'] or '')[:20]}")

print("\n" + "=" * 80)
print("3. 用第一个活跃账号测试 Gemini Omni 提交 + 查看返回详情")
print("=" * 80)

active = [a for a in accts if a['status'] == 'active' and a['points'] >= 60]
if not active:
    print("  No active account with 60+ points!")
    conn.close()
    sys.exit(0)

a = active[0]
print(f"  Using #{a['id']} {a['email'][:30]} pts={a['points']}")

c = OiioiiClient(a['email'], a['password'] if 'password' in a.keys() else "", 
                 account_id=a['id'], workspace_id=a['workspace_id'] or "")

# Get password from DB
cur.execute("SELECT password FROM accounts WHERE id=?", (a['id'],))
pw_row = cur.fetchone()
conn.close()

if not pw_row:
    print("  No password found!")
    sys.exit(0)

c = OiioiiClient(a['email'], pw_row['password'], account_id=a['id'], workspace_id=a['workspace_id'] or "")
if not c.login():
    print("  Login failed!")
    sys.exit(0)

print(f"  Login OK. Workspace: {c.workspace_id[:30]}")

# Check workspace
assets, has_list = c._get_asset_list()
print(f"  assetList: exists={has_list} count={len(assets)}")

# Check async tasks
r = requests.get(f"{API_BASE}/media/canvas_async_tasks/sync", headers=c._headers, timeout=15)
if r.status_code == 200:
    tasks = r.json().get("data", {}).get("tasks", [])
    print(f"  Async tasks: {len(tasks)}")
    for t in tasks[-3:]:
        print(f"    {str(t.get('task_id',''))[:30]} status={t.get('status','?')}")
else:
    print(f"  async_tasks: HTTP {r.status_code}")

# Submit test
print(f"\n  Submitting Gemini Omni 6s 720p...")
ok, result, manual_refresh = c.generate_video(
    prompt="A golden sunset over a calm ocean, cinematic",
    model_name="Gemini Omni",
    ratio="16:9",
    duration=6,
    resolution="720p"
)
print(f"  Result: ok={ok} result={str(result)[:80]} manualRefresh={manual_refresh}")

if ok:
    print(f"\n  Polling (max 120s, interval 8s)...")
    skip_uris = c.get_known_uris()
    status, uri = c.poll_result("video", skip_uris, max_wait=120, interval=8, remote_task_id=result)
    print(f"  Final: status={status} uri={str(uri)[:80]}")
