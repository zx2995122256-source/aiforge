#!/usr/bin/env python3
"""Create project and generate videos via AiForge API - 2min Cthulhu"""
import requests
import json
import time
import sys
import os

BASE = "http://localhost:7862"

def get_token():
    # Register a new user for video generation
    r = requests.post(f"{BASE}/api/auth/register", json={
        "email": "video_gen@aiforge.local", "password": "Gen12345!", "nickname": "VideoGen"
    }, timeout=10)
    if r.status_code == 200:
        return r.json().get("token")
    # If already registered, login
    r = requests.post(f"{BASE}/api/auth/login", json={
        "email": "video_gen@aiforge.local", "password": "Gen12345!"
    }, timeout=10)
    if r.status_code == 200:
        return r.json().get("token")
    print(f"Login failed: {r.status_code} {r.text[:200]}")
    return None

def create_project(token, name, raw_script):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{BASE}/api/project/create", json={
        "name": name,
        "script": json.dumps({"assets": [], "segments": []}),
        "raw_script": raw_script,
        "video_model": "Gemini Omni",
        "image_model": "GPT-Image2",
        "ratio": "9:16",
        "resolution": "4K",
        "image_resolution": "4K",
        "duration": 10
    }, headers=headers, timeout=15)
    if r.status_code == 200:
        return r.json()
    print(f"Create failed: {r.status_code} {r.text[:300]}")
    return None

def ai_split(token, project_id):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{BASE}/api/project/{project_id}/ai-split", json={
        "duration_per_segment": 10
    }, headers=headers, timeout=600)
    if r.status_code == 200:
        return r.json()
    print(f"Split failed: {r.status_code} {r.text[:300]}")
    return None

def generate_single_asset(token, project_id, idx):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{BASE}/api/project/{project_id}/asset/{idx}/generate", json={}, headers=headers, timeout=30)
    return r.status_code == 200

def generate_single_video(token, project_id, idx):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{BASE}/api/project/{project_id}/segment/{idx}/generate-video", json={}, headers=headers, timeout=30)
    return r.status_code == 200

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
        if time.time() - last_print > 20:
            print(f"  [{phase_key}] done={done} running={running} pending={pending} failed={failed} total={len(phase_results)}")
            last_print = time.time()
        time.sleep(10)
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
    print("=== 深渊之岛：大航海×克苏鲁 (2min) ===")
    
    # Login
    print("1. Login...")
    token = get_token()
    if not token:
        sys.exit(1)
    print(f"  OK: {token[:20]}...")
    
    # Script - 2min, hook开头+钩子结尾
    raw_script = """【开头钩子】1623年9月13日。加勒比海，午夜。"圣卡塔琳娜号"的航海日志在此刻中断。最后一页只有四个字——"它看见我了"。

三天前。葡萄牙商船"圣卡塔琳娜号"驶入一片无雾的海域。船长若昂·德·奥利维拉站在船首，望远镜中地平线出现一座从未标注在任何海图上的黑色岛屿。岛屿呈不规则的五角形，海岸线布满巨大的黑色玄武岩柱，如同从海底生长出的肋骨。

大副塞巴斯蒂昂警告船长绕行，但若昂坚持登陆补给淡水。登陆小队划着小艇靠近海岸，发现岩柱上刻满了无法辨认的符号——既非欧洲文字，也非加勒比原住民的图腾。符号在潮湿的岩面上微微泛着磷光，像某种活物的呼吸。

随船修道士安东尼奥跪在沙滩上祈祷，他声称听到了来自地下的低语——一种不属于人类语言的震颤声，像无数舌头同时蠕动。他颤抖着翻开宗教裁判所封禁的典籍，认出那些符号属于"深渊之眼"——一个被教会抹去所有记载的古神标记。

夜幕降临，潮水退去，露出一扇隐藏在岩壁间的石门。门上雕刻着一只巨大的眼睛，瞳孔中嵌着触须环绕的漩涡图案。石门半开，内部透出幽暗的蓝绿色光芒，像深海中某种生物的呼吸。

若昂带着火把踏入石门。通道内壁覆盖着某种有机质——像皮肤，又像菌丝，随火光脉动收缩。通道越来越窄，空气变得粘稠，带着深海鱼腥和硫磺的混合气味。船员们的灯笼一个接一个熄灭，仿佛黑暗本身在吞噬光明。

通道尽头是一个巨大的地下穹顶。穹顶中央悬浮着一颗直径三米的黑色球体，表面不断翻涌着暗紫色的纹路，像一颗活着的心脏。球体周围漂浮着数百条触须状的藤蔓，从穹顶垂落，末端发出微弱的蓝绿色荧光，照亮了穹顶内壁上密密麻麻的符号。

球体表面的暗紫色纹路突然加速翻涌，一条触须猛然伸向最近的船员——水手佩德罗。触须刺入他的胸口，没有流血，佩德罗的身体却开始扭曲变形，骨骼发出碎裂声，皮肤下有什么东西在蠕动。他张开嘴想尖叫，发出的却是和地下低语相同的震颤声。

若昂拔出火枪射击球体，子弹击中表面却像被吞噬一般消失无踪。更多触须从球体射出，缠住两名船员。他们的身体在触须中溶解，化为蓝绿色的光点被球体吸收。球体的脉动越来越快，整个穹顶开始共振。

塞巴斯蒂昂在入口处大喊撤退。幸存者疯狂奔向通道出口。若昂最后看了一眼球体——它的表面浮现出一张人脸，那是佩德罗的脸，嘴在无声地张合，眼眶中是深不见底的黑暗。

逃出石门后，若昂下令立即启航。但当他们回到"圣卡塔琳娜号"时，发现船体上爬满了和通道内同样的有机质——菌丝状的物质正在缓慢吞噬船身，像某种疾病在蔓延。

若昂望着渐渐被菌丝覆盖的船帆，做出了最后的决定：点燃火药库。他让塞巴斯蒂昂带着幸存者乘小艇离开，自己留在船上。火光冲天，"圣卡塔琳娜号"在爆炸中碎裂，燃烧的残骸照亮了海面。

但若昂没有死——在火焰中，他看见球体从海底升起，比岛屿更大，触须伸向天空，遮蔽了月亮。那不是岛屿，那是沉睡在海底的某种巨大生物露出水面的背脊。球体是它的心脏，而那些符号是它的梦。

【结尾钩子】塞巴斯蒂昂的小艇在巨浪中颠簸。他回头望去，看见海面上漂浮着若昂的帽子——帽子下面，是若昂的脸。他活着，但眼睛已经不再是人类的眼睛。瞳孔中嵌着触须环绕的漩涡，嘴角上扬，露出一个不属于人类的微笑。他缓缓沉入海面之下，低语声从四面八方传来："你也会回来的。"海面恢复平静。航海日志的最后一页，墨迹未干。"""

    # Create project
    print("2. Creating project...")
    proj = create_project(token, "深渊之岛EP1-大航海克苏鲁", raw_script)
    if not proj:
        sys.exit(1)
    project_id = proj.get("id")
    print(f"  Project ID: {project_id}")
    
    # AI Split
    print("3. AI splitting...")
    split_result = ai_split(token, project_id)
    if not split_result:
        sys.exit(1)
    
    # Check split quality
    proj_data = get_project(token, project_id)
    assets = proj_data.get("assets", [])
    segments = proj_data.get("segments", [])
    
    print(f"\n  === SPLIT RESULT ===")
    print(f"  Assets: {len(assets)}")
    for a in assets:
        print(f"    - {a.get('name','?')} ({a.get('type','?')}) is_primary={a.get('is_primary',True)}")
    print(f"  Segments: {len(segments)}")
    for i, s in enumerate(segments):
        shots = s.get("shots", [])
        seg_assets = s.get("assets", [])
        print(f"    段{i+1}: {s.get('title','?')} | {len(shots)}shots | assets={seg_assets}")
    
    # Verify segment count is reasonable for 2min
    if len(segments) < 10:
        print(f"\n  WARNING: Only {len(segments)} segments for 2min! Expected ~12. Check split quality.")
    elif len(segments) > 15:
        print(f"\n  WARNING: {len(segments)} segments might be too many for 2min.")
    else:
        print(f"\n  Segment count looks good: {len(segments)} segments for ~2min")
    
    # Save split result
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", f"cthulhu_ep1_{project_id}")
    os.makedirs(save_dir, exist_ok=True)
    with open(os.path.join(save_dir, "split_result.json"), "w", encoding="utf-8") as f:
        json.dump({"assets": assets, "segments": segments}, f, indent=2, ensure_ascii=False)
    
    # Generate assets
    print("\n4. Generating assets...")
    for i in range(len(assets)):
        print(f"  Asset {i+1}/{len(assets)}: {assets[i].get('name','?')}")
        generate_single_asset(token, project_id, i)
        time.sleep(2)
    
    print("  Waiting for assets...")
    asset_results = poll_phase(token, project_id, "phase2", timeout=600)
    if asset_results:
        done = sum(1 for r in asset_results if r.get("status") == "completed")
        failed = sum(1 for r in asset_results if r.get("status") == "failed")
        print(f"  Assets: {done} done, {failed} failed")
        
        # Retry failed
        for i, r in enumerate(asset_results):
            if r.get("status") == "failed":
                print(f"  Retrying asset {i}...")
                generate_single_asset(token, project_id, i)
                time.sleep(2)
        if failed > 0:
            asset_results = poll_phase(token, project_id, "phase2", timeout=600)
    
    # Generate videos
    print("\n5. Generating videos...")
    proj_data = get_project(token, project_id)
    segments = proj_data.get("segments", [])
    
    for i in range(len(segments)):
        print(f"  Video {i+1}/{len(segments)}: {segments[i].get('title','?')}")
        generate_single_video(token, project_id, i)
        time.sleep(3)
    
    print("  Waiting for videos...")
    video_results = poll_phase(token, project_id, "phase4", timeout=1800)
    if video_results:
        done = sum(1 for r in video_results if r.get("status") == "completed")
        failed = sum(1 for r in video_results if r.get("status") == "failed")
        print(f"  Videos: {done} done, {failed} failed")
        
        # Retry failed (up to 3 rounds)
        for retry_round in range(3):
            failed_indices = [i for i, r in enumerate(video_results) if r.get("status") == "failed"]
            if not failed_indices:
                break
            print(f"  Retry round {retry_round+1}: {len(failed_indices)} failed videos...")
            for i in failed_indices:
                print(f"    Retrying video {i}...")
                generate_single_video(token, project_id, i)
                time.sleep(3)
            video_results = poll_phase(token, project_id, "phase4", timeout=1800)
            if video_results:
                done = sum(1 for r in video_results if r.get("status") == "completed")
                failed = sum(1 for r in video_results if r.get("status") == "failed")
                print(f"    After retry: {done} done, {failed} failed")
    
    # Download videos
    print("\n6. Downloading videos...")
    proj_data = get_project(token, project_id)
    segments = proj_data.get("segments", [])
    
    for i in range(len(segments)):
        print(f"  Downloading segment {i+1}/{len(segments)}...")
        success = download_video(token, project_id, i, save_dir)
        if not success:
            print(f"    FAILED to download segment {i+1}")
    
    # Summary
    print(f"\n=== COMPLETE ===")
    print(f"Project: {project_id}")
    print(f"Videos saved to: {save_dir}")
    
    # List downloaded files
    files = [f for f in os.listdir(save_dir) if f.endswith(".mp4")]
    print(f"Downloaded {len(files)} videos:")
    for f in sorted(files):
        size = os.path.getsize(os.path.join(save_dir, f)) / 1024 / 1024
        print(f"  {f} ({size:.1f}MB)")

if __name__ == "__main__":
    main()
