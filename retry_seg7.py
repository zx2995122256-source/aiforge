#!/usr/bin/env python3
"""Retry failed segment 7 and download all videos to local"""
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

def generate_single_video(token, project_id, idx):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{BASE}/api/project/{project_id}/segment/{idx}/generate-video", json={}, headers=headers, timeout=30)
    return r.status_code == 200

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
    
    # Check current status
    proj = get_project(token, project_id)
    results = proj.get("results", {})
    phase4 = results.get("phase4", [])
    
    # Find failed segments
    failed = [i for i, r in enumerate(phase4) if r.get("status") == "failed"]
    print(f"Failed segments: {failed}")
    
    # Retry failed
    for i in failed:
        print(f"Retrying segment {i}...")
        generate_single_video(token, project_id, i)
    
    if failed:
        # Wait for completion
        print("Waiting for retry...")
        for _ in range(120):  # 30 min max
            time.sleep(15)
            proj = get_project(token, project_id)
            phase4 = proj.get("results", {}).get("phase4", [])
            all_done = all(r.get("status") in ("completed", "failed", "timeout") for r in phase4)
            if all_done:
                break
        
        # Check results
        for i in failed:
            if i < len(phase4) and phase4[i].get("status") == "completed":
                print(f"  Segment {i} completed!")
            else:
                print(f"  Segment {i} still failed: {phase4[i].get('error','?') if i < len(phase4) else 'no data'}")
    
    # Download all videos
    save_dir = f"/home/ubuntu/aiforge/data/cthulhu_ep1_{project_id}"
    os.makedirs(save_dir, exist_ok=True)
    
    segments = proj.get("segments", [])
    print(f"\nDownloading all {len(segments)} videos...")
    for i in range(len(segments)):
        download_video(token, project_id, i, save_dir)
    
    # List files
    print(f"\n=== FILES ===")
    files = [f for f in os.listdir(save_dir) if f.endswith(".mp4")]
    for f in sorted(files):
        size = os.path.getsize(os.path.join(save_dir, f)) / 1024 / 1024
        print(f"  {f} ({size:.1f}MB)")

if __name__ == "__main__":
    main()
