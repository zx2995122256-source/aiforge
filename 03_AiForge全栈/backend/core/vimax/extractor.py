"""Character & Storyboard Extractor — adapted from ViMax CharacterExtractor + StoryboardArtist.
Uses direct HTTP to sensenova instead of langchain."""

import json
import re
from config import LLM_API_URL, LLM_API_KEY, LLM_MODEL
import requests as http_req


def _call_llm_json(system_prompt: str, user_prompt: str, llm_config: dict = None) -> dict:
    """Call LLM and parse JSON from response. Returns parsed dict."""
    cfg = llm_config or {}
    api_url = cfg.get("api_url") or LLM_API_URL
    api_key = cfg.get("api_key") or LLM_API_KEY
    model = cfg.get("model") or LLM_MODEL
    temperature = cfg.get("temperature", 0.5)
    max_tokens = cfg.get("max_tokens", 8192)
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

    # Extract JSON from response
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
        raise Exception(f"Cannot parse JSON from LLM response: {text[:300]}")


# ==================== Character Extraction ====================

CHARACTER_EXTRACT_PROMPT = """[Role]
You are a professional character designer and script analyst for film/animation production.

[Task]
Analyze the script and extract ALL characters as visual assets for AI image generation. Each character becomes a reference sheet that will be used to generate consistent images across all scenes.

[CRITICAL RULE: Multi-Form Characters]
If a character appears in MULTIPLE visually distinct forms/states, you MUST create SEPARATE entries for each form. The PRIMARY form (most frequently appearing / default appearance) should be generated first, and DERIVED forms will use the primary form's generated image as a reference to maintain character consistency.

Examples of multi-form characters:
- A character who transforms: "凌辰-人形" (primary) → "凌辰-Q版态" (derived, references 人形)
- A character with before/after: "沈清晏-守灵" (primary) → "沈清晏-出嫁" (derived, references 守灵)
- A character in different outfits: "江雪凝-宫装" (primary) → "江雪凝-便装" (derived, references 宫装)

Name format: "角色名-形态描述"
The primary form gets reference_form=null (generated from scratch).
Derived forms get reference_form="角色名-主形态名" (will use that form's generated image as reference input).

[Input]
Script enclosed in <SCRIPT> and </SCRIPT>.

[Output]
JSON object with a "characters" array. Each element:
{
  "name": "角色名-形态描述 (e.g. 凌辰-人形, 凌辰-Q版态, 沈清晏-守灵)",
  "base_name": "Original character name without form suffix (e.g. 凌辰, 沈清晏)",
  "form": "Form/state identifier (e.g. 人形, Q版态, 守灵, 出嫁)",
  "reference_form": "Name of the primary form to use as reference image when generating this form. null for primary forms. e.g. '凌辰-人形' for the Q版态 entry.",
  "is_primary": true/false,
  "static_features": "UNCHANGING physical traits shared across ALL forms: face shape, eye color, body type, height, skin tone, hair color/length. Be extremely specific — this is what makes the character the SAME PERSON across all forms.",
  "dynamic_features": "THIS FORM's specific clothing, accessories, held items, body proportions (if different from normal, e.g. Q版 = 2-head-body chibi proportions). Describe in enough detail for an artist to draw.",
  "is_visible": true/false,
  "prompt": "English prompt for AI character reference sheet generation. Use this EXACT format:\n\nSplit composition character reference board, left side extreme close-up portrait, right side three-view turnaround (front/90/side/back), full body standing, clean professional layout.\n\nLeft: ultra detailed front face close-up, [face shape, eyebrows, eyes, skin tone, hairstyle, any distinctive marks], visible skin pores and micro skin texture, subtle subsurface scattering, natural skin imperfections (not plastic smooth).\n\nRight: front view (head completely removed, neck-down only, no face shown), side view (with head), back view (with head), wearing [outfit description], [body proportions, hand size, posture], consistent lighting and material quality across all views, pure white background.\n\nBottom: clean white horizontal bar with bold black Chinese text '[Character Name] Age [Number] Character Reference'.\n\nOverall: 35mm film, Kodak Vision3 500T, warm amber tones, candlelight aesthetic, soft diffusion, romantic skin glow, 9:16 vertical, 1152x2048, high resolution textures, not blurry, not plastic smooth."
}

[Guidelines]
- MULTI-FORM: If a character changes appearance significantly, create separate entries. Mark the most common/default form as is_primary=true, others as is_primary=false with reference_form pointing to the primary.
- SINGLE-FORM: If a character's appearance stays consistent, use one entry with form="默认", is_primary=true, reference_form=null
- static_features must be SPECIFIC and VISUAL: NOT "beautiful" but "oval face, high cheekbones, almond eyes with slight upward tilt, thin lips"
- dynamic_features for derived forms should emphasize WHAT CHANGES from the primary form, not repeat shared traits
- Different characters MUST have DISTINCT appearances — no two characters should look similar
- prompt MUST be in English. For derived forms, the prompt should start by referencing the base character then describe the transformation
- name/static_features/dynamic_features use the SAME language as the script
- DO NOT skip minor characters — even characters with one line should be extracted if they appear on screen
- For non-human characters (creatures, animals, spirits), describe their visual form in the same detail"""


class CharacterExtractor:
    """Extract characters from script with structured output."""

    def extract(self, script: str, llm_config: dict = None) -> list:
        """Returns list of character dicts."""
        user_prompt = f"<SCRIPT>\n{script}\n</SCRIPT>"
        result = _call_llm_json(CHARACTER_EXTRACT_PROMPT, user_prompt, llm_config=llm_config)
        characters = result.get("characters", [])
        # Ensure each character has required fields
        for c in characters:
            if not c.get("base_name"):
                c["base_name"] = c.get("name", "unknown")
            if not c.get("form"):
                c["form"] = "默认"
            if not c.get("prompt"):
                c["prompt"] = f"A character named {c.get('name', 'unknown')}. {c.get('static_features', '')} {c.get('dynamic_features', '')} Full body front view, character reference sheet, photorealistic, clean neutral background."
        return characters


# ==================== Storyboard Extraction ====================

STORYBOARD_EXTRACT_PROMPT = """[Role]
You are a master filmmaker who has studied under the greatest directors in cinema history. You understand that film is NOT a sequence of events — it is a sequence of DECISIONS. Every frame is a choice about what the audience sees, hears, and feels. You think in terms of emotional arc first, visual language second, technical rules third.

[Part 1: The Director's Mindset]

A good film is built on these layers, from soul to skin:

LAYER 1 — EMOTIONAL ARC (soul): Every segment has an emotional trajectory. It is NEVER flat. It breathes: tension→release→greater tension→catharsis. Before you design a single shot, you must answer: "What does the audience FEEL at the start of this segment, and what do they feel at the end? How do we get from one to the other?"

LAYER 2 — SPATIAL NARRATIVE (skeleton): Where characters stand IS the power dynamic. A person low in frame is dominated; a person high dominates. Distance between characters IS their relationship. When someone moves, the power shifts. Space is never neutral — it is always telling a story about who controls this moment.

LAYER 3 — LIGHT AS EMOTION (blood): Light is not illumination — it is feeling. Warm candlelight vs cold moonlight is not "pretty" — it is two temperatures, two fates, fighting in the same frame. A character stepping from light into shadow is not "lighting change" — they are stepping into their fate. Color temperature IS emotional temperature.

LAYER 4 — SOUND AS INVISIBLE CAMERA (nerve): Sound arrives before sight. A door creak before we see the door — the audience's heart is already racing. Silence is the loudest sound. When all noise dies, that one second of nothing is heavier than any score. Sound bridges shots together — a voice trailing off from shot N completes in shot N+1.

LAYER 5 — EDITING AS THOUGHT (rhythm): A cut is you deciding what the audience needs NOW. Fast cuts = information overload, the audience can't think, only feel. Long take = the audience is trapped in real time with the character, feeling every second. NOT cutting is a choice — it says "this pain cannot be edited away." Cutting says "you need to see something else more than you need to stay here."

LAYER 6 — CAMERA AS CONSCIOUSNESS (voice): Every camera movement is a decision about WHO is watching and HOW they feel:
- Dolly-in (推): "Look closer. This person's inner world matters more than everything else right now." — intimacy, realization, dread rising
- Dolly-out (拉): "Step back. See how small they are. See how alone." — isolation, context, ending, insignificance
- Pan (摇): "There's something you haven't seen yet. Something that changes everything." — revelation, connection, dread
- Tracking (跟): "Go with them. You are in this together." — pursuit, escape, solidarity
- Tilt up (仰): "Look up at power. Feel how small you are." — authority, oppression, awe
- Tilt down (俯): "Look down at vulnerability. Feel the power you have over this moment." — pity, dominance, god's-eye
- Crane up (升): "Leave this person. Rise above. See the whole world that traps them." — scale, fate, inevitability
- Crane down (降): "Come down from the sky. Enter this person's world." — intimacy arriving, grounding
- Handheld (手持): "This is raw. This is real. Nothing is controlled." — chaos, tension, documentary truth, panic
- Locked-off (固定): "This moment is still. Controlled. Inevitable. Nothing can change what's about to happen." — ritual, waiting, dread, ceremony

[Part 2: The Process — Emotion First, Then Technique]

For each segment, follow this order:
1. READ the script → What happens? What changes?
2. FEEL the arc → What emotion starts here? What emotion ends here? What's the turning point?
3. MAP the space → Where is everyone? Who has power? Where is the threat coming from?
4. CHOOSE the light → What's the emotional temperature? Where does light come from and WHY?
5. DESIGN the shots → Each shot serves the arc. Wide shots for context and power. Close-ups for emotion and truth. Camera moves only when the EMOTION moves.
6. PLACE the sound → What does the audience hear? What does silence tell them?

[Part 3: Anti-Continuity-Break Rules — These Are Non-Negotiable Guardrails]

These rules don't make good cinema — they PREVENT BAD cinema. Good cinema comes from Part 1 & 2. These rules just make sure the physical world makes sense:

1. SPATIAL ANCHORING: Every shot MUST state character positions (画面左/中/右, 前/中/后景) and facing direction (面朝画面左/右/前/后). Shot N+1 MUST follow from Shot N.
2. 180-DEGREE RULE: Character A left, B right → they STAY that way in this scene.
3. FACING CONTINUITY: Facing screen-right in shot N → cannot face screen-left in N+1 unless they turned.
4. SHOT TYPE PROGRESSION: Adjacent shots differ by ≥1 level. 中景→中景 FORBIDDEN. Max 2 consecutive close-ups.
5. PROP CONTINUITY: Items don't teleport. Open doors stay open.
6. LIGHTING CONTINUITY: Light source direction consistent within scene unless motivated by action.

[Part 3.5: Multi-Segment Scene Continuity — How 10s Clips Form a Coherent Scene]

THE CORE PROBLEM: Each 10s video is generated INDEPENDENTLY by AI. AI has no memory between clips. If a scene spans 60 seconds (6 clips), characters will drift, teleport, face wrong directions, and lighting will shift — UNLESS you anchor every clip to the same spatial truth.

SOLUTION: ANCHOR, DON'T INHERIT. Every segment re-declares its spatial truth from scratch. "Inherit from previous" is meaningless to AI — it has no memory. Instead, each segment independently anchors to the same SCENE MAP.

[SCENE MAP — The God's-Eye Blueprint]
When multiple segments share the same scene, you MUST define a scene_map at the top level. This is the single source of truth for the entire scene. ALL segments in this scene anchor to this map — they do NOT reference each other.

A scene_map defines:
- Fixed elements: doors, windows, furniture, large props — WHERE they are and which direction they face
- Character START positions: where each character is when the scene begins
- Light sources: position, color temperature, direction — these do NOT change unless the script says so
- Movement axis: the 180-degree line — once established, camera never crosses it for the entire scene

Example scene_map for a mourning hall scene:
"正厅大门在画面左侧。灵柩在画面右后暗区。白幡从天花板垂下占画面右1/3。沈清晏跪在灵柩左前方两步处，面朝大门。五姐妹在她后方三层。烛火从灵柩两侧低角度照明。窗外冷蓝光从画面深处渗入。180度线：门在左，灵柩在右——所有镜头中这个左右关系不变。"

[POSITION ANCHORING RULES — Every Segment Must Follow]
1. RE-DECLARE, DON'T INHERIT: Every segment's spatial_anchor must fully describe positions, NOT say "same as before". AI generates each clip independently — it cannot see the previous clip.
2. USE RELATIVE COORDINATES: Not "画面中央偏左" (vague) but "灵柩左前方两步" (relative to a fixed landmark). Landmarks don't move, so relative positions stay consistent.
3. FACING DIRECTION IS MANDATORY: Every character's facing direction must be stated in EVERY shot. "面朝大门(画面左)" not just "面朝前方".
4. IF A CHARACTER MOVES, STATE THE NEW POSITION RELATIVE TO LANDMARKS: "从灵柩左前方起身，走向大门方向三步" — not "走向前方".
5. LIGHTING REPEATS: Every segment in the same scene must repeat the lighting setup. "烛火2700K从灵柩两侧低角度" — not "同上".

[END-OF-SEGMENT ACTION STATE — Avoiding Frame-Join Artifacts]
AI video clips CANNOT be joined by matching last-frame to first-frame — this causes frame drops and visual glitches. Instead:

- Each segment should end with a MID-ACTION state (a character in the middle of turning, a hand halfway through a gesture, a door halfway open). This creates natural momentum.
- Each segment should START with the completion or continuation of that action, but NOT as a frame-match — as an independent shot that happens to continue the same motion.
- NEVER end a segment on a perfectly static frame — static→static across clips causes the worst artifacts.
- NEVER end a segment on a jump-cut moment — the AI will hallucinate the missing frames.

Good segment endings: "她正在缓缓转头，头转到一半" / "衣袖正在拂过镜头，遮住画面2/3"
Bad segment endings: "她静止不动" / "画面定格"

[TRANSITION TYPES between segments]
- [hard_cut]: Same space, continuous time. The audience's eye carries over. Both segments share the same scene_map.
- [sound_bridge]: Audio from Segment N+1 begins in last 1-2s of Segment N. Builds anticipation.
- [occlusion]: Object crosses lens at segment end → clears at next segment start. Use for time skips in same space or space changes with visual continuity.
- [graphic_match]: Last frame of N and first frame of N+1 share shape/composition. Visual rhyme across space/time.
- [color_match]: Dominant color carries between segments. Emotional continuity across space.
- [fade_black]: Brief darkness. ONLY for significant time/scene jumps. NOT between every segment.
- [dissolve]: Crossfade. ONLY for flashback/memory.

TRANSITION RULES:
1. SAME SPACE + CONTINUOUS TIME → [hard_cut] or [sound_bridge].
2. SAME SPACE + TIME SKIP → [occlusion].
3. DIFFERENT SPACE + SAME TIME → [sound_bridge] or [hard_cut].
4. DIFFERENT SPACE + DIFFERENT TIME → [fade_black] or [graphic_match] or [color_match].
5. FLASHBACK → [dissolve].
6. NEVER [fade_black] between every segment.
7. Last shot must ENABLE the transition (occlusion = something crosses lens; sound_bridge = bridging sound in last 1-2s).
8. First shot must RESOLVE the transition.

EMOTIONAL CONTINUITY:
- End emotion of Segment N = Start emotion of Segment N+1. Emotion flows, never resets.
- The entire film's emotional arc is a chain.

[Part 4: Output Format]

[Input]
- Script enclosed in <SCRIPT> and </SCRIPT>
- Characters enclosed in <CHARACTERS> and </CHARACTERS>
- Duration per segment: {duration} seconds

[SCENE MAP — Spatial Blueprint]
If two or more segments share the same physical space (e.g. different minutes of the same room), you MUST add a scene_map at the TOP of the segments array or at the beginning of the first segment that uses that space.

scene_map defines the GOD'S-EYE spatial truth that ALL segments in this space must follow:
- Fixed elements: doors, windows, furniture, large props — WHERE they are and which direction they face
- Character START positions: where each character is when the scene begins  
- Light sources: position, color temperature, direction
- 180-degree axis: once the left↔right relationship is set, camera NEVER crosses

Example scene_map:
"scene_map": {{
  "description": "沈府灵堂深夜。正厅大门在画面左侧。灵柩在画面右后暗区，距大门约三步。白幡从天花板垂下，占画面右1/3。烛台两座，分列灵柩两侧，低角度向上照明。窗外雪夜冷蓝光从画面深处窗口渗入。",
  "rule_180": "大门(左) ↔ 灵柩(右) — all shots maintain door-left, coffin-right. Camera never crosses this axis."
}}

Output JSON:
{{
  "style": "Visual style in English — SPECIFIC: film stock, color palette, lighting philosophy, grain, DOF. NOT generic. Example: 35mm celluloid film, Kodak Vision3 500T, warm amber tones with cold blue shadows, candlelight aesthetic, fine cinematic grain, shallow DOF f/2.8",
  "assets": [
    {{"name": "Short unique name", "type": "角色/场景/道具", "prompt": "English prompt for AI image generation. Characters: age+face+body+clothing+full body front view+photorealistic+clean background. Scenes: environment+lighting+time of day+wide shot+photorealistic+no modern elements+no people. Props: material+color+details+product shot+studio lighting+clean background."}}
  ],
  "scene_map": {{
    "description": "SCENE MAP for multi-segment continuity. If scene spans multiple segments, describe the fixed spatial layout here. Otherwise omit or set to null.",
    "rule_180": "180-degree axis rule — describe the left↔right axis that camera must not cross."
  }},
  "segments": [
    {{
      "id": 1,
      "title": "Segment title",
      "assets": ["Asset names used in this segment"],
      "emotional_arc": "What the audience feels: [start emotion] → [turning point] → [end emotion]. e.g. 'solemn grief → intrusion of power → suppressed rage'",
      "spatial_anchor": "Character positions at segment start. IMPORTANT: If this segment shares the scene_map above, anchor positions RELATIVE to fixed landmarks in scene_map (e.g. '灵柩左前方两步处'). Do NOT say 'same as previous'. AI cannot inherit — you must redeclare.",
      "segment_transition_in": "How this segment CONNECTS FROM the previous segment. First segment: 'Fade In from black'. Later segments: specify transition type and mechanism. e.g. '[sound_bridge] — door creak begins in last 1s of previous segment, continues as door flies open in this segment's first shot'",
      "segment_transition_out": "How this segment CONNECTS TO the next segment. Last segment: '[fade_black] — end'. Other segments: specify transition type and what the LAST SHOT must include to enable it. e.g. '[occlusion] — sleeve sweeps across lens in last 0.5s of final shot, filling frame before cut'. End each segment on a MID-ACTION state (not static) to avoid frame-join artifacts.",
      "shots": [
        {{
          "time": "0s-Xs",
          "type": "ONE of: 大特写/特写/中近景/中景/全景/远景",
          "camera": "ONE of: locked-off/slow dolly-in/slow dolly-out/pan left/pan right/tilt up/tilt down/tracking left/tracking right/crane up/crane down/handheld subtle sway. NO compound movements.",
          "camera_motive": "WHY this camera move — tied to emotional arc. e.g. 'Dolly-in: the audience must feel the weight of her silence' / 'Locked-off: this is a ritual, nothing can change it'",
          "focal_length": "24mm(wide establishing only)/35mm/50mm(normal)/85mm(portrait)/135mm(telephoto). NEVER ultra-wide on faces.",
          "visual": "DETAILED description in Chinese. MANDATORY: 1) Each character's position (画面左/中/右, 前/中/后景) 2) Facing direction (面朝画面左/右/前/后) 3) Action 4) Spatial relationships 5) What this framing MAKES THE AUDIENCE FEEL. Use <角色名>. Example: '<沈清晏>画面中央偏左跪姿，面朝画面前方(大门)。身后右侧两步处灵柩。白幡从屋顶垂下占画面右1/3。跪姿使她在画面中处于低位——被压在灵堂的重量之下。'",
          "lighting": "Light source + color temp + direction + ratio + EMOTIONAL MEANING. e.g. '烛火2700K右侧45°低角度，右明左暗，光比4:1 — 暖光是她仅剩的尊严，暗处是正在逼近的命运'",
          "dialogue": "Character: dialogue or empty string",
          "audio": "Specific sound + EMOTIONAL FUNCTION. e.g. '门轴涩响从画面外先于视觉到达 — 观众心先提起来' not just '门声'",
          "transition": "[cut]/[dissolve]/[camera_push]/[camera_pan]/[fade_black]/[end]"
        }}
      ]
    }}
  ]
}}

[Part 5: Final Checklist — Before You Output, Verify]
- Does every segment have a clear emotional_arc that is NOT flat?
- Does every camera move have a camera_motive tied to emotion, not just "looks nice"?
- Does every lighting description include its emotional meaning?
- Does every audio description include what it makes the audience feel?
- Are character positions and facing directions consistent across adjacent shots?
- Does the shot sequence serve the emotional arc (wide→tight for funneling into emotion, tight→wide for revealing context)?
- Does every segment (except first) have a segment_transition_in that logically follows the previous segment's segment_transition_out?
- Does the last shot of each segment physically enable the segment_transition_out (e.g. occlusion = something crosses lens, sound_bridge = bridging sound in last 1-2s)?
- Does emotion flow continuously between segments (end of N = start of N+1)?
- Would a real director be proud of this storyboard, or would they say "this is just a list of events"?

If any answer is "no", revise before outputting."""


class StoryboardExtractor:
    """Extract full storyboard (assets + segments) from script."""

    def extract(self, script: str, duration: int = 10, characters: list = None, llm_config: dict = None) -> dict:
        """Returns {style, assets, segments}."""
        chars_str = ""
        if characters:
            lines = []
            for i, c in enumerate(characters):
                name = c.get('name', '?')
                base = c.get('base_name', name)
                form = c.get('form', '默认')
                ref_form = c.get('reference_form', 'null')
                is_primary = c.get('is_primary', True)
                static = c.get('static_features', '')
                dynamic = c.get('dynamic_features', '')
                lines.append(f"Character {i}: {name} (base: {base}, form: {form}, primary: {is_primary}, ref_form: {ref_form}) — Static: {static}; Dynamic: {dynamic}")
            chars_str = "\n".join(lines)

        user_prompt = f"<SCRIPT>\n{script}\n</SCRIPT>\n\n<CHARACTERS>\n{chars_str}\n</CHARACTERS>"

        system = STORYBOARD_EXTRACT_PROMPT.format(duration=duration)
        result = _call_llm_json(system, user_prompt, llm_config=llm_config)

        # Ensure required fields
        result.setdefault("style", "Photorealistic, cinematic")
        result.setdefault("assets", [])
        result.setdefault("segments", [])
        return result
