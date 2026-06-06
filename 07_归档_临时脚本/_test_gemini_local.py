#!/usr/bin/env python3
import sys, os, time, json, requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "OiioiiPool"))

from core.db import AccountDB, TaskDB
from core.client import OiioiiClient
from config import VIDEO_MODELS_DIRECT, API_BASE, SUPABASE_URL, SUPABASE_ANON_KEY

print("=" * 80)
print("1. 查看最近任务记录")
print("=" * 80)
tasks = TaskDB.get_all(30)
for t in tasks:
    model = t.get("model_name", "?")
    if "gemini" in model.lower() or "omni" in model.lower() or t.get("task_type") == "video":
        status = t.get("status", "?")
        err = str(t.get("error_message", "") or "")[:80]
        tid = str(t.get("task_id", "") or "")[:30]
        cost = t.get("points_cost", 0)
        acct = t.get("account_id", "?")
        print(f"  Task#{t['id']}: model={model} status={status} cost={cost} acct={acct} tid={tid} err={err}")

print("\n" + "=" * 80)
print("2. 查看账号状态")
print("=" * 80)
db = AccountDB()
accts = db.get_all_accounts()
for a in accts[:5]:
    email = a["email"]
    pts = a.get("points", 0)
    vid = a.get("video_used", 0)
    status = a.get("status", "?")
    ws = str(a.get("workspace_id", "") or "")[:20]
    print(f"  #{a['id']} {email[:30]} pts={pts} video_used={vid} status={status} ws={ws}")

print("\n" + "=" * 80)
print("3. 实际测试 Gemini Omni 提交（不垫图不垫视频）")
print("=" * 80)

model_info = VIDEO_MODELS_DIRECT.get("Gemini Omni")
print(f"  Model config: {json.dumps({k: v for k, v in model_info.items() if k != 'cost_duration_scale'}, indent=2)}")

# 找一个有积分的账号
test_client = None
for a in accts:
    if a.get("points", 0) >= 60 and a.get("status") == "active":
        c = OiioiiClient(a["email"], a["password"], account_id=a["id"], workspace_id=a.get("workspace_id", ""))
        if c.login():
            real_pts = c.get_points()
            print(f"  Using account #{a['id']} {a['email'][:30]} real_pts={real_pts}")
            test_client = c
            break

if not test_client:
    print("  No suitable account found for testing!")
else:
    # 先看 workspace 状态
    print(f"\n  Workspace ID: {test_client.workspace_id[:30]}")
    assets, has_list = test_client._get_asset_list()
    print(f"  assetList exists: {has_list}, asset count: {len(assets)}")
    if assets:
        for ast in assets[-3:]:
            print(f"    Last asset: type={ast.get('type','?')} uri={str(ast.get('uri',''))[:60]}")

    # 看 async_tasks
    r = requests.get(f"{API_BASE}/media/canvas_async_tasks/sync", headers=test_client._headers, timeout=15)
    if r.status_code == 200:
        tasks_data = r.json().get("data", {}).get("tasks", [])
        print(f"  Async tasks: {len(tasks_data)}")
        for t in tasks_data[-3:]:
            print(f"    Task: id={str(t.get('task_id',''))[:25]} status={t.get('status','?')} type={t.get('type','?')}")
    else:
        print(f"  async_tasks failed: {r.status_code}")

    # 提交一个简单的 Gemini Omni 视频生成
    print(f"\n  Submitting Gemini Omni test (6s 720p 16:9, no refs)...")
    ok, result, manual_refresh = test_client.generate_video(
        prompt="A golden sunset over a calm ocean, cinematic, slow motion",
        model_name="Gemini Omni",
        ratio="16:9",
        duration=6,
        resolution="720p"
    )
    print(f"  Submit result: ok={ok} result={str(result)[:80]} manualRefresh={manual_refresh}")

    if ok:
        print(f"\n  Polling for result (max 120s)...")
        skip_uris = test_client.get_known_uris()
        status, uri = test_client.poll_result("video", skip_uris, max_wait=120, interval=8, remote_task_id=result)
        print(f"  Poll result: status={status} uri={str(uri)[:80]}")
