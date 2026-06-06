"""AiForge 一键生成完整测试 — THE LAST SIGNAL
模拟网站操作：创建项目→Phase1拆段→Phase2资产生图→Phase3故事板→Phase4视频生成
"""
import json, time, sys, os, requests

BASE = "http://localhost:7862"

SCRIPT_PATH = "/home/ubuntu/aiforge/test_sci-fi_raw_script.txt"
with open(SCRIPT_PATH, "r") as f:
    RAW_SCRIPT = f.read().strip()

s = requests.Session()
auth_token = None

def api(method, path, **kw):
    global auth_token
    headers = kw.pop("headers", {})
    if auth_token:
        headers.setdefault("Authorization", f"Bearer {auth_token}")
    timeout = kw.pop("timeout", 180)  # default 180s for LLM calls
    try:
        r = s.request(method, f"{BASE}{path}", headers=headers, timeout=timeout, **kw)
        if r.status_code >= 400:
            print(f"  [ERROR] {method} {path} -> {r.status_code}: {r.text[:200]}")
            return None
        return r.json()
    except Exception as e:
        print(f"  [EXCEPTION] {method} {path}: {e}")
        return None

def wait_phase(pid, phase_key, total, label, timeout=3600):
    done_key = f"{phase_key}_done"
    waited = 0
    while waited < timeout:
        p = api("GET", f"/api/project/{pid}")
        if not p:
            time.sleep(15)
            waited += 15
            continue
        done = p.get(done_key, 0)
        items = p.get("results", {}).get(phase_key, [])
        failed = sum(1 for x in items if x.get("status") == "failed")
        timeout_items = sum(1 for x in items if x.get("status") == "timeout")
        running = sum(1 for x in items if x.get("status") == "running")
        pending = sum(1 for x in items if x.get("status") == "pending")
        print(f"  [{phase_key}] {done}/{total} done | fail={failed} timeout={timeout_items} run={running} pend={pending} | {waited}s")
        sys.stdout.flush()
        if done >= total:
            print(f"  >>> {label} COMPLETE")
            return True
        if failed + timeout_items > 0 and done + failed + timeout_items >= total:
            print(f"  >>> {label} FINISHED with {failed} fails")
            return True
        time.sleep(15)
        waited += 15
    print(f"  >>> {label} TIMEOUT")
    return False

def log(msg):
    print(f"\n{'='*60}\n  {msg}\n{'='*60}")
    sys.stdout.flush()

# ====== MAIN ======
log("LOGIN")
r = api("POST", "/api/auth/login", json={"email": "sci_test@aiforge.ai", "password": "sci2025pw"})
if not r:
    sys.exit(1)
auth_token = r["token"]
uid = r["user"]["id"]
pts = r["user"]["points"]
print(f"  User {uid}: {pts} pts")

# Create project
log("CREATE PROJECT — THE LAST SIGNAL")
r = api("POST", "/api/project/create", json={
    "name": f"THE LAST SIGNAL test {int(time.time())}",
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
print(f"  Project #{pid}")

seg_count = None

# Phase 1: AI Split
log("PHASE 1: AI SPLIT")
r = api("POST", f"/api/project/{pid}/run", json={"phase": 1})
if r:
    segments = r.get("segments", [])
    assets = r.get("assets", [])
    seg_count = len(segments)
    print(f"  {seg_count} segments, {len(assets)} assets")

if seg_count is None:
    p = api("GET", f"/api/project/{pid}")
    seg_count = len(p.get("segments", [])) if p else 0

# Phase 2: Generate Assets
log(f"PHASE 2: GENERATE ASSETS")
r = api("POST", f"/api/project/{pid}/run", json={"phase": 2})
if r:
    asset_count = r.get("assets_count", 0)
    print(f"  Assets to generate: {asset_count}")
    wait_phase(pid, "phase2", asset_count, "ASSET GENERATION")

# Phase 3: Generate Storyboards
time.sleep(5)  # brief pause between phases
log(f"PHASE 3: GENERATE STORYBOARDS ({seg_count} boards)")
r = api("POST", f"/api/project/{pid}/run", json={"phase": 3})
if r:
    print(f"  Storyboard generation started")
    wait_phase(pid, "phase3", seg_count, "STORYBOARD GENERATION")

# Phase 4: Generate Videos
time.sleep(5)
log(f"PHASE 4: GENERATE VIDEOS ({seg_count} x 10s = {seg_count * 10}s)")
r = api("POST", f"/api/project/{pid}/run", json={"phase": 4})
if r:
    print(f"  Video generation started")
    wait_phase(pid, "phase4", seg_count, "VIDEO GENERATION")

# Final Report
log("FINAL REPORT")
p = api("GET", f"/api/project/{pid}")
if p:
    results = p.get("results", {})
    print(f"\n  Project: {p['name']}")
    print(f"  Duration: {seg_count} x 10s = {seg_count * 10}s = {seg_count * 10 // 60}m{seg_count * 10 % 60}s")
    print()
    for ph in ("phase2", "phase3", "phase4"):
        items = results.get(ph, [])
        ok = sum(1 for x in items if x.get("status") == "completed")
        fail = sum(1 for x in items if x.get("status") in ("failed", "timeout"))
        print(f"  {ph}: {ok}/{len(items)} completed, {fail} failed")

    print(f"\n  --- VIDEO URLs ---")
    phase4 = results.get("phase4", [])
    for i, v in enumerate(phase4):
        url = v.get("result_url", "")
        status = v.get("status", "?")
        if url:
            print(f"  seg{i+1:02d}: {BASE}{url}  [{status}]")
        else:
            print(f"  seg{i+1:02d}: [no url]  [{status}]")

print(f"\n\n  --- WEB VIEW ---")
print(f"  http://122.51.205.94/project/{pid}")
print(f"\n  --- LOGIN ---")
print(f"  Email: sci_test@aiforge.ai")
print(f"  Password: sci2025pw")
print(f"\n{'='*60}")
print("  DONE")
print(f"{'='*60}")