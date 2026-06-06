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
cur = conn.cursor()

# Get schema
cur.execute("PRAGMA table_info(accounts)")
cols = [r['name'] for r in cur.fetchall()]
print(f"accounts columns: {cols}")

cur.execute("SELECT * FROM accounts ORDER BY id LIMIT 5")
accts = [dict(r) for r in cur.fetchall()]
for a in accts:
    print(f"  #{a.get('id')} email={str(a.get('email',''))[:30]} pts={a.get('available_points', a.get('points','?'))} video_used={a.get('video_used','?')} status={a.get('status','?')}")

# Gemini Omni failure analysis
print("\n" + "=" * 80)
print("Gemini Omni 失败原因分析")
print("=" * 80)
cur.execute("SELECT error_message, COUNT(*) as cnt FROM tasks WHERE model_name='Gemini Omni' AND status='failed' GROUP BY error_message ORDER BY cnt DESC")
for r in cur.fetchall():
    print(f"  {r['cnt']}x: {r['error_message'][:80]}")

# 成功 vs 失败的 manualRefresh 对比
print("\n" + "=" * 80)
print("Gemini Omni 最近10个失败任务的详细信息")
print("=" * 80)
cur.execute("SELECT id, account_id, points_cost, task_id, error_message, created_at FROM tasks WHERE model_name='Gemini Omni' AND status='failed' ORDER BY id DESC LIMIT 10")
for r in cur.fetchall():
    print(f"  Task#{r['id']}: acct={r['account_id']} cost={r['points_cost']} tid={str(r['task_id'] or '')[:35]} err={str(r['error_message'] or '')[:60]}")

print("\n" + "=" * 80)
print("Gemini Omni 最近10个成功任务的详细信息")
print("=" * 80)
cur.execute("SELECT id, account_id, points_cost, task_id, created_at FROM tasks WHERE model_name='Gemini Omni' AND status='completed' ORDER BY id DESC LIMIT 10")
for r in cur.fetchall():
    print(f"  Task#{r['id']}: acct={r['account_id']} cost={r['points_cost']} tid={str(r['task_id'] or '')[:35]}")

# 找一个活跃账号做实时测试
print("\n" + "=" * 80)
print("实时测试 Gemini Omni")
print("=" * 80)

cur.execute("SELECT id, email, password, workspace_id, status FROM accounts WHERE status='active' LIMIT 5")
test_accts = [dict(r) for r in cur.fetchall()]
conn.close()

test_client = None
for a in test_accts:
    c = OiioiiClient(a['email'], a['password'], account_id=a['id'], workspace_id=a.get('workspace_id', ''))
    if c.login():
        pts = c.get_points()
        print(f"  #{a['id']} {a['email'][:30]} pts={pts}")
        if pts >= 60:
            test_client = c
            break

if not test_client:
    print("  No account with 60+ points for testing")
    sys.exit(0)

print(f"  Using #{test_client.account_id}")

# Check workspace
assets, has_list = test_client._get_asset_list()
print(f"  assetList: exists={has_list} count={len(assets)}")

# Check async tasks
r = requests.get(f"{API_BASE}/media/canvas_async_tasks/sync", headers=test_client._headers, timeout=15)
if r.status_code == 200:
    tasks = r.json().get("data", {}).get("tasks", [])
    print(f"  Async tasks: {len(tasks)}")
else:
    print(f"  async_tasks: HTTP {r.status_code}")

# Submit
print(f"\n  Submitting Gemini Omni 6s 720p no refs...")
ok, result, manual_refresh = test_client.generate_video(
    prompt="A golden sunset over a calm ocean, cinematic",
    model_name="Gemini Omni",
    ratio="16:9",
    duration=6,
    resolution="720p"
)
print(f"  Submit: ok={ok} result={str(result)[:80]} manualRefresh={manual_refresh}")

if ok:
    print(f"  Polling (max 120s)...")
    skip_uris = test_client.get_known_uris()
    status, uri = test_client.poll_result("video", skip_uris, max_wait=120, interval=8, remote_task_id=result)
    print(f"  Result: status={status} uri={str(uri)[:80]}")
