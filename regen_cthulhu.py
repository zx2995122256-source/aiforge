#!/usr/bin/env python3
"""Regenerate assets and videos for existing project #26"""
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
    print(f"Login failed: {r.status_code} {r.text[:200]}")
    return None

def generate_single_asset(token, project_id, idx):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{BASE}/api/project/{project_id}/asset/{idx}/generate", json={}, headers=headers, timeout=30)
    ok = r.status_code == 200
    if not ok:
        print(f"    Asset {idx} generate failed: {r.status_code} {r.text[:200]}")
    return ok

def generate_single_video(token, project_id, idx):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{BASE}/api/project/{project_id}/segment/{idx}/generate-video", json={}, headers=headers, timeout=30)
    ok = r.status_code == 200
    if not ok:
        print(f"    Video {idx} generate failed: {r.status_code} {r.text[:200]}")
    return ok

def get_project(token, project_id):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE}/api/project/{project_id}", headers=headers, timeout=10)
    if r.status_code == 200:
        return r.json()
    return None

def poll_phase(token, project_id, phase_key, timeout=1800):
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
            if time.time() - last_print > 30:
                print(f"  [{phase_key}] waiting for results...")
                last_print = time.time()
            time.sleep(10)
            continue
        all_done = all(r.get("status") in ("completed", "failed", "timeout", "skipped") for r in phase_results)
        if all_done:
            return phase_results
        done = sum(1 for r in phase_results if r.get("status") == "completed")
        running = sum(1 for r in phase_results if r.get("status") == "running")
        pending = sum(1 for r in phase_results if r.get("status") == "pending")
        failed = sum(1 for r in phase_results if r.get("status") == "failed")
        if time.time() - last_print > 30:
            print(f"  [{phase_key}] done={done} running={running} pending={pending} failed={failed} total={len(phase_results)}")
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
    print("=== Regenerating Project #26 (50万积分) ===")
    
    token = get_token()
    if not token:
        sys.exit(1)
    print(f"  Token: {token[:20]}...")
    
    project_id = 26
    proj_data = get_project(token, project_id)
    if not proj_data:
        print("Cannot access project #26")
        sys.exit(1)
    
    assets = proj_data.get("assets", [])
    segments = proj_data.get("segments", [])
    print(f"  Assets: {len(assets)}, Segments: {len(segments)}")
    
    save_dir = f"/home/ubuntu/aiforge/data/cthulhu_ep1_{project_id}"
    os.makedirs(save_dir, exist_ok=True)
    
    # Generate ALL assets
    print("\n1. Generating ALL assets...")
    for i in range(len(assets)):
        print(f"  Asset {i+1}/{len(assets)}: {assets[i].get('name','?')}")
        generate_single_asset(token, project_id, i)
        time.sleep(1)
    
    print("  Waiting for assets to complete...")
    asset_results = poll_phase(token, project_id, "phase2", timeout=900)
    if asset_results:
        done = sum(1 for r in asset_results if r.get("status") == "completed")
        failed = sum(1 for r in asset_results if r.get("status") == "failed")
        print(f"  Assets: {done} done, {failed} failed")
        
        # Retry failed up to 3 times
        for retry in range(3):
            failed_indices = [i for i, r in enumerate(asset_results) if r.get("status") == "failed"]
            if not failed_indices:
                break
            print(f"  Retry round {retry+1}: {len(failed_indices)} failed...")
            for i in failed_indices:
                generate_single_asset(token, project_id, i)
                time.sleep(2)
            asset_results = poll_phase(token, project_id, "phase2", timeout=600)
    
    # Generate ALL videos
    print("\n2. Generating ALL videos...")
    for i in range(len(segments)):
        print(f"  Video {i+1}/{len(segments)}: {segments[i].get('title','?')}")
        generate_single_video(token, project_id, i)
        time.sleep(2)
    
    print("  Waiting for videos to complete...")
    video_results = poll_phase(token, project_id, "phase4", timeout=3600)
    if video_results:
        done = sum(1 for r in video_results if r.get("status") == "completed")
        failed = sum(1 for r in video_results if r.get("status") == "failed")
        print(f"  Videos: {done} done, {failed} failed")
        
        # Retry failed up to 3 times
        for retry in range(3):
            failed_indices = [i for i, r in enumerate(video_results) if r.get("status") == "failed"]
            if not failed_indices:
                break
            print(f"  Retry round {retry+1}: {len(failed_indices)} failed...")
            for i in failed_indices:
                generate_single_video(token, project_id, i)
                time.sleep(3)
            video_results = poll_phase(token, project_id, "phase4", timeout=1800)
    
    # Download
    print("\n3. Downloading videos...")
    for i in range(len(segments)):
        print(f"  Downloading segment {i+1}/{len(segments)}...")
        success = download_video(token, project_id, i, save_dir)
        if not success:
            print(f"    FAILED segment {i+1}")
    
    print(f"\n=== DONE ===")
    files = [f for f in os.listdir(save_dir) if f.endswith(".mp4")]
    print(f"Downloaded {len(files)} videos to {save_dir}")
    for f in sorted(files):
        size = os.path.getsize(os.path.join(save_dir, f)) / 1024 / 1024
        print(f"  {f} ({size:.1f}MB)")

if __name__ == "__main__":
    main()
