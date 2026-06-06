#!/usr/bin/env python3
"""Regenerate project #26 with lower resolution - 720p video, 1K images"""
import requests
import json
import time
import sys
import os

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

def update_project_settings(token, project_id):
    """Update project to use 720p video and 1K images"""
    headers = {"Authorization": f"Bearer {token}"}
    # Get current project data
    proj = get_project(token, project_id)
    if not proj:
        return False
    
    # Update via PUT script endpoint - just update the settings fields
    script = proj.get("script", {})
    if isinstance(script, str):
        script = json.loads(script)
    
    # We need to update the project's video_model, resolution etc
    # The PUT /project/{id}/script only updates script, not settings
    # Let's use a direct DB update instead
    return True

def generate_single_video(token, project_id, idx):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{BASE}/api/project/{project_id}/segment/{idx}/generate-video", json={}, headers=headers, timeout=30)
    ok = r.status_code == 200
    if not ok:
        print(f"    Video {idx} failed: {r.status_code} {r.text[:200]}")
    return ok

def poll_phase(token, project_id, phase_key, timeout=3600):
    start = time.time()
    last_print = 0
    while time.time() - start < timeout:
        proj = get_project(token, project_id)
        if not proj:
            time.sleep(10)
            continue
        results = proj.get("results", {})
        phase_results = results.get(phase_key, [])
        if not phase_results:
            if time.time() - last_print > 60:
                print(f"  [{phase_key}] waiting...")
                last_print = time.time()
            time.sleep(15)
            continue
        all_done = all(r.get("status") in ("completed", "failed", "timeout", "skipped") for r in phase_results)
        if all_done:
            return phase_results
        done = sum(1 for r in phase_results if r.get("status") == "completed")
        running = sum(1 for r in phase_results if r.get("status") == "running")
        failed = sum(1 for r in phase_results if r.get("status") == "failed")
        if time.time() - last_print > 60:
            print(f"  [{phase_key}] done={done} running={running} failed={failed} total={len(phase_results)}")
            last_print = time.time()
        time.sleep(15)
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
    print("=== Regenerating Project #26 with 720p video ===")
    
    token = get_token()
    if not token:
        sys.exit(1)
    
    project_id = 26
    
    # First, update project settings in DB to use 720p
    import sqlite3
    c = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
    c.execute("UPDATE projects SET video_model='Gemini Omni', resolution='720p', image_resolution='1K', ratio='9:16' WHERE id=26")
    c.commit()
    c.close()
    print("  Updated project settings: 720p video, 1K images")
    
    # Clear phase4 results
    c = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
    r = c.execute('SELECT results_json FROM projects WHERE id=26').fetchone()
    results = json.loads(r[0]) if r and r[0] else {}
    results["phase4"] = []
    c.execute("UPDATE projects SET results_json=? WHERE id=26", (json.dumps(results, ensure_ascii=False),))
    c.commit()
    c.close()
    print("  Cleared phase4 results")
    
    proj_data = get_project(token, project_id)
    segments = proj_data.get("segments", [])
    print(f"  Segments: {len(segments)}")
    
    save_dir = f"/home/ubuntu/aiforge/data/cthulhu_ep1_{project_id}"
    os.makedirs(save_dir, exist_ok=True)
    
    # Generate videos one at a time to avoid timeout
    print("\n1. Generating videos (one at a time)...")
    for i in range(len(segments)):
        print(f"  Submitting video {i+1}/{len(segments)}: {segments[i].get('title','?')}")
        generate_single_video(token, project_id, i)
        time.sleep(5)  # Wait between submissions
    
    print("  Waiting for videos...")
    video_results = poll_phase(token, project_id, "phase4", timeout=3600)
    if video_results:
        done = sum(1 for r in video_results if r.get("status") == "completed")
        failed = sum(1 for r in video_results if r.get("status") == "failed")
        print(f"  Videos: {done} done, {failed} failed")
        
        # Retry failed
        for retry in range(5):
            failed_indices = [i for i, r in enumerate(video_results) if r.get("status") == "failed"]
            if not failed_indices:
                break
            print(f"  Retry round {retry+1}: {len(failed_indices)} failed...")
            for i in failed_indices:
                generate_single_video(token, project_id, i)
                time.sleep(5)
            video_results = poll_phase(token, project_id, "phase4", timeout=1800)
    
    # Download
    print("\n2. Downloading videos...")
    for i in range(len(segments)):
        print(f"  Downloading segment {i+1}/{len(segments)}...")
        download_video(token, project_id, i, save_dir)
    
    print(f"\n=== DONE ===")
    files = [f for f in os.listdir(save_dir) if f.endswith(".mp4")]
    print(f"Downloaded {len(files)} videos to {save_dir}")

if __name__ == "__main__":
    main()
