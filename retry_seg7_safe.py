#!/usr/bin/env python3
"""Retry segment 7 with safer prompt - remove body horror descriptions"""
import requests
import json
import time
import sys
import os
import sqlite3

BASE = "http://localhost:7862"

def get_token():
    r = requests.post(f"{BASE}/api/auth/login", json={
        "email": "video_gen@aiforge.local", "password": "Gen12345!"
    }, timeout=10)
    if r.status_code == 200:
        return r.json().get("token")
    return None

def get_project(token, project_id):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE}/api/project/{project_id}", headers=headers, timeout=10)
    if r.status_code == 200:
        return r.json()
    return None

def download_video(token, project_id, seg_idx, save_dir):
    headers = {"Authorization": f"Bearer {token}"}
    proj = get_project(token, project_id)
    if not proj:
        return False
    results = proj.get("results", {})
    for phase_key in ["phase4", "phase3"]:
        phase_results = results.get(phase_key, [])
        if seg_idx < len(phase_results):
            r = phase_results[seg_idx]
            if r.get("status") != "completed":
                continue
            result_url = r.get("result_url", "")
            if not result_url:
                continue
            if result_url.startswith("/api/"):
                url = f"{BASE}{result_url}"
            else:
                url = result_url
            try:
                resp = requests.get(url, headers=headers, timeout=120, stream=True)
                if resp.status_code == 200:
                    seg_title = ""
                    segments = proj.get("segments", [])
                    if seg_idx < len(segments):
                        seg_title = segments[seg_idx].get("title", "").replace(" ", "_")[:20]
                    filepath = os.path.join(save_dir, f"seg{seg_idx+1:02d}_{seg_title}.mp4")
                    with open(filepath, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    size_mb = os.path.getsize(filepath) / 1024 / 1024
                    print(f"  Downloaded: {os.path.basename(filepath)} ({size_mb:.1f}MB)")
                    return True
            except Exception as e:
                print(f"  Download error: {e}")
    return False

def main():
    token = get_token()
    if not token:
        sys.exit(1)
    
    project_id = 26
    
    # Modify segment 7's shots to remove body horror
    c = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
    r = c.execute('SELECT segments_json FROM projects WHERE id=26').fetchone()
    segments = json.loads(r[0]) if r and r[0] else []
    
    if len(segments) > 6:
        seg7 = segments[6]
        # Replace horror descriptions with safer alternatives
        for shot in seg7.get("shots", []):
            visual = shot.get("visual", "")
            # Replace body horror with mystical effects
            visual = visual.replace("触须刺入他的胸口", "触须伸向佩德罗")
            visual = visual.replace("没有流血", "")
            visual = visual.replace("身体却开始扭曲变形", "被蓝绿色光芒笼罩")
            visual = visual.replace("骨骼发出碎裂声", "周围空气剧烈震动")
            visual = visual.replace("皮肤下有什么东西在蠕动", "身体开始发出蓝绿色荧光")
            visual = visual.replace("他张开嘴想尖叫，发出的却是和地下低语相同的震颤声", "他无声地张嘴，蓝绿色光点从他身上飘出")
            visual = visual.replace("缠住两名船员", "伸向两名船员")
            visual = visual.replace("他们的身体在触须中溶解", "他们被蓝绿色光芒包裹")
            visual = visual.replace("化为蓝绿色的光点被球体吸收", "化为光点消散在球体中")
            shot["visual"] = visual
        
        # Also update segment title
        seg7["title"] = "球体苏醒与光点吞噬"
        
        c.execute("UPDATE projects SET segments_json=? WHERE id=26", (json.dumps(segments, ensure_ascii=False),))
        c.commit()
        print("Updated segment 7 with safer descriptions")
    
    # Clear phase4 result for segment 7
    r = c.execute('SELECT results_json FROM projects WHERE id=26').fetchone()
    results = json.loads(r[0]) if r and r[0] else {}
    phase4 = results.get("phase4", [])
    if len(phase4) > 6:
        phase4[6] = {"status": "pending", "title": "球体苏醒与光点吞噬"}
        results["phase4"] = phase4
        c.execute("UPDATE projects SET results_json=? WHERE id=26", (json.dumps(results, ensure_ascii=False),))
        c.commit()
        print("Cleared phase4 result for segment 7")
    c.close()
    
    # Regenerate segment 7
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{BASE}/api/project/{project_id}/segment/6/generate-video", json={}, headers=headers, timeout=30)
    print(f"Generate video response: {r.status_code}")
    
    # Wait for completion
    print("Waiting for segment 7...")
    for _ in range(120):
        time.sleep(15)
        proj = get_project(token, project_id)
        phase4 = proj.get("results", {}).get("phase4", [])
        if len(phase4) > 6 and phase4[6].get("status") in ("completed", "failed", "timeout"):
            print(f"  Segment 7 status: {phase4[6].get('status')}")
            if phase4[6].get("status") == "completed":
                # Download
                save_dir = f"/home/ubuntu/aiforge/data/cthulhu_ep1_{project_id}"
                download_video(token, project_id, 6, save_dir)
            else:
                print(f"  Error: {phase4[6].get('error','?')}")
            break
    
    # Final list
    save_dir = f"/home/ubuntu/aiforge/data/cthulhu_ep1_{project_id}"
    files = [f for f in os.listdir(save_dir) if f.endswith(".mp4")]
    print(f"\n=== FINAL: {len(files)} videos ===")
    for f in sorted(files):
        size = os.path.getsize(os.path.join(save_dir, f)) / 1024 / 1024
        print(f"  {f} ({size:.1f}MB)")

if __name__ == "__main__":
    main()
