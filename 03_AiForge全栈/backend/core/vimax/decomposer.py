"""Visual Decomposer — adapted from ViMax StoryboardArtist.decompose_visual_description.
Breaks each shot into first_frame + last_frame + motion for better video generation."""

import json
import re
from config import LLM_API_URL, LLM_API_KEY, LLM_MODEL
import requests as http_req


def _call_llm_json(system_prompt: str, user_prompt: str, llm_config: dict = None) -> dict:
    """Call LLM and parse JSON from response."""
    cfg = llm_config or {}
    api_url = cfg.get("api_url") or LLM_API_URL
    api_key = cfg.get("api_key") or LLM_API_KEY
    model = cfg.get("model") or LLM_MODEL
    temperature = cfg.get("temperature", 0.5)
    max_tokens = cfg.get("max_tokens", 4096)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    r = http_req.post(api_url, headers=headers, json=body, timeout=120)
    if r.status_code != 200:
        raise Exception(f"LLM API error {r.status_code}: {r.text[:200]}")

    text = r.json()["choices"][0]["message"]["content"]
    json_str = text.strip()
    if "```json" in json_str:
        json_str = json_str.split("```json")[1].split("```")[0].strip()
    elif "```" in json_str:
        json_str = json_str.split("```")[1].split("```")[0].strip()
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        match = re.search(r'\{[\s\S]*\}', json_str)
        if match:
            return json.loads(match.group())
        raise Exception(f"Cannot parse JSON: {text[:300]}")


DECOMPOSE_PROMPT = """[Role]
You are a professional visual text analyst, proficient in cinematic language and shot narration.

[Task]
Decompose a shot's visual description into three parts:
- first_frame: Static image at the beginning of the shot
- last_frame: Static image at the end of the shot
- motion: All movements between first and last frame (camera + on-screen elements)

[Input]
- Visual description enclosed in <VISUAL_DESC> and </VISUAL_DESC>
- Characters enclosed in <CHARACTERS> and </CHARACTERS>

[Output]
JSON object:
{
  "first_frame": "Detailed description of the first frame. Must be a pure snapshot with no ongoing actions. Include: shot type, angle, composition, character positions, lighting, colors.",
  "last_frame": "Detailed description of the last frame. Pure snapshot reflecting final state after all motion.",
  "motion": "All movements between frames. Use professional cinematic terminology for camera (dolly, pan, zoom, etc.). Refer to characters by visible features NOT names. E.g. 'the woman in white dress' not 'Alice'.",
  "variation_type": "small/medium/large",
  "video_prompt": "A complete English prompt for AI video generation combining first_frame + motion + last_frame. Should be a single coherent paragraph describing the full shot dynamics."
}

[Guidelines]
- First and last frame must be pure snapshots, no ongoing actions
- In motion description, use character's visible features to refer to them, NOT names
- Variation types: small=minor changes (expression, pose), medium=new character or turn around, large=major composition change
- video_prompt must be in English, detailed, suitable for AI video models
- The language of first_frame/last_frame/motion should match the input language"""


class VisualDecomposer:
    """Decompose shot visual descriptions into first_frame + last_frame + motion for better video prompts."""

    def decompose_shot(self, visual_desc: str, characters: list = None, llm_config: dict = None) -> dict:
        """Returns {first_frame, last_frame, motion, variation_type, video_prompt}."""
        chars_str = ""
        if characters:
            chars_str = "\n".join([f"{c.get('name','?')}: {c.get('static_features','')}; {c.get('dynamic_features','')}" for c in characters])

        user_prompt = f"<VISUAL_DESC>\n{visual_desc}\n</VISUAL_DESC>\n\n<CHARACTERS>\n{chars_str}\n</CHARACTERS>"

        return _call_llm_json(DECOMPOSE_PROMPT, user_prompt, llm_config=llm_config)

    def build_video_prompt(self, shot: dict, decomposed: dict = None) -> str:
        """Build a complete English video prompt from shot data + optional decomposition.
        If decomposed is provided, uses its video_prompt. Otherwise builds from shot fields."""
        if decomposed and decomposed.get("video_prompt"):
            return decomposed["video_prompt"]

        # Fallback: build from shot fields
        parts = []
        camera = shot.get("camera", "locked-off")
        visual = shot.get("visual", "")
        lighting = shot.get("lighting", "")
        audio = shot.get("audio", "")
        dialogue = shot.get("dialogue", "")

        parts.append(f"Camera: {camera}.")
        if visual:
            parts.append(visual)
        if lighting:
            parts.append(f"Lighting: {lighting}")
        if audio:
            parts.append(f"Audio: {audio}")
        if dialogue:
            parts.append(f"Dialogue: {dialogue}")

        return ". ".join(parts)
