#!/usr/bin/env python3
"""AiForge 一键生成测试脚本 — 超未来科幻英文本片《THE LAST SIGNAL》

用法: python3 test_pipeline.py
前提: AiForge 后端在 http://localhost:7862 运行
"""
import json, time, sys, os
import requests

BASE = "http://localhost:7862"
EMAIL = "test_sci@aiforge.ai"
PWD = "test123456"
NAME = "TestBot"

# ===== Read raw script =====
SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "test_sci-fi_raw_script.txt")
with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
    RAW_SCRIPT = f.read().strip()

s = requests.Session()


def api(method, path, **kw):
    """Wrapper that auto-adds auth header."""
    headers = kw.pop("headers", {})
    if s.headers.get("Authorization"):
        headers.setdefault("Authorization", s.headers["Authorization"])
    r = s.request(method, f"{BASE}{path}", headers=headers, **kw)
    if r.status_code >= 400:
        print(f"  ❌ {method} {path} → {r.status_code}: {r.text[:200]}")
        return None
    return r.json()


def wait_project(pid, phase_key, total, timeout=1800):
    """Wait for a phase's items to all complete."""
    done_key = f"{phase_key}_done"
    wait = 0
    while wait < timeout:
        p = api("GET", f"/api/project/{pid}")
        if not p:
            time.sleep(10)
            wait += 10
            continue
        done = p.get(done_key, 0)
        failed = sum(1 for x in p.get("results", {}).get(phase_key, []) if x.get("status") == "failed")
        timeout_items = sum(1 for x in p.get("results", {}).get(phase_key, []) if x.get("status") == "timeout")
        print(f"  [{phase_key}] {done}/{total} done | failed={failed} timeout={timeout_items} | waited {wait}s" + (" " * 20))
        if done >= total:
            print(f"  ✅ {phase_key} COMPLETE")
            return True
        if failed + timeout_items > 0 and done + failed + timeout_items >= total:
            print(f"  ⚠️ {phase_key} finished with errors: {failed} failed, {timeout_items} timeout")
            return True
        time.sleep(10)
        wait += 10
    print(f"  ❌ {phase_key} TIMEOUT after {timeout}s")
    return False


def run():
    print("=" * 60)
    print("  AiForge 一键生成测试 — THE LAST SIGNAL")
    print("=" * 60)

    # Step 0: Register or login
    print("\n[0] 注册/登录...")
    r = api("POST", "/api/auth/register", json={"email": EMAIL, "password": PWD, "nickname": NAME})
    if r:
        s.headers["Authorization"] = f"Bearer {r['token']}"
        print(f"  ✅ 注册成功 | 用户ID={r['user']['id']}")
        uid = r['user']['id']
    else:
        # Try login
        r = api("POST", "/api/auth/login", json={"email": EMAIL, "password": PWD})
        if not r:
            print("  ❌ 登录也失败，退出")
            sys.exit(1)
        s.headers["Authorization"] = f"Bearer {r['token']}"
        uid = r['user']['id']
        print(f"  ✅ 登录成功 | 用户ID={uid}")

    # Credit check
    print(f"\n  积分: {r.get('user', {}).get('points', '?')} pts")

    # Step 1: Create project
    print("\n[1] 创建项目...")
    ten_minutes = time.time() + 600  # 10 min from now
    proj_name = f"THE LAST SIGNAL — {int(time.time())}"
    r = api("POST", "/api/project/create", json={
        "name": proj_name,
        "raw_script": RAW_SCRIPT,
        "script": json.dumps({"assets": [], "segments": []}),
        "video_model": "Gemini Omni",
        "image_model": "GPT-Image2",
        "ratio": "16:9",
        "resolution": "720p",
        "image_resolution": "1K",
        "duration": 10,
    })
    if not r:
        sys.exit(1)
    pid = r["id"]
    print(f"  ✅ Project #{pid}: {proj_name}")

    # Step 2: Phase 1 — AI split
    print("\n[2] Phase 1: AI 拆段...")
    r = api("POST", f"/api/project/{pid}/run", json={"phase": 1})
    if not r:
        sys.exit(1)
    segments = r.get("segments", [])
    assets = r.get("assets", [])
    print(f"  ✅ {len(segments)} 段, {len(assets)} 资产")

    # Step 3: Phase 2 — Generate assets
    print(f"\n[3] Phase 2: 生成资产 ({len(assets)} 项)...")
    r = api("POST", f"/api/project/{pid}/run", json={"phase": 2})
    if not r:
        sys.exit(1)
    wait_project(pid, "phase2", len(assets))

    # Step 4: Phase 3 — Generate storyboards
    seg_count = len(segments) or (api("GET", f"/api/project/{pid}") or {}).get("segments", [])
    if isinstance(seg_count, list):
        seg_count = len(seg_count)
    print(f"\n[4] Phase 3: 生成故事板 ({seg_count} 张)...")
    r = api("POST", f"/api/project/{pid}/run", json={"phase": 3})
    if not r:
        sys.exit(1)
    wait_project(pid, "phase3", seg_count)

    # Step 5: Phase 4 — Generate videos
    print(f"\n[5] Phase 4: 生成视频 ({seg_count} 段 × 10s)...")
    r = api("POST", f"/api/project/{pid}/run", json={"phase": 4})
    if not r:
        sys.exit(1)
    wait_project(pid, "phase4", seg_count)

    # Step 6: Done — show results
    print("\n" + "=" * 60)
    print("  ✅ PIPELINE COMPLETE")
    print("=" * 60)
    p = api("GET", f"/api/project/{pid}")
    if p:
        results = p.get("results", {})
        for ph in ("phase2", "phase3", "phase4"):
            items = results.get(ph, [])
            good = sum(1 for x in items if x.get("status") == "completed")
            fail = sum(1 for x in items if x.get("status") in ("failed", "timeout"))
            print(f"  {ph}: {good} completed, {fail} failed/@{len(items)} total")

        # Print video URLs
        print(f"\n  📍 视频输出:")
        phase4 = results.get("phase4", [])
        for i, v in enumerate(phase4):
            url = v.get("result_url", "")
            status = v.get("status", "?")
            if url:
                print(f"  段{i+1}: {BASE}{url}  [{status}]")
            else:
                print(f"  段{i+1}: [no URL yet]  [{status}]")

        # Print project URL for web view
        print(f"\n  🌐 Web: http://122.51.205.94/project/{pid}")
    print("\n✅ 测试完成")


if __name__ == "__main__":
    run()