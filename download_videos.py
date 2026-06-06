import requests, json, os

BASE = "http://localhost:7862"
LOCAL_DIR = "/home/ubuntu/aiforge/data/abyss_road_ep1_27"
os.makedirs(LOCAL_DIR, exist_ok=True)

# Login
r = requests.post(f"{BASE}/api/auth/login", json={"email": "test@test.com", "password": "test123"})
token = r.json().get("token")
headers = {"Authorization": f"Bearer {token}"}

# Get results from DB
import sqlite3
conn = sqlite3.connect('backend/data/aiforge.db')
c = conn.cursor()
c.execute("SELECT results_json FROM projects WHERE id=27")
row = c.fetchone()
results = json.loads(row[0])

seg_titles = [
    "01_开头钩子_日志最后一页",
    "02_迷雾中的信号",
    "03_登陆黑色岛屿",
    "04_石碑与预言",
    "05_深入地下",
    "06_祭坛觉醒",
    "07_深渊凝视",
    "08_逃离岛屿",
    "09_船上的异变",
    "10_火攻与挣扎",
    "11_深渊显现",
    "12_结尾钩子_深渊之路",
]

phase4 = results.get("phase4", [])
print(f"Phase4: {len(phase4)} items")

for i, item in enumerate(phase4):
    status = item.get("status", "?")
    if status != "completed":
        print(f"  {i}: SKIPPED ({status})")
        continue

    result_url = item.get("result_url", "")
    if not result_url:
        print(f"  {i}: NO result_url")
        continue

    # result_url is like /api/gen/file/1314
    full_url = f"{BASE}{result_url}"
    r = requests.get(full_url, headers=headers, stream=True)
    if r.status_code != 200:
        print(f"  {i}: DOWNLOAD FAILED ({r.status_code})")
        continue

    title = seg_titles[i] if i < len(seg_titles) else f"seg{i:02d}"
    fname = f"seg{title}.mp4"
    fpath = os.path.join(LOCAL_DIR, fname)

    with open(fpath, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    size_mb = os.path.getsize(fpath) / 1024 / 1024
    print(f"  {i}: {fname} ({size_mb:.1f}MB)")

print("\nAll videos downloaded!")
