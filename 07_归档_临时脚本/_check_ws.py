#!/usr/bin/env python3
import sys, json, requests
sys.path.insert(0, "/opt/OiioiiPool")
from core.db import AccountDB
from core.client import OiioiiClient

db = AccountDB()
accts = db.get_all_accounts()
print(f"Total accounts: {len(accts)}")

for a in accts[:3]:
    email = a["email"]
    points = a.get("points", 0)
    print(f"\n--- Account: {email[:30]} points={points} ---")
    c = OiioiiClient(email, a["password"])
    if not c.login():
        print("  login failed")
        continue
    headers = c._headers
    r = requests.post("https://api.oiioii.ai/workspace/workspace_list",
        json={"data": {"limit": 10}}, headers=headers, timeout=15)
    if r.status_code != 200:
        print(f"  workspace_list failed: {r.status_code}")
        continue
    data = r.json().get("data", {})
    workspaces = data.get("workspaces", [])
    for ws in workspaces[:2]:
        ws_id = ws.get("workspaceId", "")[:20]
        doc = ws.get("workspaceDocument", {})
        has_assets = "assetList" in doc
        assets = doc.get("assetList", [])
        print(f"  Workspace {ws_id}: has_assetList={has_assets}, asset_count={len(assets)}")
        if assets:
            for ast in assets[:3]:
                print(f"    Asset: type={ast.get('type','?')} uri={str(ast.get('uri',''))[:80]}")
        else:
            print(f"    doc keys: {list(doc.keys())[:10]}")

    # Also check canvas_async_tasks
    r2 = requests.get("https://api.oiioii.ai/media/canvas_async_tasks/sync", headers=headers, timeout=15)
    if r2.status_code == 200:
        tasks = r2.json().get("data", {}).get("tasks", [])
        print(f"  Async tasks: {len(tasks)}")
        for t in tasks[:3]:
            print(f"    Task: id={str(t.get('taskId',''))[:20]} status={t.get('status','?')} type={t.get('type','?')}")
    else:
        print(f"  async_tasks failed: {r2.status_code}")
