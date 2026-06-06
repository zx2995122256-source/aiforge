import json, sys
d = json.load(sys.stdin)
acts = d.get("accounts", [])
active = [a for a in acts if a["status"]=="active"]
exhausted = [a for a in acts if a["status"]=="exhausted"]
total_pts = sum(a.get("points",0) for a in active)
print(f"Total: {len(acts)}  Active: {len(active)}  Exhausted: {len(exhausted)}")
print(f"Active points sum: {total_pts}")
if active:
    pts = [a["points"] for a in active]
    print(f"Min: {min(pts)}  Max: {max(pts)}")
