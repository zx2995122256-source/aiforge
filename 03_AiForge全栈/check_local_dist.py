import os, glob

dist = r"c:\Users\Administrator\Documents\锤子Aicg\03_AiForge全栈\frontend\dist\assets"
proj = glob.glob(os.path.join(dist, "*Project*"))
for f in sorted(proj):
    size = os.path.getsize(f)
    mtime = os.path.getmtime(f)
    import datetime
    print(f"{os.path.basename(f):40s} {size:>6d}B  {datetime.datetime.fromtimestamp(mtime).strftime('%H:%M:%S')}")

print("\n--- Checking for new colors ---")
js_files = [f for f in proj if f.endswith(".js")]
if js_files:
    with open(js_files[0], "rb") as fh:
        js = fh.read().decode(errors="replace")
    checks = ["#252540", "#556688", "#1a1a2e", "onDeactivated", "onActivated"]
    for c in checks:
        print(f"  {'✅' if c in js else '❌'} {c}")
    print(f"\nJS size: {len(js)} bytes")
    print(f"File: {os.path.basename(js_files[0])}")