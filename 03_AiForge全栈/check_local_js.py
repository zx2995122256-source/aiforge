import os, glob

dist = r"c:\Users\Administrator\Documents\锤子Aicg\03_AiForge全栈\frontend\dist\assets"
proj = glob.glob(os.path.join(dist, "*Project*.js"))
if proj:
    with open(proj[0], "rb") as fh:
        js = fh.read().decode(errors="replace")
    
    # Search for activated related patterns
    for term in ["onActivated", "onDeactivated", "activated", "deactivated", "_alive", "stopPolling", "fetchProjects", "Deactivated", "Activated"]:
        count = js.count(term)
        if count:
            idx = js.find(term)
            print(f"  ✅ '{term}' found {count}x at pos {idx}")
            print(f"     context: {js[max(0,idx-20):idx+80]}")
        else:
            print(f"  ❌ '{term}' not found")
    
    print(f"\nTotal JS: {len(js)} bytes")