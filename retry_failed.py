import requests, json, time

BASE = "http://localhost:7862"

# Login
r = requests.post(f"{BASE}/api/auth/login", json={"email": "test@test.com", "password": "test123"})
token = r.json().get("token")
headers = {"Authorization": f"Bearer {token}"}

# Get current project data
r = requests.get(f"{BASE}/api/project/27", headers=headers)
proj = r.json()

# Modify segment 1 (迷雾中的信号) - safer descriptions
segs = proj.get("segments", [])

segs[1]["shots"] = [
    {"time":"0s-4s","type":"WS","camera":"crane shot rising above ship","visual":"Aerial view of a 17th century sailing ship surrounded by thick green-tinted fog on the ocean. The fog swirls in slow spiral patterns around the vessel. Strange blue-green lights pulse beneath the water surface in rhythmic patterns. The ship appears small and isolated in the vast fog-covered sea.","lighting":"Overhead fog diffuses all light, green tint everywhere, blue-green pulses from below","dialogue":"","audio":"Deep underwater pulse, fog swirling, distant whale-like moan","transition":"[cut]"},
    {"time":"4s-7s","type":"MS","camera":"handheld, following woman at bow","visual":"A woman in explorer clothing stands at the bow rail of the ship, holding a dark green stone amulet. The amulet glows faintly with blue-green light, pulsing gently. She stares into the fog ahead with an expression of curiosity and unease. The amulet chain is taut in her hand.","lighting":"Amulet emits soft blue-green glow on her face, fog backlighting creates silhouette edges","dialogue":"Isabella (whispered): The amulet... it is resonating with something. Something ahead.","audio":"Amulet humming softly, water lapping against hull, wind in rigging","transition":"[cut]"},
    {"time":"7s-10s","type":"MS","camera":"whip pan to starboard","visual":"Through the fog on the starboard side, a dark landmass emerges. A small volcanic island with black basalt rock formations jutting from the sea. Green-tinged clouds hang above it. Ancient stone pillars are visible on the plateau. The fog parts slightly to reveal the island.","lighting":"Island lit by eerie green cloud-filtered light, fog creates depth layers, no warm tones","dialogue":"Fernando (shouting from behind): Land! Captain, land off starboard!","audio":"Fog parting with a soft whoosh, waves crashing on rocks, wind picking up","transition":"[cut]"}
]

# Modify segment 11 (结尾钩子) - safer descriptions
segs[11]["shots"] = [
    {"time":"0s-4s","type":"WS","camera":"crane shot rising above ship","visual":"A 17th century sailing ship moves forward into a wide channel of green-lit ocean. The fog has retreated, replaced by vast bioluminescent water. The horizon glows intensely green. As the camera rises, the glowing patterns in the water form a single massive spiral shape, with the green glow pulsing at its center like a beacon. The ship is tiny against this vast luminous ocean.","lighting":"Bioluminescent ocean patterns as primary light, green horizon glow intensifying, ship dark silhouette","dialogue":"","audio":"Deep resonant tone, ocean current rushing, ship groaning under speed","transition":"[cut]"},
    {"time":"4s-7s","type":"CU","camera":"slow push on woman at the bow","visual":"A woman stands at the bow of the ship, wind blowing her hair, a faint blue-green pattern glowing on her chest through her shirt. She looks ahead with calm determination. Her eyes reflect the green glow on the horizon. She reaches her hand toward the distant light. Behind her, a man watches, hand on his sword, unable to stop what has begun.","lighting":"Green glow from ahead lighting her face, pattern on chest pulsing, wind and sea spray","dialogue":"Isabella (voiceover, calm and clear): We thought we discovered the unknown. But the unknown was waiting for us. And now, there is no turning back.","audio":"Wind howling, deep resonant tone harmonizing with her voice, ship speeding through water","transition":"[hard cut to black]"},
    {"time":"7s-10s","type":"ECU","camera":"locked-off, dark screen","visual":"Black screen. Two seconds of silence. Then a single amber-colored light appears in the darkness, shaped like a narrow vertical slit. It glows steadily. Then text fades in: THE ABYSS ROAD - Episode II. The amber light remains as the text fades. Then black.","lighting":"Pure black, then amber glow, then black","dialogue":"","audio":"Two seconds of silence. Then a single slow heartbeat. The light appears. Silence. Title card with deep resonant tone. End.","transition":"[fade to black]"}
]

# Save modified segments
r = requests.put(f"{BASE}/api/project/27/script", headers=headers, json={
    "raw_script": proj.get("raw_script", ""),
    "segments": segs,
    "assets": proj.get("assets", []),
    "style": proj.get("style", ""),
    "aspect_ratio": "9:16",
    "video_model": "Gemini Omni",
    "video_duration": 10,
    "video_resolution": "720p"
})
print("Save script:", r.status_code, r.text[:200] if r.status_code != 200 else "OK")

# Retry segment 1 (phase=4, item_index=1)
print("\nRetrying segment 1...")
r = requests.post(f"{BASE}/api/project/27/retry/4/1", headers=headers)
print(f"  Retry seg1: {r.status_code} {r.text[:200]}")

# Retry segment 11 (phase=4, item_index=11)
print("Retrying segment 11...")
r = requests.post(f"{BASE}/api/project/27/retry/4/11", headers=headers)
print(f"  Retry seg11: {r.status_code} {r.text[:200]}")

print("\nRetries submitted!")
