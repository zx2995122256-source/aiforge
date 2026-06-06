import sys

# Read current server file
with open('/home/ubuntu/aiforge/backend/api/generate.py', 'r') as f:
    content = f.read()

# Check if already patched
if 'PRICE_10S_720P' in content:
    print("Already patched with new pricing")
    sys.exit(0)

# Find and replace _calc_video_cost function
old_func_start = 'def _calc_video_cost(model: str, duration: int, resolution: str) -> int:'
old_func_end = 'def _poll_oiioii'

# Find start index
start_idx = content.find(old_func_start)
if start_idx == -1:
    print("ERROR: Could not find _calc_video_cost function")
    sys.exit(1)

# Find end index (next function)
end_idx = content.find(old_func_end, start_idx)
if end_idx == -1:
    print("ERROR: Could not find end of _calc_video_cost function")
    sys.exit(1)

new_func = '''def _calc_video_cost(model: str, duration: int, resolution: str) -> int:
    """Calculate video cost in points (100 points = 1 RMB).
    
    Pricing based on RMB per 10s at 720p, then linear scale by duration and resolution.
    Resolution ratios: 720p=1.0, 1080p=1.29, 4K=2.14 (derived from Gemini Omni pricing).
    """
    # Price per 10s at 720p in RMB, then * 100 = points
    PRICE_10S_720P = {
        "Grok Imagine": 0.4,
        "Gemini Omni": 0.7,
        "Wan2.7": 0.6,
        "Wan2.6": 0.6,
        "Vidu Q2": 0.7,
        "Vidu Q3 Pro": 0.84,
        "Vidu Q3 Ref": 0.84,
        "Vidu Q3 Mix": 0.84,
        "Kling 2.6": 0.7,
        "Kling O1": 1.12,
        "Hailuo 2.3 Std": 0.7,
        "Hailuo 2.3 Pro": 1.12,
        "Seedance 1.5 Pro": 1.12,
    }

    base_price = PRICE_10S_720P.get(model)
    if not base_price:
        # Fallback: try to get cost_base from oiioii and scale proportionally
        try:
            models_data = proxy.get_models()
            model_info = models_data.get("video", {}).get(model, {})
            cost_base = model_info.get("cost_base", 25)
            base_price = 0.7 * (cost_base / 25)  # Proportional to Gemini (base=25 -> 0.7 RMB)
        except:
            base_price = 0.7  # Default to Gemini price

    # Duration: linear scale (10s = 1.0)
    duration_scale = duration / 10.0

    # Resolution scale: 720p=1.0, 1080p=1.29, 4K=2.14
    res_scale = 1.0
    if resolution in ("1080p", "2K"):
        res_scale = 1.29
    elif resolution in ("4K", "4k"):
        res_scale = 2.14

    # RMB -> points (x 100)
    cost_rmb = base_price * duration_scale * res_scale
    return max(1, int(round(cost_rmb * 100)))


'''

content = content[:start_idx] + new_func + content[end_idx:]

with open('/home/ubuntu/aiforge/backend/api/generate.py', 'w') as f:
    f.write(content)

print("PATCHED: generate.py with new pricing")
