import sqlite3, json
db = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
db.row_factory = sqlite3.Row
row = db.execute("SELECT id, name, video_model, duration, resolution, ratio, segments_json, results_json, script FROM projects WHERE id=16").fetchone()
if row:
    print("ID:", row['id'])
    print("Name:", row['name'])
    print("Model:", row['video_model'])
    print("Duration:", row['duration'])
    print("Resolution:", row['resolution'])
    print("Ratio:", row['ratio'])
    results = json.loads(row['results_json'] or '{}')
    print("\n=== Phase2 (assets) ===")
    for i, r in enumerate(results.get('phase2', [])):
        print(f"  Asset {i}: status={r.get('status')}, name={r.get('name','')}, has_result={bool(r.get('result_url'))}")
    print("\n=== Phase3 (storyboards) ===")
    for i, r in enumerate(results.get('phase3', [])):
        print(f"  Seg {i}: status={r.get('status')}, has_result={bool(r.get('result_url'))}")
    print("\n=== Phase4 (videos) ===")
    for i, r in enumerate(results.get('phase4', [])):
        print(f"  Seg {i}: status={r.get('status')}, oiioii_id={r.get('oiioii_task_id')}, has_result={bool(r.get('result_url'))}, prompt={r.get('prompt','')[:100]}")
    print("\n=== Segments ===")
    segs = json.loads(row['segments_json'] or '[]')
    for i, s in enumerate(segs):
        print(f"  Seg {i}: title={s.get('title','')}, shots={len(s.get('shots',[]))}, assets={s.get('assets',[])}")
    print("\n=== Script ===")
    script = row['script'] or '{}'
    sd = json.loads(script)
    print("  style:", sd.get('style',''))
    print("  assets count:", len(sd.get('assets',[])))
    print("  segments count:", len(sd.get('segments',[])))
db.close()
