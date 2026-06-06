"""一键成片项目API - 3阶段自动工作流：AI拆段→资产生图→视频生成（故事板可手动触发）

核心设计：复用 generate.py 的 create_task + _poll_oiioii 流程，
poll 完成后自动回写 result_url 到 project.results_json。
"""
import io
import json
import os
import time
import threading
import zipfile
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from api.auth import auth_required
from models.db import _get_conn, deduct_points, add_points, create_task, update_task
from core.proxy import OiioiiProxy
from core.vimax import VisualDecomposer
from config import OIIOII_API, LLM_API_URL, LLM_API_KEY, LLM_MODEL

proxy = OiioiiProxy(OIIOII_API)
_visual_decomposer = VisualDecomposer()

import requests as http_req
import json

# 加载牛马全流程竖屏分镜提示词（10s英文版）
_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")
_VERTICAL_CINEMA_PROMPT = ""
_vc_path = os.path.join(_PROMPTS_DIR, "vertical_cinema_10s.txt")
if os.path.exists(_vc_path):
    with open(_vc_path, "r", encoding="utf-8") as f:
        _VERTICAL_CINEMA_PROMPT = f.read().strip()


def _get_user_llm(uid: int) -> dict:
    """Get user's custom LLM settings, return dict with api_url/api_key/model/temperature/max_tokens."""
    try:
        conn = _get_conn()
        row = conn.execute("SELECT llm_settings FROM users WHERE id=?", (uid,)).fetchone()
        conn.close()
        if row and row["llm_settings"]:
            return json.loads(row["llm_settings"])
    except Exception:
        pass
    return {}

router = APIRouter(prefix="/api/project", tags=["project"])

# Ensure chat_history_json column exists in projects table
try:
    _db = _get_conn()
    _db.execute("ALTER TABLE projects ADD COLUMN chat_history_json TEXT DEFAULT ''")
    _db.commit()
    _db.close()
except Exception:
    pass  # Column already exists


class CreateProjectReq(BaseModel):
    name: str
    script: str
    raw_script: str = ""
    video_model: str = "Gemini Omni"
    image_model: str = "GPT-Image2"
    ratio: str = "16:9"
    resolution: str = "720p"
    image_resolution: str = "1K"
    duration: int = 10


class RunPhaseReq(BaseModel):
    phase: int  # 1=AI拆段 2=资产生图 3=故事板 4=视频生成


class UpdateScriptReq(BaseModel):
    script: str


class SaveRawScriptReq(BaseModel):
    raw_script: str


class AISplitReq(BaseModel):
    duration_per_segment: int = 5  # 每段时长（秒），根据剧本总时长自动估算


class AgentChatReq(BaseModel):
    message: str
    history: list = []  # [{"role": "user"/"assistant", "content": "..."}]


class AssetRefReq(BaseModel):
    image_url: str  # 前端先上传图片到oiioii拿到URL，再传过来


class VideoGenReq(BaseModel):
    prompt: Optional[str] = None  # 可选自定义prompt，为空则自动构建
    use_decomposer: bool = False  # 是否使用VisualDecomposer增强视频提示词（LLM调用，较慢）
    reference_images: Optional[list] = None  # 用户手动指定的垫图URL列表，优先级最高


class AssetUploadReq(BaseModel):
    image_url: str


def _call_llm_messages(messages: list, tools: list = None, uid: int = 0, max_tokens: int = 0) -> dict:
    """Call LLM API with full message list (multi-turn). Returns full response dict (not just content)."""
    user_llm = _get_user_llm(uid) if uid else {}
    api_url = user_llm.get("api_url") or LLM_API_URL
    api_key = user_llm.get("api_key") or LLM_API_KEY
    model = user_llm.get("model") or LLM_MODEL
    temperature = user_llm.get("temperature", 0.7)
    tokens = max_tokens or user_llm.get("max_tokens", 16384)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": tokens
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    try:
        r = http_req.post(api_url, headers=headers, json=body, timeout=600)
        if r.status_code == 200:
            return r.json()
        return {"error": f"LLM API returned {r.status_code}: {r.text[:300]}"}
    except Exception as e:
        return {"error": str(e)}


def _call_llm(system_prompt: str, user_prompt: str, uid: int = 0, max_tokens: int = 0) -> str:
    """Call LLM API (OpenAI-compatible) and return the response content."""
    user_llm = _get_user_llm(uid) if uid else {}
    api_url = user_llm.get("api_url") or LLM_API_URL
    api_key = user_llm.get("api_key") or LLM_API_KEY
    model = user_llm.get("model") or LLM_MODEL
    temperature = user_llm.get("temperature", 0.7)
    tokens = max_tokens or user_llm.get("max_tokens", 16384)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": tokens
    }
    try:
        r = http_req.post(api_url, headers=headers, json=body, timeout=600)
        if r.status_code == 200:
            data = r.json()
            return data["choices"][0]["message"]["content"]
        return f"ERROR: LLM API returned {r.status_code}: {r.text[:300]}"
    except Exception as e:
        return f"ERROR: {str(e)}"


SYSTEM_PROMPT_SPLIT = """你是一个专业的影视分镜师，专门为AI视频模型（Gemini Omni）准备分镜脚本。

【最高优先级】你必须直接输出JSON，不要输出任何对话、问候、分析、解释。不要说"好的导演"或任何开场白。只输出一个JSON对象，以左花括号开头，以右花括号结尾。

用户会给你一段剧本/故事文本，你需要按以下规则拆段：

## 核心导演规则（必须遵守）

VERTICAL_CINEMA_PLACEHOLDER

---

## 适配说明
以上是完整的竖屏分镜导演系统。在实际执行中，你需要将输出适配为以下JSON格式（而非上面的纯文本格式），以便系统解析：

**重要覆盖规则**：上面导演系统中所有"10s"的时长限制，在本项目中统一替换为{duration}秒。铁律#6改为"Total effective duration ≤ {duration}s"。段溢出阈值从>10s改为>{duration}s。其余所有铁律、构图、灯光、转场规则完全保留。

## 任务
1. 提取所有角色、场景、道具作为"资产"（assets）
2. 把剧本拆成多个"段"（segments），每段固定{duration}秒
3. 每段包含4-9个镜头（shots），节奏由内容决定
4. **必须输出所有段！** 剧本有多少内容就拆多少段，绝不能只输出2段就停止。如果剧本很长，拆成5段、8段、10段都可以，必须覆盖全部剧情。
5. 每段必须列出用到的资产名（assets字段），这是视频生成的关键参考

## 镜头规则
- 每段时长：固定{duration}秒
- 每段镜头数：4-9镜（节奏自适应）
- 每段台词：≤20中文字（标点不计，OS旁白不计）
- 画幅：{ratio}
- 台词口型：英文lip-sync（模型为国外模型，中文口型无法对齐）

## 镜头节奏指南
| 段类型 | 镜数 | 每镜时长 | 转场 |
|--------|------|----------|------|
| 冲突/爆发段 | 4-6镜 | 1-2s | cut快切 |
| 情绪积累段 | 5-7镜 | 1.5-3s | dissolve/camera |
| 氛围铺垫段 | 5-9镜 | 1-3s | 混合转场 |
| 关键定格 | locked-off | 1-2s | dissolve前后 |

## 转场方式
| 标记 | 含义 | 适用场景 |
|------|------|----------|
| [cut] | 硬切 | 快节奏、冲突 |
| [dissolve] | 叠化 | 情绪过渡、时间流逝 |
| [camera_pan] | 运镜横摇衔接 | 空间连续 |
| [camera_push] | 运镜推拉衔接 | 跟随移动 |
| [fade_black] | 黑场 | 段末、死亡、重生 |
| [end] | 段末标记 | 最后一个镜头 |

## 运镜清单
缓慢推进(slow dolly-in)、缓慢后拉(slow pull-back)、横摇(pan left/right)、上摇/下摇(tilt up/down)、手持微晃(handheld)、跟拍(tracking)、固定镜头(locked-off)、缓推+停顿(slow push hold)、环绕(orbit)、快切(quick cut)

## 资产prompt规则
- 角色prompt：必须严格使用以下框架（不可修改框架结构，只填入方括号内容）：
  "Split composition character reference board, left side extreme close-up portrait, right side three-view turnaround (front/90/side/back), full body standing, clean professional layout. Left: ultra detailed front face close-up, [face shape, eyebrows, eyes, skin tone, hairstyle, any distinctive marks], visible skin pores and micro skin texture, subtle subsurface scattering, natural skin imperfections (not plastic smooth). Right: front view (head completely removed, neck-down only, no face shown), side view (with head), back view (with head), wearing [outfit description], [body proportions, hand size, posture], consistent lighting and material quality across all views, pure white background. Bottom: clean white horizontal bar with bold black Chinese text \"[Character Name] Age [Number] Character Reference\". Overall: vertical, high resolution textures, not blurry, not plastic smooth."
  示例："Split composition character reference board, left side extreme close-up portrait, right side three-view turnaround (front/90/side/back), full body standing, clean professional layout. Left: ultra detailed front face close-up, oval face, thick straight eyebrows, deep-set dark brown eyes, warm olive skin tone, black hair tied in low bun, a small mole on left cheekbone, visible skin pores and micro skin texture, subtle subsurface scattering, natural skin imperfections (not plastic smooth). Right: front view (head completely removed, neck-down only, no face shown), side view (with head), back view (with head), wearing dark navy cotton robe with silver embroidery at cuffs, slim build, small hands, upright posture, consistent lighting and material quality across all views, pure white background. Bottom: clean white horizontal bar with bold black Chinese text \"沈清晏 Age 22 Character Reference\". Overall: vertical, high resolution textures, not blurry, not plastic smooth."
- 场景prompt：必须包含环境细节、光线方向、氛围、广角建立镜头、photorealistic、年代风格、No modern elements
  示例："A 1980s Chinese outdoor food market in winter, heavy snow falling. A simple fish stall with wooden table, water basin, fish on display. Wide establishing shot, photorealistic, 1980s Chinese rural town, overcast snowy sky, cinematic wide angle. No modern elements."
- 道具prompt：必须包含尺寸、材质、细节、产品级拍摄、soft studio lighting、clean neutral background
  示例："A white porcelain Chinese vase, 30cm tall, classic Ming-style shape, glossy finish, standing on a wooden side table. Photorealistic product shot, soft studio lighting, clean neutral background."
- 所有prompt必须用英文

## 多形态角色规则
同一角色如果有多种形态（如：年轻版/老年版、人形/兽形、便装/战甲），必须拆成多个独立资产：
- 资产命名格式：`角色名_形态名`（如：冷秋月_老年、冷秋月_年轻）
- 主形态（最先出场的版本）：设 `"is_primary": true`，无 `reference_form` 字段
- 衍生形态：设 `"is_primary": false, "reference_form": "主形态资产名"`
- 衍生形态的prompt必须描述与主形态的关联（如"same person as 冷秋月_老年 but 20 years younger"）
- 衍生形态会以主形态的生成图作为参考图（垫图），确保面部一致性

## 违禁词
禁止出现：60FPS、60fps、高帧率、No hard cuts、one seamless flow、one continuous flow

## 输出格式
严格JSON，不要任何其他文字。不要输出对话、问候、分析、解释。直接以左花括号开头输出JSON：
{{
  "style": "整体视觉风格描述，如：35mm celluloid film, 1980s China, cinematic",
  "assets": [
    {{"name": "角色名", "type": "角色", "prompt": "Split composition character reference board... Left: ultra detailed front face close-up, [face details]... Right: front view (neck-down only), side view, back view, wearing [outfit]... Bottom: \"[角色名] Age [数字] Character Reference\"... Overall: 35mm film, Kodak Vision3 500T...", "is_primary": true}},
    {{"name": "角色名_形态名", "type": "角色", "prompt": "Split composition character reference board... Same person as 角色名 but [形态差异]... Left: [face details]... Right: [outfit]... Bottom: \"[角色名_形态名] Age [数字] Character Reference\"...", "is_primary": false, "reference_form": "角色名"}},
    {{"name": "场景名", "type": "场景", "prompt": "A [年代] Chinese [场景类型]... Wide establishing shot, photorealistic, [年代风格]. No modern elements."}},
    {{"name": "道具名", "type": "道具", "prompt": "A [描述]... Photorealistic product shot, soft studio lighting, clean neutral background."}}
  ],
  "segments": [
    {{
      "id": 1,
      "title": "段标题",
      "assets": ["用到的资产名1", "用到的资产名2"],
      "video_prompt": "本段完整视频提示词（英文，一段连贯的段落，融合所有镜头的画面、运镜、光线、动作、转场描述，直接用于AI视频生成模型。必须详细具体，包含角色外观、动作、表情、运镜方式、光线氛围、转场方式等所有视觉信息）",
      "negative": "本段负面约束（英文，如：no modern objects, no bright colors, no smiling等）",
      "shots": [
        {{"time": "0s—Xs", "type": "景别", "camera": "运镜方式(英文)", "visual": "画面描述（英文，具体画面感强，这是给视频生成模型用的）", "lighting": "光线描述(英文)", "dialogue": "角色：台词或留空", "audio": "音效描述(英文)", "transition": "[cut]/[dissolve]/[camera_push]/[fade_black]/[end]"}}
      ]
    }}
  ]
}}

重要：每段的"assets"字段必须列出该段用到的所有角色和场景资产名，不能留空！这是视频生成时引用参考图的关键。
重要：每段的"video_prompt"字段是视频生成的核心！它必须是一段连贯的英文段落，把本段所有镜头的画面、运镜、光线、角色动作、转场融合成一个完整的视频描述。不要简单罗列镜头，要写成一段有画面感的叙事。这个字段会被直接发送给视频生成模型。

## 语言要求（最高优先级）
- 所有 prompt、visual、lighting、audio、video_prompt、negative 字段必须使用英文！视频生成模型是国外模型（Gemini Omni），中文会被安全系统拦截导致生成失败。
- 只有 dialogue 字段可以保留中文台词（但视频生成时会自动要求英文口型）。
- title 可以用中文。
- style 必须用英文。"""


def _calc_image_cost(model: str, resolution: str = "1K") -> int:
    from api.generate import _calc_image_cost as ic
    return ic(model, resolution)


def _calc_video_cost(model: str, duration: int, resolution: str) -> int:
    from api.generate import _calc_video_cost as vc
    return vc(model, duration, resolution)


def _get_base_url() -> str:
    """Get the base URL for constructing absolute URLs from relative paths.
    Priority: AIFORGE_BASE_URL env var > auto-detect from request.
    For Gemini Omni (external Google server), must use public URL not localhost.
    """
    env_url = os.environ.get("AIFORGE_BASE_URL", "")
    if env_url:
        return env_url.rstrip("/")
    # Default: use the public server address
    return "http://122.51.205.94"


def _to_absolute_url(relative_url: str) -> str:
    """Convert relative URL like /api/gen/file/123 to absolute URL for oiioii API."""
    if not relative_url:
        return ""
    if relative_url.startswith("http"):
        return relative_url
    base = _get_base_url().rstrip("/")
    return base + relative_url


def _build_video_prompt(segment: dict, duration: int, style: str,
                        seg_asset_names: list, phase2_results: list,
                        segment_index: int,
                        scene_map: dict = None,
                        use_decomposer: bool = False,
                        characters: list = None,
                        llm_config: dict = None) -> dict:
    """
    Build video prompt + reference images + reference map for a segment.

    Priority:
    1. If segment has a "video_prompt" field (user/AI written full prompt), use it directly
    2. Otherwise, build from shot fields using template

    Returns: {"prompt": str, "ref_images": list[str], "ref_map": dict[str, str], "decomposed": list[dict]}
    """
    shots = segment.get("shots", [])
    n_shots = len(shots)
    scene_title = segment.get("title", f"Segment {segment_index + 1}")
    seg_asset_names = segment.get("assets", []) or seg_asset_names or []

    # Fallback style if empty
    if not style or not style.strip():
        style = "35mm celluloid film, Kodak Vision3 500T, cinematic, warm amber tones"

    # --- Build reference images + map ---
    ref_images = []
    ref_map = {}

    # 1. Asset reference images from phase2 — match by name
    if seg_asset_names:
        for r in phase2_results:
            if r.get("result_url") and r.get("name") and r["name"] in seg_asset_names:
                url = _to_absolute_url(r["result_url"])
                tag = f"@{r['name']}"
                if tag not in ref_map:
                    ref_images.append(url)
                    ref_map[tag] = url

    # Limit to 3 reference images (oiioii constraint)
    ref_images = ref_images[:3]

    # --- Priority: use segment's video_prompt if available ---
    seg_video_prompt = segment.get("video_prompt", "").strip()
    if seg_video_prompt:
        # User/AI provided full video prompt — use it directly, just append style + negative
        parts = [seg_video_prompt]
        parts.append("")
        # Append negative constraints from segment if available
        seg_negative = segment.get("negative", "").strip()
        if seg_negative:
            parts.append(f"Negative constraints: {seg_negative}")
        parts.append(f"Style: {style}")
        return {
            "prompt": "\n".join(parts),
            "ref_images": ref_images,
            "ref_map": ref_map,
            "decomposed": None,
        }

    # --- Fallback: build from shot fields using template ---
    parts = []

    # Header: cinematic video generation
    parts.append(f"Generate a cinematic video following the shot descriptions below.")
    parts.append("")

    # Reference section
    ref_tags = list(ref_map.keys())
    if ref_tags:
        parts.append("Reference materials:")
        char_refs = ref_tags
        parts.append(f"- Character reference images provide appearance template — facial features, hairstyle, clothing colors and styles must match exactly")
        parts.append(f"- Scene reference images provide spatial layout — positions, lighting direction, overall atmosphere must match exactly")
    parts.append("")

    # Execution rules
    parts.append("Execution rules:")
    parts.append("1. Follow shot timing for cuts, do not adjust shot durations")
    parts.append("2. Camera moves must follow annotations — supports hard cut/dissolve/camera transition")
    parts.append("3. Character faces must match reference images exactly")
    parts.append("4. Scene lighting and color tone must match scene reference images")
    parts.append("5. Each shot's action must follow the description only — do not add shots or actions not described")
    parts.append("6. Transitions follow bracketed markers: [cut]/[dissolve]/[camera_push]/[fade_black]/[end]")
    parts.append("")

    # Multi-shot timeline
    parts.append(f"A {duration}-second cinematic sequence with {n_shots} shots. {style}.")
    parts.append("")

    # Segment-level fields
    emotional_arc = segment.get("emotional_arc", "")
    spatial_anchor = segment.get("spatial_anchor", "")
    if emotional_arc:
        parts.append(f"Emotional arc: {emotional_arc}")
    if spatial_anchor:
        parts.append(f"Spatial anchor: {spatial_anchor}")
    if emotional_arc or spatial_anchor:
        parts.append("")

    # --- Optional: decompose shots via VisualDecomposer (LLM-based, slow & costly) ---
    decomposed_shots = []  # store decomposition results per shot

    for j, sh in enumerate(shots):
        time_range = sh.get("time", "")
        camera = sh.get("camera", "locked-off")
        camera_motive = sh.get("camera_motive", "")
        focal_length = sh.get("focal_length", "")
        shot_type = sh.get("type", "")  # 景别
        visual = sh.get("visual", "")[:200]
        lighting = sh.get("lighting", "")
        audio = sh.get("audio", "")
        dialogue = sh.get("dialogue", "")
        transition = sh.get("transition", "[cut]" if j < n_shots - 1 else "[end]")

        # Try decomposer for this shot if enabled and visual description exists
        decomposed = None
        if use_decomposer and visual:
            try:
                decomposed = _visual_decomposer.decompose_shot(
                    visual_desc=sh.get("visual", ""),
                    characters=characters,
                    llm_config=llm_config,
                )
                decomposed_shots.append({"shot_index": j, **decomposed})
            except Exception as e:
                print(f"[Decomposer] shot {j} decompose failed: {e}")
                decomposed = None
                decomposed_shots.append({"shot_index": j, "error": str(e)})

        shot_parts = [f"SHOT: {time_range}"]
        if shot_type:
            shot_parts.append(f"Frame: {shot_type}")
        shot_parts.append(f"{camera}")
        if camera_motive:
            shot_parts.append(f"Motive: {camera_motive}")
        if focal_length:
            shot_parts.append(f"Lens: {focal_length}")

        # Use decomposed video_prompt if available, otherwise use original visual
        if decomposed and decomposed.get("video_prompt"):
            shot_parts.append(f". {decomposed['video_prompt']}")
        else:
            shot_parts.append(f". {visual}")

        if lighting:
            shot_parts.append(f". Lighting: {lighting}")
        if audio:
            shot_parts.append(f". Audio: {audio}")
        shot_parts.append(f" [{transition}]")
        parts.append("".join(shot_parts))

    parts.append("")

    # Audio chain
    audio_parts = [sh.get("audio", "") for sh in shots if sh.get("audio")]
    if audio_parts:
        parts.append(f"AUDIO: {' → '.join(audio_parts[:5])}")

    # Dialogue with English lip-sync
    dialogue_parts = []
    for sh in shots:
        d = sh.get("dialogue", "")
        if d and not d.startswith("OS") and not d.startswith("（"):
            dialogue_parts.append(d[:80])
    if dialogue_parts:
        parts.append(f'DIALOGUE (English lip-sync required): "English translation" | "' + '" | "'.join(dialogue_parts[:3]) + '"')

    parts.append("")

    # Dialogue rules
    parts.append("Dialogue rules:")
    parts.append("- All dialogue must use English lip-sync (model is English-based, Chinese lip-sync cannot align)")
    parts.append("- English translation must preserve original meaning and emotional intensity, use colloquial expressions")
    parts.append("- No profanity allowed")
    parts.append("")

    # Content safety
    parts.append("Content guidelines:")
    parts.append("- No graphic gore close-ups")
    parts.append("")

    # Negative constraints
    parts.append(f"Negative constraints: No modern objects (phones/power lines/plastic), no CGI effects, character appearance must not deviate from reference images, do not invent extra plot points.")
    parts.append("")
    parts.append(f"Style: {style}")

    return {
        "prompt": "\n".join(parts),
        "ref_images": ref_images,
        "ref_map": ref_map,
        "decomposed": decomposed_shots if decomposed_shots else None,
    }


def _poll_and_update_project(project_id: int, phase: int, oiioii_task_id: int,
                              aiforge_task_id: int, uid: int, cost: int,
                              result_key: str, item_index: int):
    """Poll oiioii task, then update project.results_json with result_url."""
    start = time.time()
    max_wait = 1800
    try:
        while time.time() - start < max_wait:
            try:
                result = proxy.get_task(oiioii_task_id)
            except Exception as e:
                print(f"[ProjectPoll] #{aiforge_task_id}: proxy.get_task exception: {e}")
                time.sleep(10)
                continue

            status = result.get("status", "")
            if status == "completed":
                file_url = f"/api/gen/file/{oiioii_task_id}"
                update_task(aiforge_task_id, "completed", file_url)
                _update_project_result(project_id, phase, result_key, item_index, {
                    "status": "completed", "result_url": file_url, "aiforge_task_id": aiforge_task_id
                })
                print(f"[ProjectPoll] project#{project_id} phase{phase} item{item_index}: completed")
                return
            elif status == "failed":
                error_msg = result.get("error", result.get("message", "未知错误"))
                update_task(aiforge_task_id, "failed", "", error=error_msg)
                add_points(uid, cost, f"任务失败退还-#{aiforge_task_id}")
                _update_project_result(project_id, phase, result_key, item_index, {
                    "status": "failed", "error": error_msg, "aiforge_task_id": aiforge_task_id
                })
                print(f"[ProjectPoll] project#{project_id} phase{phase} item{item_index}: failed")
                return
            elif result.get("error"):
                print(f"[ProjectPoll] #{aiforge_task_id}: has error but still processing: {result['error'][:50]}")
                time.sleep(5)
                continue
            time.sleep(5)

        update_task(aiforge_task_id, "timeout", "", error="任务超时，积分已退还")
        add_points(uid, cost, f"任务超时退还-#{aiforge_task_id}")
        _update_project_result(project_id, phase, result_key, item_index, {
            "status": "timeout", "error": "任务超时", "aiforge_task_id": aiforge_task_id
        })
    except Exception as e:
        print(f"[ProjectPoll] project#{project_id} CRASHED: {e}")
        try:
            update_task(aiforge_task_id, "failed", "", error="内部错误，积分已退还")
            add_points(uid, cost, f"内部错误退还-#{aiforge_task_id}")
            _update_project_result(project_id, phase, result_key, item_index, {
                "status": "failed", "error": str(e), "aiforge_task_id": aiforge_task_id
            })
        except:
            print(f"[ProjectPoll] project#{project_id}: CRITICAL - failed to update after crash!")


def _update_project_result(project_id: int, phase: int, result_key: str,
                            item_index: int, item_result: dict):
    """Thread-safe update of a single item in project.results_json."""
    db = _get_conn()
    try:
        row = db.execute("SELECT results_json FROM projects WHERE id=?", (project_id,)).fetchone()
        results = json.loads(row["results_json"]) if row and row["results_json"] else {}
        phase_key = f"phase{phase}"
        if phase_key not in results:
            results[phase_key] = []
        while len(results[phase_key]) <= item_index:
            results[phase_key].append({"status": "pending"})
        results[phase_key][item_index].update(item_result)
        db.execute("UPDATE projects SET results_json=?, updated_at=? WHERE id=?",
                   (json.dumps(results, ensure_ascii=False), time.time(), project_id))
        db.commit()
    except Exception as e:
        print(f"[Project] _update_project_result error: {e}")
        try:
            db.rollback()
        except:
            pass
    finally:
        db.close()


def _get_project_results(project_id: int) -> dict:
    """Get current results_json for a project (used for cross-asset reference)."""
    db = _get_conn()
    try:
        row = db.execute("SELECT results_json FROM projects WHERE id=?", (project_id,)).fetchone()
        return json.loads(row["results_json"]) if row and row["results_json"] else {}
    except Exception:
        return {}
    finally:
        db.close()


def _get_project_data(project_id: int, uid: int) -> dict:
    """Get project data as dict."""
    db = _get_conn()
    r = db.execute("SELECT * FROM projects WHERE id=? AND user_id=?", (project_id, uid)).fetchone()
    if not r:
        db.close()
        raise HTTPException(404, "项目不存在")
    col_names = [desc[0] for desc in db.execute("SELECT * FROM projects LIMIT 0").description]
    db.close()
    return dict(zip(col_names, r))


# ==================== CRUD ====================

@router.post("/create")
def create_project(req: CreateProjectReq, user: dict = Depends(auth_required)):
    segments = []
    assets = []
    try:
        script_data = json.loads(req.script)
        segments = script_data.get("segments", [])
        assets = script_data.get("assets", [])
    except json.JSONDecodeError:
        pass

    db = _get_conn()
    now = time.time()
    cursor = db.execute("""
        INSERT INTO projects (user_id, name, script, raw_script, video_model, image_model, ratio, resolution, image_resolution, duration,
                              segments_json, assets_json, phase, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
    """, (user["id"], req.name, req.script, req.raw_script, req.video_model, req.image_model,
          req.ratio, req.resolution, req.image_resolution, req.duration,
          json.dumps(segments, ensure_ascii=False), json.dumps(assets, ensure_ascii=False),
          now, now))
    db.commit()
    project_id = cursor.lastrowid
    db.close()
    return {"id": project_id, "name": req.name, "phase": 0, "segments": len(segments), "assets": len(assets)}


@router.get("/list")
def list_projects(user: dict = Depends(auth_required)):
    db = _get_conn()
    rows = db.execute("""
        SELECT id, name, video_model, image_model, ratio, resolution, image_resolution, duration, phase,
               segments_json, assets_json, results_json, created_at, updated_at
        FROM projects WHERE user_id=? ORDER BY updated_at DESC
    """, (user["id"],)).fetchall()
    result = []
    for r in rows:
        segs = json.loads(r[9]) if r[9] else []
        assets = json.loads(r[10]) if r[10] else []
        results = json.loads(r[11]) if r[11] else {}
        phase2_done = sum(1 for x in results.get("phase2", []) if x.get("status") == "completed")
        phase3_done = sum(1 for x in results.get("phase3", []) if x.get("status") == "completed")
        phase4_done = sum(1 for x in results.get("phase4", []) if x.get("status") == "completed")
        result.append({
            "id": r[0], "name": r[1], "video_model": r[2], "image_model": r[3],
            "ratio": r[4], "resolution": r[5], "image_resolution": r[6], "duration": r[7], "phase": r[8],
            "segments_count": len(segs), "assets_count": len(assets),
            "phase2_done": phase2_done, "phase3_done": phase3_done, "phase4_done": phase4_done,
            "results": results,
            "created_at": r[12], "updated_at": r[13]
        })
    db.close()
    return result


@router.get("/{project_id}")
def get_project(project_id: int, user: dict = Depends(auth_required)):
    db = _get_conn()
    r = db.execute("""
        SELECT id, name, script, raw_script, video_model, image_model, ratio, resolution, image_resolution, duration,
               segments_json, assets_json, phase, results_json, created_at, updated_at
        FROM projects WHERE id=? AND user_id=?
    """, (project_id, user["id"])).fetchone()
    if not r:
        db.close()
        raise HTTPException(404, "项目不存在")
    segs = json.loads(r[10]) if r[10] else []
    assets = json.loads(r[11]) if r[11] else []
    results = json.loads(r[13]) if r[13] else {}
    phase2_items = results.get("phase2", [])
    phase3_items = results.get("phase3", [])
    phase4_items = results.get("phase4", [])
    db.close()
    return {
        "id": r[0], "name": r[1], "script": r[2], "raw_script": r[3],
        "video_model": r[4], "image_model": r[5],
        "ratio": r[6], "resolution": r[7], "image_resolution": r[8], "duration": r[9],
        "segments": segs, "assets": assets, "phase": r[12],
        "results": results,
        "phase2_total": len(assets), "phase2_done": sum(1 for x in phase2_items if x.get("status") == "completed"),
        "phase3_total": len(segs), "phase3_done": sum(1 for x in phase3_items if x.get("status") == "completed"),
        "phase4_total": len(segs), "phase4_done": sum(1 for x in phase4_items if x.get("status") == "completed"),
        "created_at": r[14], "updated_at": r[15]
    }


@router.put("/{project_id}/script")
def update_script(project_id: int, req: UpdateScriptReq, user: dict = Depends(auth_required)):
    db = _get_conn()
    r = db.execute("SELECT id, assets_json, segments_json, results_json FROM projects WHERE id=? AND user_id=?",
                   (project_id, user["id"])).fetchone()
    if not r:
        db.close()
        raise HTTPException(404, "项目不存在")

    # Parse old data for comparison
    old_assets = json.loads(r["assets_json"]) if r["assets_json"] else []
    old_segments = json.loads(r["segments_json"]) if r["segments_json"] else []
    old_results = json.loads(r["results_json"]) if r["results_json"] else {}

    segments = []
    assets = []
    try:
        script_data = json.loads(req.script)
        segments = script_data.get("segments", [])
        assets = script_data.get("assets", [])
    except json.JSONDecodeError:
        pass

    # Compare old vs new to determine which results to clear
    # Assets comparison
    if len(assets) != len(old_assets):
        # Asset count changed — reset all phase2 results
        old_results["phase2"] = []
    else:
        # Compare by index
        phase2 = old_results.get("phase2", [])
        for i in range(len(assets)):
            old_a = old_assets[i] if i < len(old_assets) else {}
            new_a = assets[i]
            if (old_a.get("name") != new_a.get("name") or
                old_a.get("type") != new_a.get("type") or
                old_a.get("prompt") != new_a.get("prompt")):
                if i < len(phase2):
                    old_name = phase2[i].get("name", "")
                    phase2[i] = {"name": old_name, "status": "pending"}
        old_results["phase2"] = phase2

    # Segments comparison
    if len(segments) != len(old_segments):
        # Segment count changed — reset all phase3/phase4 results
        old_results["phase3"] = []
        old_results["phase4"] = []
    else:
        # Compare by index
        phase3 = old_results.get("phase3", [])
        phase4 = old_results.get("phase4", [])
        for i in range(len(segments)):
            old_s = old_segments[i] if i < len(old_segments) else {}
            new_s = segments[i]
            if old_s.get("shots") != new_s.get("shots"):
                if i < len(phase3):
                    old_title = phase3[i].get("title", "")
                    phase3[i] = {"title": old_title, "status": "pending"}
                if i < len(phase4):
                    old_title = phase4[i].get("title", "")
                    phase4[i] = {"title": old_title, "status": "pending"}
        old_results["phase3"] = phase3
        old_results["phase4"] = phase4

    db.execute("""
        UPDATE projects SET script=?, segments_json=?, assets_json=?, results_json=?, updated_at=?
        WHERE id=? AND user_id=?
    """, (req.script, json.dumps(segments, ensure_ascii=False),
          json.dumps(assets, ensure_ascii=False),
          json.dumps(old_results, ensure_ascii=False), time.time(),
          project_id, user["id"]))
    db.commit()
    db.close()
    return {"ok": True, "segments": len(segments), "assets": len(assets)}


@router.delete("/{project_id}")
def delete_project(project_id: int, user: dict = Depends(auth_required)):
    db = _get_conn()
    db.execute("DELETE FROM projects WHERE id=? AND user_id=?", (project_id, user["id"]))
    db.commit()
    db.close()
    return {"ok": True}


@router.put("/{project_id}/raw-script")
def save_raw_script(project_id: int, req: SaveRawScriptReq, user: dict = Depends(auth_required)):
    """保存原始剧本文本"""
    db = _get_conn()
    r = db.execute("SELECT id FROM projects WHERE id=? AND user_id=?", (project_id, user["id"])).fetchone()
    if not r:
        db.close()
        raise HTTPException(404, "项目不存在")
    db.execute("UPDATE projects SET raw_script=?, updated_at=? WHERE id=? AND user_id=?",
               (req.raw_script, time.time(), project_id, user["id"]))
    db.commit()
    db.close()
    return {"ok": True, "length": len(req.raw_script)}


# ==================== Phase Execution ====================

@router.post("/{project_id}/run")
def run_phase(project_id: int, req: RunPhaseReq, user: dict = Depends(auth_required)):
    db = _get_conn()
    r = db.execute("SELECT * FROM projects WHERE id=? AND user_id=?", (project_id, user["id"])).fetchone()
    if not r:
        db.close()
        raise HTTPException(404, "项目不存在")

    col_names = [desc[0] for desc in db.execute("SELECT * FROM projects LIMIT 0").description]
    project = dict(zip(col_names, r))

    if req.phase == 1:
        # Phase1 = AI拆段（需要先有raw_script）
        db.close()
        return _run_phase1_split(user["id"], project)
    elif req.phase == 2:
        return _run_phase2(user["id"], project, db)
    elif req.phase == 3:
        return _run_phase3(user["id"], project, db)  # 故事板生成
    elif req.phase == 4:
        return _run_phase4(user["id"], project, db)  # 视频生成
    else:
        db.close()
        raise HTTPException(400, f"阶段{req.phase}暂不支持自动执行")


# ==================== AI Script Split ====================

CHAPTER_SPLIT_PROMPT = """你是一个专业的影视分镜师。用户会给你一段长剧本，你需要把它划分成若干章节。

【最高优先级】直接输出JSON，不要任何对话、问候、解释。以左花括号开头，以右花括号结尾。

规则：
1. 每个章节约5-10分钟的剧情量（约30-60个{duration}秒的分镜段）
2. 章节按剧情自然转折点划分（场景转换、时间跳跃、情绪转折等）
3. 为每章提供简短摘要，方便后续分镜师理解上下文

输出格式：
{{
  "chapters": [
    {{"id": 1, "title": "章节标题", "summary": "本章剧情摘要(2-3句)", "text": "本章对应的原文内容(完整复制，不要省略任何字)"}},
    ...
  ]
}}

重要：每章的text字段必须包含该章的完整原文，不能省略任何内容！所有章节的text合起来必须等于完整剧本！"""


@router.post("/{project_id}/ai-split")
def ai_split_script(project_id: int, req: AISplitReq, user: dict = Depends(auth_required)):
    """Use LLM to automatically split raw script into assets + segments.
    For long scripts (>3000 chars), uses a two-pass approach:
    Pass 1: Split into chapters
    Pass 2: Split each chapter into segments (parallel)
    """
    project = _get_project_data(project_id, user["id"])

    raw_script = project.get("raw_script", "")
    if not raw_script:
        raise HTTPException(400, "请先上传或粘贴原始剧本")

    # Deduct a small fee for LLM usage
    llm_cost = 5
    if not deduct_points(user["id"], llm_cost, "一键成片-AI拆段"):
        raise HTTPException(402, "积分不足")

    # Auto-estimate optimal segment duration based on script length
    script_len = len(raw_script)
    if script_len < 500:
        req.duration_per_segment = 4
    elif script_len < 1000:
        req.duration_per_segment = 5
    elif script_len < 2000:
        req.duration_per_segment = 6
    elif script_len < 3000:
        req.duration_per_segment = 8
    else:
        req.duration_per_segment = 10

    # Build ratio/resolution strings from project settings
    ratio_val = project.get("ratio", "16:9")
    resolution_val = project.get("resolution", "720p")
    ratio_str = f"{ratio_val} {'竖屏' if '9:16' in ratio_val else '横屏'}"
    resolution_str = {"720p": "1152x2048" if "9:16" in ratio_val else "2048x1152",
                      "1080p": "1080x1920" if "9:16" in ratio_val else "1920x1080",
                      "4K": "2160x3840" if "9:16" in ratio_val else "3840x2160"}.get(resolution_val, "2048x1152")

    system_prompt = SYSTEM_PROMPT_SPLIT.format(duration=req.duration_per_segment, ratio=ratio_str, resolution=resolution_str)
    system_prompt = system_prompt.replace("VERTICAL_CINEMA_PLACEHOLDER", _VERTICAL_CINEMA_PROMPT)

    # ─── Short script: single pass ───
    if len(raw_script) <= 3000:
        result_text = _call_llm(system_prompt, raw_script, uid=user["id"], max_tokens=65536)
        if result_text.startswith("ERROR:"):
            add_points(user["id"], llm_cost, "AI拆段失败退还")
            raise HTTPException(500, f"LLM调用失败: {result_text}")
        script_data = _parse_llm_json(result_text)
        if not script_data:
            add_points(user["id"], llm_cost, "AI拆段JSON解析失败退还")
            raise HTTPException(500, f"LLM返回的JSON无法解析，请重试。原始返回: {result_text[:500]}")
        assets = script_data.get("assets", [])
        segments = script_data.get("segments", [])
    else:
        # ─── Long script: two-pass (chapter split → segment split per chapter) ───
        # Pass 1: Split into chapters
        chapter_prompt = CHAPTER_SPLIT_PROMPT.format(duration=req.duration_per_segment)
        chapter_result = _call_llm(chapter_prompt, raw_script, uid=user["id"], max_tokens=65536)
        if chapter_result.startswith("ERROR:"):
            add_points(user["id"], llm_cost, "AI拆段失败退还")
            raise HTTPException(500, f"章节划分失败: {chapter_result}")

        chapter_data = _parse_llm_json(chapter_result)
        if not chapter_data or "chapters" not in chapter_data:
            add_points(user["id"], llm_cost, "AI拆段失败退还")
            raise HTTPException(500, f"章节划分JSON解析失败，请重试。原始返回: {chapter_result[:500]}")

        chapters = chapter_data["chapters"]
        if not chapters:
            add_points(user["id"], llm_cost, "AI拆段失败退还")
            raise HTTPException(500, "章节划分为空，请重试")

        # Pass 2: Split each chapter into segments (parallel via threads)
        all_assets = []
        all_segments = []
        segment_id_offset = 0
        asset_name_map = {}  # dedup assets across chapters

        def _split_chapter(chapter_idx, chapter):
            """Split a single chapter into segments. Returns (assets, segments)."""
            ch_title = chapter.get("title", f"第{chapter_idx+1}章")
            ch_summary = chapter.get("summary", "")
            ch_text = chapter.get("text", "")
            if not ch_text:
                return [], []
            # Add chapter context to the system prompt
            ch_context = f"\n\n【当前章节上下文】\n章节：{ch_title}\n摘要：{ch_summary}\n这是第{chapter_idx+1}章（共{len(chapters)}章）。请只输出本章的分镜段，不要输出其他章节的内容。"
            ch_system = system_prompt + ch_context
            result = _call_llm(ch_system, ch_text, uid=user["id"], max_tokens=65536)
            if result.startswith("ERROR:"):
                return [], []
            data = _parse_llm_json(result)
            if not data:
                return [], []
            return data.get("assets", []), data.get("segments", [])

        # Use threads for parallel LLM calls (max 3 concurrent)
        from concurrent.futures import ThreadPoolExecutor, as_completed
        chapter_results = [None] * len(chapters)
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_idx = {}
            for i, ch in enumerate(chapters):
                future = executor.submit(_split_chapter, i, ch)
                future_to_idx[future] = i
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    chapter_results[idx] = future.result()
                except Exception as e:
                    print(f"[ai-split] Chapter {idx+1} failed: {e}")
                    chapter_results[idx] = ([], [])

        # Merge results
        for idx, (ch_assets, ch_segments) in enumerate(chapter_results):
            if not ch_assets and not ch_segments:
                continue
            # Dedup assets: if asset name already exists, skip
            for asset in ch_assets:
                name = asset.get("name", "")
                if name and name not in asset_name_map:
                    asset_name_map[name] = asset
                    all_assets.append(asset)
            # Offset segment IDs and add chapter info
            for seg in ch_segments:
                seg["id"] = segment_id_offset + seg.get("id", 1)
                seg["chapter"] = chapters[idx].get("title", f"第{idx+1}章")
                all_segments.append(seg)
                segment_id_offset = seg["id"]

        # Re-index segments sequentially
        for i, seg in enumerate(all_segments):
            seg["id"] = i + 1

        assets = all_assets
        segments = all_segments

        if not segments:
            add_points(user["id"], llm_cost, "AI拆段失败退还")
            raise HTTPException(500, "所有章节拆段均失败，请重试或缩短剧本")

    # Update project script
    db = _get_conn()
    script_data = {"style": "", "assets": assets, "segments": segments}
    script_json = json.dumps(script_data, ensure_ascii=False)
    db.execute("""
        UPDATE projects SET script=?, segments_json=?, assets_json=?, updated_at=?
        WHERE id=? AND user_id=?
    """, (script_json, json.dumps(segments, ensure_ascii=False),
          json.dumps(assets, ensure_ascii=False), time.time(),
          project_id, user["id"]))
    db.commit()
    db.close()

    return {
        "ok": True,
        "assets": assets,
        "segments": segments,
        "assets_count": len(assets),
        "segments_count": len(segments)
    }


def _parse_llm_json(text: str) -> dict:
    """Parse JSON from LLM response text. Returns dict or None."""
    json_str = text.strip()
    if "```json" in json_str:
        json_str = json_str.split("```json")[1].split("```")[0].strip()
    elif "```" in json_str:
        json_str = json_str.split("```")[1].split("```")[0].strip()
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{[\s\S]*\}', json_str)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                return None
        return None


# ==================== Agent Chat ====================

AGENT_SYSTEM_PROMPT = """你是"锤子导演"，一个专业的AI影视分镜助手。你正在帮用户制作一部AI生成的短片。

当前项目状态：
{project_context}

你的核心职责是**实际修改项目内容并触发生成**，不是只给建议。当用户要求修改时，你必须调用工具来执行；当用户要求生成时，你必须调用生成工具来触发。

## 核心导演系统（分镜铁律，必须遵守）

VERTICAL_CINEMA_PLACEHOLDER

---

## 数据修改工具
- 用户要求添加/删除/修改资产或分镜时，立即调用对应工具执行
- 用户只问问题不要求修改时，正常回答即可
- 一次可以调用多个工具（比如"添加3个角色"可以一次调3次add_asset）
- 资产名必须简短，type只能是"角色"、"场景"或"道具"
- prompt是英文提示词，描述该资产的外观、风格，用于AI生图

## 生成工具（核心能力）
- **generate_assets**: 触发资产生图（定妆照/参考图）。多形态角色会自动垫图。建议：先修改好资产再生成。
- **generate_storyboard**: 触发故事板生图。会自动垫入已完成的资产参考图。建议：资产图生成完成后再生成故事板。
- **generate_video**: 触发视频生成。会自动构建英文视频提示词并垫入资产图作为参考。建议：资产图生成完成后再生成视频。
- **check_status**: 查看各阶段生成进度。生成是异步的，调用后可用此工具查看进度。
- **retry_failed**: 重试所有失败的生成任务。

## 生成流程建议
1. 先编辑好资产（角色/场景/道具）和分镜
2. generate_assets → 等资产图完成 → check_status确认
3. generate_storyboard → 等故事板完成 → check_status确认
4. generate_video → 等视频完成 → check_status确认
5. 如有失败 → retry_failed

回复用中文，简洁专业。"""


AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_asset",
            "description": "添加一个资产（角色/场景/道具）。资产会立即写入项目。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "资产名，如'沈清晏'、'灵堂'、'圣旨'"},
                    "type": {"type": "string", "enum": ["角色", "场景", "道具"], "description": "资产类型"},
                    "prompt": {"type": "string", "description": "英文提示词，描述外观风格，用于AI生图。如：A 25-year-old Chinese woman in white mourning dress, photorealistic, clean background"}
                },
                "required": ["name", "type", "prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remove_asset",
            "description": "删除指定索引的资产。索引从0开始。",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer", "description": "要删除的资产索引（从0开始）"}
                },
                "required": ["index"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_asset",
            "description": "修改指定资产的字段（名字、类型、提示词）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer", "description": "资产索引（从0开始）"},
                    "name": {"type": "string", "description": "新名字（可选）"},
                    "type": {"type": "string", "enum": ["角色", "场景", "道具"], "description": "新类型（可选）"},
                    "prompt": {"type": "string", "description": "新英文提示词（可选）"}
                },
                "required": ["index"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_segment",
            "description": "添加一个分镜段。段会追加到末尾。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "段标题，如'圣旨到'"},
                    "shots": {
                        "type": "array",
                        "description": "镜头列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "time": {"type": "string", "description": "时间范围，如'0s-3s'"},
                                "type": {"type": "string", "description": "景别，如'中近景'"},
                                "camera": {"type": "string", "description": "英文运镜，如'slow dolly-in'"},
                                "visual": {"type": "string", "description": "画面描述（英文，给视频生成模型用）"},
                                "lighting": {"type": "string", "description": "光线描述"},
                                "dialogue": {"type": "string", "description": "台词，格式'角色：台词'"},
                                "audio": {"type": "string", "description": "音效描述"},
                                "transition": {"type": "string", "description": "转场方式：cut/dissolve/camera_pan/camera_push/fade_black/end"}
                            },
                            "required": ["time", "visual"]
                        }
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remove_segment",
            "description": "删除指定索引的分镜段。索引从0开始。",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer", "description": "要删除的段索引（从0开始）"}
                },
                "required": ["index"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_shot",
            "description": "修改某个段中某个镜头的字段。",
            "parameters": {
                "type": "object",
                "properties": {
                    "segment_index": {"type": "integer", "description": "段索引（从0开始）"},
                    "shot_index": {"type": "integer", "description": "镜头索引（从0开始）"},
                    "visual": {"type": "string", "description": "新画面描述（可选）"},
                    "camera": {"type": "string", "description": "新运镜方式（可选）"},
                    "dialogue": {"type": "string", "description": "新台词（可选）"},
                    "lighting": {"type": "string", "description": "新光线描述（可选）"},
                    "audio": {"type": "string", "description": "新音效描述（可选）"},
                    "transition": {"type": "string", "description": "新转场方式（可选）"}
                },
                "required": ["segment_index", "shot_index"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_script",
            "description": "完全替换整个脚本（资产+分镜）。慎用，仅在需要大规模重写时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "assets": {
                        "type": "array",
                        "description": "新资产列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                                "prompt": {"type": "string"}
                            },
                            "required": ["name", "type", "prompt"]
                        }
                    },
                    "segments": {
                        "type": "array",
                        "description": "新分镜段列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "title": {"type": "string"},
                                "assets": {"type": "array", "items": {"type": "object"}},
                                "shots": {"type": "array", "items": {"type": "object"}}
                            },
                            "required": ["id", "title", "shots"]
                        }
                    }
                },
                "required": ["assets", "segments"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_assets",
            "description": "触发资产图片生成（Phase 2）。为所有没有生成结果的资产生成定妆照/参考图。多形态角色会自动垫图。生成是异步的，调用后立即返回，可用check_status查看进度。",
            "parameters": {
                "type": "object",
                "properties": {
                    "indices": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "要生成的资产索引列表（从0开始）。不传则生成全部资产。"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_storyboard",
            "description": "触发故事板图片生成（Phase 3）。为指定段生成分镜故事板图，会自动垫入已生成的资产参考图。生成是异步的，调用后立即返回。",
            "parameters": {
                "type": "object",
                "properties": {
                    "segment_index": {
                        "type": "integer",
                        "description": "段索引（从0开始）。不传则生成全部段的故事板。"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_video",
            "description": "触发视频生成（Phase 4）。为指定段生成视频，会自动垫入资产图作为参考。视频提示词会自动从分镜数据构建（英文）。生成是异步的，调用后立即返回。",
            "parameters": {
                "type": "object",
                "properties": {
                    "segment_index": {
                        "type": "integer",
                        "description": "段索引（从0开始）。不传则生成全部段的视频。"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_status",
            "description": "查看项目各阶段的生成状态（资产/故事板/视频的完成情况）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "phase": {
                        "type": "string",
                        "enum": ["assets", "storyboard", "video", "all"],
                        "description": "要查看的阶段。assets=资产生成, storyboard=故事板, video=视频, all=全部。默认all。"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "retry_failed",
            "description": "重试失败的生成任务。会重新提交所有失败（failed）的资产/故事板/视频生成。",
            "parameters": {
                "type": "object",
                "properties": {
                    "phase": {
                        "type": "string",
                        "enum": ["assets", "storyboard", "video", "all"],
                        "description": "要重试的阶段。assets=资产, storyboard=故事板, video=视频, all=全部失败任务。默认all。"
                    }
                },
                "required": []
            }
        }
    }
]


def _execute_agent_tool(tool_name: str, tool_args: dict, project_id: int, uid: int,
                         assets: list, segments: list,
                         script_modified: bool = False,
                         modified_asset_indices: list = None,
                         modified_segment_indices: list = None) -> dict:
    """执行单个Agent工具调用，返回 {success, message, assets, segments, script_modified, modified_asset_indices, modified_segment_indices}。"""
    if modified_asset_indices is None:
        modified_asset_indices = []
    if modified_segment_indices is None:
        modified_segment_indices = []

    if tool_name == "add_asset":
        new_asset = {
            "name": tool_args.get("name", ""),
            "type": tool_args.get("type", "角色"),
            "prompt": tool_args.get("prompt", "")
        }
        assets.append(new_asset)
        script_modified = True
        modified_asset_indices.append(len(assets) - 1)  # 新增的资产索引
        return {"success": True, "message": f"已添加资产：{new_asset['name']}({new_asset['type']})", "assets": assets, "segments": segments, "script_modified": True, "modified_asset_indices": modified_asset_indices, "modified_segment_indices": modified_segment_indices}

    elif tool_name == "remove_asset":
        idx = tool_args.get("index", -1)
        if 0 <= idx < len(assets):
            removed = assets.pop(idx)
            modified_asset_indices = list(range(len(assets)))  # 删除后索引全部偏移，全部需重检
            return {"success": True, "message": f"已删除资产：{removed.get('name', '?')}(索引{idx})", "assets": assets, "segments": segments, "script_modified": True, "modified_asset_indices": modified_asset_indices, "modified_segment_indices": modified_segment_indices}
        return {"success": False, "message": f"删除资产失败：索引{idx}越界（共{len(assets)}个资产）", "assets": assets, "segments": segments, "script_modified": False, "modified_asset_indices": [], "modified_segment_indices": []}

    elif tool_name == "update_asset":
        idx = tool_args.get("index", -1)
        if 0 <= idx < len(assets):
            asset = assets[idx]
            old_name = asset.get("name", "?")
            if "name" in tool_args:
                asset["name"] = tool_args["name"]
            if "type" in tool_args:
                asset["type"] = tool_args["type"]
            if "prompt" in tool_args:
                asset["prompt"] = tool_args["prompt"]
            modified_asset_indices.append(idx)  # 这个资产的生成结果需要清除
            return {"success": True, "message": f"已修改资产：{old_name}→{asset.get('name', old_name)}", "assets": assets, "segments": segments, "script_modified": True, "modified_asset_indices": modified_asset_indices, "modified_segment_indices": modified_segment_indices}
        return {"success": False, "message": f"修改资产失败：索引{idx}越界", "assets": assets, "segments": segments, "script_modified": False, "modified_asset_indices": [], "modified_segment_indices": []}

    elif tool_name == "add_segment":
        new_segment = {
            "id": len(segments) + 1,
            "title": tool_args.get("title", ""),
            "assets": [],
            "shots": tool_args.get("shots", [])
        }
        segments.append(new_segment)
        modified_segment_indices.append(len(segments) - 1)
        return {"success": True, "message": f"已添加段：{new_segment['title']}", "assets": assets, "segments": segments, "script_modified": True, "modified_asset_indices": modified_asset_indices, "modified_segment_indices": modified_segment_indices}

    elif tool_name == "remove_segment":
        idx = tool_args.get("index", -1)
        if 0 <= idx < len(segments):
            removed = segments.pop(idx)
            modified_segment_indices = list(range(len(segments)))
            return {"success": True, "message": f"已删除段：{removed.get('title', '?')}(索引{idx})", "assets": assets, "segments": segments, "script_modified": True, "modified_asset_indices": modified_asset_indices, "modified_segment_indices": modified_segment_indices}
        return {"success": False, "message": f"删除段失败：索引{idx}越界（共{len(segments)}段）", "assets": assets, "segments": segments, "script_modified": False, "modified_asset_indices": [], "modified_segment_indices": []}

    elif tool_name == "update_shot":
        si = tool_args.get("segment_index", -1)
        shi = tool_args.get("shot_index", -1)
        if 0 <= si < len(segments) and 0 <= shi < len(segments[si].get("shots", [])):
            shot = segments[si]["shots"][shi]
            updated_fields = []
            for field in ["visual", "camera", "dialogue", "lighting", "audio", "transition"]:
                if field in tool_args:
                    shot[field] = tool_args[field]
                    updated_fields.append(field)
            seg_title = segments[si].get("title", f"段{si+1}")
            modified_segment_indices.append(si)  # 这个段的视频结果需要清除
            return {"success": True, "message": f"已修改段{si+1}「{seg_title}」镜{shi+1}的字段：{','.join(updated_fields)}", "assets": assets, "segments": segments, "script_modified": True, "modified_asset_indices": modified_asset_indices, "modified_segment_indices": modified_segment_indices}
        return {"success": False, "message": f"修改镜头失败：段索引{si}或镜索引{shi}越界", "assets": assets, "segments": segments, "script_modified": False, "modified_asset_indices": [], "modified_segment_indices": []}

    elif tool_name == "update_script":
        new_assets = tool_args.get("assets", assets)
        new_segments = tool_args.get("segments", segments)
        # 全量替换，所有资产和段都需要重新生成
        all_asset_indices = list(range(len(new_assets)))
        all_segment_indices = list(range(len(new_segments)))
        return {"success": True, "message": f"已替换整个脚本：{len(new_assets)}个资产，{len(new_segments)}段", "assets": new_assets, "segments": new_segments, "script_modified": True, "modified_asset_indices": all_asset_indices, "modified_segment_indices": all_segment_indices}

    # === 生成类工具 ===
    elif tool_name == "generate_assets":
        # Save any pending script changes before generating
        if script_modified:
            _save_project_script(project_id, uid, assets, segments,
                                 modified_asset_indices=modified_asset_indices if modified_asset_indices else None,
                                 modified_segment_indices=modified_segment_indices if modified_segment_indices else None)
            script_modified = False
            modified_asset_indices = []
            modified_segment_indices = []

        indices = tool_args.get("indices", None)
        # 获取最新的project数据
        project = _get_project_data(project_id, uid)
        current_assets = json.loads(project.get("assets_json", "[]"))
        if not current_assets:
            return {"success": False, "message": "没有资产定义，请先添加资产", "assets": assets, "segments": segments, "script_modified": False}

        # 确定要生成的索引
        if indices:
            target_indices = [i for i in indices if 0 <= i < len(current_assets)]
        else:
            target_indices = list(range(len(current_assets)))

        if not target_indices:
            return {"success": False, "message": "没有有效的资产索引", "assets": assets, "segments": segments, "script_modified": False}

        # 逐个调用单资产生成
        results_log = []
        for idx in target_indices:
            try:
                res = generate_single_asset(project_id, idx, user={"id": uid})
                results_log.append(f"资产{idx}「{current_assets[idx].get('name','?')}」: {res.get('status','?')}")
            except HTTPException as e:
                results_log.append(f"资产{idx}「{current_assets[idx].get('name','?')}」: 失败-{e.detail}")
            except Exception as e:
                results_log.append(f"资产{idx}「{current_assets[idx].get('name','?')}」: 异常-{str(e)[:100]}")

        msg = f"已触发{len(target_indices)}个资产生成：\n" + "\n".join(results_log)
        return {"success": True, "message": msg, "assets": assets, "segments": segments, "script_modified": False}

    elif tool_name == "generate_storyboard":
        # Save any pending script changes before generating
        if script_modified:
            _save_project_script(project_id, uid, assets, segments,
                                 modified_asset_indices=modified_asset_indices if modified_asset_indices else None,
                                 modified_segment_indices=modified_segment_indices if modified_segment_indices else None)
            script_modified = False
            modified_asset_indices = []
            modified_segment_indices = []

        seg_index = tool_args.get("segment_index", None)
        project = _get_project_data(project_id, uid)
        current_segments = json.loads(project.get("segments_json", "[]"))
        if not current_segments:
            return {"success": False, "message": "没有分镜数据，请先添加分镜段", "assets": assets, "segments": segments, "script_modified": False}

        if seg_index is not None:
            target_indices = [seg_index] if 0 <= seg_index < len(current_segments) else []
        else:
            target_indices = list(range(len(current_segments)))

        if not target_indices:
            return {"success": False, "message": f"段索引{seg_index}越界（共{len(current_segments)}段）", "assets": assets, "segments": segments, "script_modified": False}

        results_log = []
        for idx in target_indices:
            try:
                res = generate_single_storyboard(project_id, idx, user={"id": uid})
                results_log.append(f"段{idx}「{current_segments[idx].get('title','?')}」: {res.get('status','?')}")
            except HTTPException as e:
                results_log.append(f"段{idx}「{current_segments[idx].get('title','?')}」: 失败-{e.detail}")
            except Exception as e:
                results_log.append(f"段{idx}「{current_segments[idx].get('title','?')}」: 异常-{str(e)[:100]}")

        msg = f"已触发{len(target_indices)}段故事板生成：\n" + "\n".join(results_log)
        return {"success": True, "message": msg, "assets": assets, "segments": segments, "script_modified": False}

    elif tool_name == "generate_video":
        # Save any pending script changes before generating
        if script_modified:
            _save_project_script(project_id, uid, assets, segments,
                                 modified_asset_indices=modified_asset_indices if modified_asset_indices else None,
                                 modified_segment_indices=modified_segment_indices if modified_segment_indices else None)
            script_modified = False
            modified_asset_indices = []
            modified_segment_indices = []

        seg_index = tool_args.get("segment_index", None)
        project = _get_project_data(project_id, uid)
        current_segments = json.loads(project.get("segments_json", "[]"))
        if not current_segments:
            return {"success": False, "message": "没有分镜数据，请先添加分镜段", "assets": assets, "segments": segments, "script_modified": False}

        if seg_index is not None:
            target_indices = [seg_index] if 0 <= seg_index < len(current_segments) else []
        else:
            target_indices = list(range(len(current_segments)))

        if not target_indices:
            return {"success": False, "message": f"段索引{seg_index}越界（共{len(current_segments)}段）", "assets": assets, "segments": segments, "script_modified": False}

        results_log = []
        for idx in target_indices:
            try:
                # 使用空prompt让系统自动构建视频提示词
                req = VideoGenReq(prompt="")
                res = generate_single_video(project_id, idx, req=req, user={"id": uid})
                results_log.append(f"段{idx}「{current_segments[idx].get('title','?')}」: {res.get('status','?')}")
            except HTTPException as e:
                results_log.append(f"段{idx}「{current_segments[idx].get('title','?')}」: 失败-{e.detail}")
            except Exception as e:
                results_log.append(f"段{idx}「{current_segments[idx].get('title','?')}」: 异常-{str(e)[:100]}")

        msg = f"已触发{len(target_indices)}段视频生成：\n" + "\n".join(results_log)
        return {"success": True, "message": msg, "assets": assets, "segments": segments, "script_modified": False}

    elif tool_name == "check_status":
        phase = tool_args.get("phase", "all")
        project = _get_project_data(project_id, uid)
        results = json.loads(project.get("results_json", "{}"))
        current_assets = json.loads(project.get("assets_json", "[]"))
        current_segments = json.loads(project.get("segments_json", "[]"))

        status_parts = []

        if phase in ("assets", "all"):
            phase2 = results.get("phase2", [])
            done = sum(1 for x in phase2 if x.get("status") == "completed")
            running = sum(1 for x in phase2 if x.get("status") == "running")
            failed = sum(1 for x in phase2 if x.get("status") == "failed")
            pending = len(current_assets) - done - running - failed
            status_parts.append(f"资产({len(current_assets)}): 完成{done} 生成中{running} 失败{failed} 待生成{pending}")
            # 列出失败项
            for i, r in enumerate(phase2):
                if r.get("status") == "failed":
                    status_parts.append(f"  ✗ 资产{i}「{r.get('name','?')}」: {r.get('error','未知错误')[:80]}")

        if phase in ("storyboard", "all"):
            phase3 = results.get("phase3", [])
            done = sum(1 for x in phase3 if x.get("status") == "completed")
            running = sum(1 for x in phase3 if x.get("status") == "running")
            failed = sum(1 for x in phase3 if x.get("status") == "failed")
            pending = len(current_segments) - done - running - failed
            status_parts.append(f"故事板({len(current_segments)}): 完成{done} 生成中{running} 失败{failed} 待生成{pending}")
            for i, r in enumerate(phase3):
                if r.get("status") == "failed":
                    status_parts.append(f"  ✗ 段{i}「{r.get('title','?')}」: {r.get('error','未知错误')[:80]}")

        if phase in ("video", "all"):
            phase4 = results.get("phase4", [])
            done = sum(1 for x in phase4 if x.get("status") == "completed")
            running = sum(1 for x in phase4 if x.get("status") == "running")
            failed = sum(1 for x in phase4 if x.get("status") == "failed")
            pending = len(current_segments) - done - running - failed
            status_parts.append(f"视频({len(current_segments)}): 完成{done} 生成中{running} 失败{failed} 待生成{pending}")
            for i, r in enumerate(phase4):
                if r.get("status") == "failed":
                    status_parts.append(f"  ✗ 段{i}「{r.get('title','?')}」: {r.get('error','未知错误')[:80]}")

        msg = "\n".join(status_parts) if status_parts else "暂无生成记录"
        return {"success": True, "message": msg, "assets": assets, "segments": segments, "script_modified": False}

    elif tool_name == "retry_failed":
        phase = tool_args.get("phase", "all")
        project = _get_project_data(project_id, uid)
        results = json.loads(project.get("results_json", "{}"))
        current_assets = json.loads(project.get("assets_json", "[]"))
        current_segments = json.loads(project.get("segments_json", "[]"))

        retry_log = []

        # 重试失败的资产
        if phase in ("assets", "all"):
            phase2 = results.get("phase2", [])
            for i, r in enumerate(phase2):
                if r.get("status") == "failed" and i < len(current_assets):
                    try:
                        res = generate_single_asset(project_id, i, user={"id": uid})
                        retry_log.append(f"资产{i}「{current_assets[i].get('name','?')}」: 已重新提交-{res.get('status','?')}")
                    except Exception as e:
                        retry_log.append(f"资产{i}「{current_assets[i].get('name','?')}」: 重试失败-{str(e)[:80]}")

        # 重试失败的故事板
        if phase in ("storyboard", "all"):
            phase3 = results.get("phase3", [])
            for i, r in enumerate(phase3):
                if r.get("status") == "failed" and i < len(current_segments):
                    try:
                        res = generate_single_storyboard(project_id, i, user={"id": uid})
                        retry_log.append(f"段{i}「{current_segments[i].get('title','?')}」故事板: 已重新提交-{res.get('status','?')}")
                    except Exception as e:
                        retry_log.append(f"段{i}「{current_segments[i].get('title','?')}」故事板: 重试失败-{str(e)[:80]}")

        # 重试失败的视频
        if phase in ("video", "all"):
            phase4 = results.get("phase4", [])
            for i, r in enumerate(phase4):
                if r.get("status") == "failed" and i < len(current_segments):
                    try:
                        req = VideoGenReq(prompt="")
                        res = generate_single_video(project_id, i, req=req, user={"id": uid})
                        retry_log.append(f"段{i}「{current_segments[i].get('title','?')}」视频: 已重新提交-{res.get('status','?')}")
                    except Exception as e:
                        retry_log.append(f"段{i}「{current_segments[i].get('title','?')}」视频: 重试失败-{str(e)[:80]}")

        if not retry_log:
            msg = "没有失败的任务需要重试"
        else:
            msg = f"已重试{len(retry_log)}个失败任务：\n" + "\n".join(retry_log)
        return {"success": True, "message": msg, "assets": assets, "segments": segments, "script_modified": False}

    return {"success": False, "message": f"未知工具：{tool_name}", "assets": assets, "segments": segments, "script_modified": False}


def _save_project_script(project_id: int, uid: int, assets: list, segments: list,
                          modified_asset_indices: list = None, modified_segment_indices: list = None):
    """保存资产和分镜到数据库。如果指定了修改的索引，清除对应项的旧生成结果，强制重新生成。"""
    script_data = {"assets": assets, "segments": segments}
    db = _get_conn()
    
    # 清除被修改资产的旧生成结果（phase2），使其需要重新生成
    if modified_asset_indices:
        row = db.execute("SELECT results_json FROM projects WHERE id=? AND user_id=?", (project_id, uid)).fetchone()
        if row and row["results_json"]:
            results = json.loads(row["results_json"])
            phase2 = results.get("phase2", [])
            for idx in modified_asset_indices:
                if 0 <= idx < len(phase2):
                    # 保留名字，清除生成结果
                    old_name = phase2[idx].get("name", "")
                    phase2[idx] = {"name": old_name, "status": "pending"}
            results["phase2"] = phase2
            db.execute("UPDATE projects SET results_json=? WHERE id=? AND user_id=?",
                       (json.dumps(results, ensure_ascii=False), project_id, uid))
    
    # 清除被修改段的旧故事板结果（phase3），使其需要重新生成
    if modified_segment_indices:
        row = db.execute("SELECT results_json FROM projects WHERE id=? AND user_id=?", (project_id, uid)).fetchone()
        if row and row["results_json"]:
            results = json.loads(row["results_json"])
            phase3 = results.get("phase3", [])
            for idx in modified_segment_indices:
                if 0 <= idx < len(phase3):
                    old_title = phase3[idx].get("title", "")
                    phase3[idx] = {"title": old_title, "status": "pending"}
            results["phase3"] = phase3
            # 同时清除phase4视频结果
            phase4 = results.get("phase4", [])
            for idx in modified_segment_indices:
                if 0 <= idx < len(phase4):
                    old_title = phase4[idx].get("title", "")
                    phase4[idx] = {"title": old_title, "status": "pending"}
            results["phase4"] = phase4
            db.execute("UPDATE projects SET results_json=? WHERE id=? AND user_id=?",
                       (json.dumps(results, ensure_ascii=False), project_id, uid))
    
    db.execute("""
        UPDATE projects SET script=?, segments_json=?, assets_json=?, updated_at=?
        WHERE id=? AND user_id=?
    """, (json.dumps(script_data, ensure_ascii=False),
          json.dumps(segments, ensure_ascii=False),
          json.dumps(assets, ensure_ascii=False),
          time.time(), project_id, uid))
    db.commit()
    db.close()


def _build_context_for_query(message: str, project: dict) -> str:
    """按需构建上下文——根据用户问题检索相关信息，不全量塞入。
    
    策略：
    - 始终包含：项目基本信息 + 资产列表（名字+类型）
    - 提到具体段号/段名 → 包含该段完整镜头数据
    - 提到角色/场景/道具 → 包含对应资产的完整prompt
    - 提到剧本/故事/整体 → 包含原始剧本摘要
    - 提到运镜/节奏/镜头 → 包含所有段的镜头摘要
    """
    assets = json.loads(project.get("assets_json", "[]"))
    segments = json.loads(project.get("segments_json", "[]"))
    results = json.loads(project.get("results_json", "{}"))
    raw_script = project.get("raw_script", "")

    phase2_done = sum(1 for x in results.get("phase2", []) if x.get("status") == "completed")
    phase3_done = sum(1 for x in results.get("phase3", []) if x.get("status") == "completed")
    phase4_done = sum(1 for x in results.get("phase4", []) if x.get("status") == "completed")

    # 1. 始终包含：基本信息
    context = f"项目: {project['name']} | {project['video_model']} | {project['ratio']} | {project['duration']}s/段\n"

    # 2. 始终包含：资产列表（名字+类型+生成状态）
    phase2_results = results.get("phase2", [])
    asset_status_parts = []
    for i, a in enumerate(assets):
        st = ""
        if i < len(phase2_results):
            st = phase2_results[i].get("status", "待生成")
            if st == "completed":
                st = "✓"
            elif st == "running":
                st = "⏳"
            elif st == "failed":
                st = "✗"
            else:
                st = "待生成"
        else:
            st = "待生成"
        asset_status_parts.append(f"{a.get('name','?')}({a.get('type','?')}){st}")
    context += f"资产({len(assets)}): " + ", ".join(asset_status_parts) + "\n"

    # 3. 判断用户问题需要什么信息
    msg = message.lower()
    
    # 是否提到具体段
    mentioned_segments = set()
    import re
    # 匹配"第X段"、"段X"、"第X幕"
    for m in re.finditer(r'第?(\d+)[段幕]', msg):
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(segments):
            mentioned_segments.add(idx)
    # 匹配段标题
    for i, seg in enumerate(segments):
        title = seg.get("title", "").lower()
        if title and title in msg:
            mentioned_segments.add(i)

    # 是否提到角色/场景/道具
    mention_assets = any(a.get("name", "").lower() in msg for a in assets if a.get("name"))
    # 是否提到剧本/故事/整体
    mention_story = any(kw in msg for kw in ["剧本", "故事", "整体", "剧情", "大纲", "梗概", "全部", "所有"])
    # 是否提到运镜/节奏/镜头
    mention_camera = any(kw in msg for kw in ["运镜", "镜头", "节奏", "景别", "构图", "推近", "拉远", "摇", "俯拍", "仰拍", "跟拍"])
    # 是否提到修改/调整
    mention_modify = any(kw in msg for kw in ["改", "调", "加", "删", "换", "修", "优化", "调整", "增加", "减少"])

    # 4. 按需加载详细资产信息
    if mention_assets or mention_modify:
        context += "\n资产详情:\n"
        for a in assets:
            context += f"  - {a.get('name','?')}({a.get('type','?')}): {a.get('prompt','')}\n"

    # 5. 按需加载分镜信息
    if mentioned_segments:
        # 只加载提到的段（完整镜头数据）
        context += f"\n相关分镜段:\n"
        for i in sorted(mentioned_segments):
            seg = segments[i]
            context += f"段{i+1}「{seg.get('title','')}」:\n"
            for j, sh in enumerate(seg.get("shots", [])):
                context += f"  镜{j+1}: 画面={sh.get('visual','')} 运镜={sh.get('camera','')} 台词={sh.get('dialogue','')}\n"
    elif mention_camera or mention_modify:
        # 运镜/修改相关：加载所有段的镜头摘要
        context += f"\n分镜段({len(segments)}段):\n"
        for i, seg in enumerate(segments):
            context += f"段{i+1}「{seg.get('title','')}」:\n"
            for j, sh in enumerate(seg.get("shots", [])):
                context += f"  镜{j+1}: 画面={sh.get('visual','')} 运镜={sh.get('camera','')} 台词={sh.get('dialogue','')}\n"
    else:
        # 默认：只显示段标题+镜头数
        context += f"\n分镜段({len(segments)}段): " + "、".join(f"段{i+1}「{seg.get('title','')}」({len(seg.get('shots',[]))}镜)" for i, seg in enumerate(segments)) + "\n"

    # 6. 进度
    context += f"\n进度: 资产{phase2_done}/{len(assets)} 故事板{phase3_done}/{len(segments)} 视频{phase4_done}/{len(segments)}"

    # 6.5 视频生成状态（哪些段有视频）
    phase4_results = results.get("phase4", [])
    phase3_results = results.get("phase3", [])
    video_status_parts = []
    storyboard_status_parts = []
    for i in range(len(segments)):
        seg_title = segments[i].get("title", f"段{i+1}")
        # Storyboard status
        if i < len(phase3_results):
            sb_st = phase3_results[i].get("status", "待生成")
            if sb_st == "completed":
                storyboard_status_parts.append(f"段{i+1}「{seg_title}」✓")
            elif sb_st == "running":
                storyboard_status_parts.append(f"段{i+1}「{seg_title}」⏳")
            elif sb_st == "failed":
                storyboard_status_parts.append(f"段{i+1}「{seg_title}」✗")
        else:
            storyboard_status_parts.append(f"段{i+1}「{seg_title}」待生成")
        # Video status
        if i < len(phase4_results):
            v_st = phase4_results[i].get("status", "待生成")
            if v_st == "completed":
                video_status_parts.append(f"段{i+1}「{seg_title}」✓")
            elif v_st == "running":
                video_status_parts.append(f"段{i+1}「{seg_title}」⏳")
            elif v_st == "failed":
                video_status_parts.append(f"段{i+1}「{seg_title}」✗")
        else:
            video_status_parts.append(f"段{i+1}「{seg_title}」待生成")
    if storyboard_status_parts:
        context += f"\n故事板状态: {', '.join(storyboard_status_parts)}"
    if video_status_parts:
        context += f"\n视频状态: {', '.join(video_status_parts)}"

    # 6.6 Style info
    try:
        script_data = json.loads(project.get("script", "{}"))
        style = script_data.get("style", "")
        if style:
            context += f"\n视觉风格: {style}"
        scene_map = script_data.get("scene_map", {})
        if scene_map:
            context += f"\n场景映射: {json.dumps(scene_map, ensure_ascii=False)}"
    except (json.JSONDecodeError, TypeError):
        pass

    # 7. 按需加载原始剧本
    if mention_story or (not segments and raw_script):
        # 剧本相关或还没拆段时，传剧本
        if raw_script:
            context += f"\n\n原始剧本:\n{raw_script}"

    return context


@router.post("/{project_id}/chat")
def agent_chat(project_id: int, req: AgentChatReq, user: dict = Depends(auth_required)):
    """Agent-style chat with LLM using function calling + tool loop."""
    project = _get_project_data(project_id, user["id"])
    assets = json.loads(project.get("assets_json", "[]"))
    segments = json.loads(project.get("segments_json", "[]"))

    # 按需构建上下文
    context = _build_context_for_query(req.message, project)
    system_prompt = AGENT_SYSTEM_PROMPT.format(project_context=context)
    system_prompt = system_prompt.replace("VERTICAL_CINEMA_PLACEHOLDER", _VERTICAL_CINEMA_PROMPT)

    # Build messages list
    messages = [{"role": "system", "content": system_prompt}]
    for h in req.history[-10:]:  # Keep last 10 turns
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": req.message})

    # Deduct small fee (2 points)
    chat_cost = 2
    if not deduct_points(user["id"], chat_cost, "一键成片-Agent对话"):
        raise HTTPException(402, "积分不足")

    # === Function Calling Tool Loop ===
    max_rounds = 15
    tool_results_log = []  # 记录所有工具调用结果
    script_modified = False
    all_modified_asset_indices = []
    all_modified_segment_indices = []

    for round_idx in range(max_rounds):
        # Call LLM with tools
        response = _call_llm_messages(messages, tools=AGENT_TOOLS, uid=user["id"])

        if "error" in response:
            add_points(user["id"], chat_cost, "Agent对话失败退还")
            raise HTTPException(500, f"LLM调用失败: {response['error']}")

        choice = response.get("choices", [{}])[0]
        msg = choice.get("message", {})
        finish_reason = choice.get("finish_reason", "")

        # Extract text content
        text_content = msg.get("content", "") or ""

        # Check if there are tool_calls
        tool_calls = msg.get("tool_calls", [])

        if not tool_calls:
            # No tool calls — AI is done, save and return
            if script_modified:
                _save_project_script(project_id, user["id"], assets, segments,
                                     modified_asset_indices=all_modified_asset_indices if all_modified_asset_indices else None,
                                     modified_segment_indices=all_modified_segment_indices if all_modified_segment_indices else None)

            # Save chat history
            _save_chat_history(project_id, user["id"], req.message, text_content.strip())

            return {
                "reply": text_content.strip(),
                "tool_results": tool_results_log,
                "script_modified": script_modified,
                "assets": assets if script_modified else None,
                "segments": segments if script_modified else None,
                "rounds_used": round_idx + 1
            }

        # Process tool calls
        # Add assistant message with tool_calls to history
        assistant_msg = {"role": "assistant", "content": text_content}
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
        messages.append(assistant_msg)

        # Execute each tool call and add results
        for tc in tool_calls:
            tc_id = tc.get("id", f"call_{round_idx}")
            func = tc.get("function", {})
            tool_name = func.get("name", "")
            try:
                tool_args = json.loads(func.get("arguments", "{}")) if isinstance(func.get("arguments"), str) else func.get("arguments", {})
            except json.JSONDecodeError:
                tool_args = {}

            # Execute the tool
            result = _execute_agent_tool(tool_name, tool_args, project_id, user["id"], assets, segments,
                                         script_modified=script_modified,
                                         modified_asset_indices=all_modified_asset_indices,
                                         modified_segment_indices=all_modified_segment_indices)

            # Update local state
            assets = result["assets"]
            segments = result["segments"]
            if result.get("script_modified"):
                script_modified = True
                # 收集被修改的索引
                for idx in result.get("modified_asset_indices", []):
                    if idx not in all_modified_asset_indices:
                        all_modified_asset_indices.append(idx)
                for idx in result.get("modified_segment_indices", []):
                    if idx not in all_modified_segment_indices:
                        all_modified_segment_indices.append(idx)

            # Log the result
            tool_results_log.append({
                "tool": tool_name,
                "args": tool_args,
                "success": result["success"],
                "message": result["message"]
            })

            # Add tool result to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tc_id,
                "content": result["message"]
            })

    # If we hit max rounds, save whatever we have and return
    if script_modified:
        _save_project_script(project_id, user["id"], assets, segments,
                             modified_asset_indices=all_modified_asset_indices if all_modified_asset_indices else None,
                             modified_segment_indices=all_modified_segment_indices if all_modified_segment_indices else None)

    # Save chat history
    _save_chat_history(project_id, user["id"], req.message, "已执行多轮工具调用，操作完成。")

    return {
        "reply": "已执行多轮工具调用，操作完成。",
        "tool_results": tool_results_log,
        "script_modified": script_modified,
        "assets": assets if script_modified else None,
        "segments": segments if script_modified else None,
        "rounds_used": max_rounds
    }


def _save_chat_history(project_id: int, uid: int, user_message: str, assistant_reply: str):
    """Save a chat turn to the project's chat_history_json."""
    db = _get_conn()
    try:
        row = db.execute("SELECT chat_history_json FROM projects WHERE id=? AND user_id=?",
                         (project_id, uid)).fetchone()
        history = json.loads(row["chat_history_json"]) if row and row["chat_history_json"] else []
        # Append new turn
        history.append({"role": "user", "content": user_message, "timestamp": time.time()})
        history.append({"role": "assistant", "content": assistant_reply, "timestamp": time.time()})
        # Keep last 100 turns to avoid unbounded growth
        if len(history) > 200:
            history = history[-200:]
        db.execute("UPDATE projects SET chat_history_json=?, updated_at=? WHERE id=? AND user_id=?",
                   (json.dumps(history, ensure_ascii=False), time.time(), project_id, uid))
        db.commit()
    except Exception as e:
        print(f"[Project] _save_chat_history error: {e}")
    finally:
        db.close()


@router.get("/{project_id}/chat-history")
def get_chat_history(project_id: int, user: dict = Depends(auth_required)):
    """获取项目的聊天历史记录。"""
    db = _get_conn()
    r = db.execute("SELECT chat_history_json FROM projects WHERE id=? AND user_id=?",
                   (project_id, user["id"])).fetchone()
    db.close()
    if not r:
        raise HTTPException(404, "项目不存在")
    history = json.loads(r["chat_history_json"]) if r["chat_history_json"] else []
    return {"history": history, "count": len(history)}


# ==================== Single Item Retry ====================

@router.post("/{project_id}/retry/{phase}/{item_index}")
def retry_item(project_id: int, phase: int, item_index: int, user: dict = Depends(auth_required)):
    """Retry a single failed/timeout item in a phase."""
    project = _get_project_data(project_id, user["id"])
    results = json.loads(project.get("results_json", "{}"))
    phase_key = f"phase{phase}"
    items = results.get(phase_key, [])

    if item_index < 0 or item_index >= len(items):
        raise HTTPException(400, "无效的item索引")

    item = items[item_index]
    if item.get("status") not in ("failed", "timeout", "skipped"):
        raise HTTPException(400, f"只能重试失败/超时/跳过的项目，当前状态: {item.get('status')}")

    uid = user["id"]

    if phase == 2:
        return _retry_phase2_item(uid, project, item_index)
    elif phase == 3:
        return _retry_phase3_item(uid, project, item_index)  # 故事板重试
    elif phase == 4:
        return _retry_phase4_item(uid, project, item_index)  # 视频重试
    else:
        raise HTTPException(400, f"阶段{phase}不支持重试")


def _retry_phase2_item(uid: int, project: dict, item_index: int):
    assets = json.loads(project.get("assets_json", "[]"))
    if item_index >= len(assets):
        raise HTTPException(400, "资产索引越界")

    asset = assets[item_index]
    name = asset.get("name", "unknown")
    prompt = asset.get("prompt", "")
    if not prompt:
        raise HTTPException(400, "该资产无prompt")

    image_model = project["image_model"]
    image_resolution = project.get("image_resolution", "1K")
    cost = _calc_image_cost(image_model, image_resolution)
    project_id = project["id"]

    if not deduct_points(uid, cost, f"一键成片-重试资产-{name}"):
        raise HTTPException(402, "积分不足")

    ratio = project.get("ratio", "16:9")
    result = proxy.generate_image(prompt, image_model, ratio, image_resolution)
    if "error" in result:
        add_points(uid, cost, f"重试提交失败退还-{name}")
        raise HTTPException(500, result["error"])

    oiioii_id = result.get("task_id", 0)
    af_id = create_task(uid, "image", image_model, prompt[:500], cost, oiioii_id)

    _update_project_result(project_id, 2, "phase2", item_index, {
        "name": name, "status": "running", "oiioii_task_id": oiioii_id,
        "aiforge_task_id": af_id, "error": ""
    })

    t = threading.Thread(
        target=_poll_and_update_project,
        args=(project_id, 2, oiioii_id, af_id, uid, cost, "phase2", item_index),
        daemon=True
    )
    t.start()

    return {"status": "running", "phase": 2, "item_index": item_index, "cost": cost}


def _retry_phase3_item(uid: int, project: dict, item_index: int):
    segments = json.loads(project.get("segments_json", "[]"))
    if item_index >= len(segments):
        raise HTTPException(400, "段索引越界")

    seg = segments[item_index]
    sid = seg.get("id", item_index)
    title = seg.get("title", "")
    shots = seg.get("shots", [])
    image_model = project["image_model"]
    image_resolution = project.get("image_resolution", "1K")
    cost = _calc_image_cost(image_model, image_resolution)
    project_id = project["id"]

    prompt_parts = [f"Professional film storyboard, vertical 9:16. Segment: {title}"]
    for j, sh in enumerate(shots):
        visual = sh.get("visual", "")[:150]
        camera = sh.get("camera", "")[:80]
        prompt_parts.append(f"Shot {j+1}: {visual}. Camera: {camera}")
    prompt_parts.append("Photorealistic movie stills, cinematic, clean layout with character legend bar at top.")
    prompt = "\n".join(prompt_parts)

    if not deduct_points(uid, cost, f"一键成片-重试故事板-段{sid}"):
        raise HTTPException(402, "积分不足")

    result = proxy.generate_image(prompt, image_model, "9:16", project.get("image_resolution", "1K"))
    if "error" in result:
        add_points(uid, cost, f"重试提交失败退还-段{sid}")
        raise HTTPException(500, result["error"])

    oiioii_id = result.get("task_id", 0)
    af_id = create_task(uid, "image", image_model, prompt[:500], cost, oiioii_id)

    _update_project_result(project_id, 4, "phase4", item_index, {
        "segment_id": sid, "status": "running", "oiioii_task_id": oiioii_id,
        "aiforge_task_id": af_id, "error": ""
    })

    t = threading.Thread(
        target=_poll_and_update_project,
        args=(project_id, 4, oiioii_id, af_id, uid, cost, "phase4", item_index),
        daemon=True
    )
    t.start()

    return {"status": "running", "phase": 4, "item_index": item_index, "cost": cost}


def _retry_phase4_item(uid: int, project: dict, item_index: int):
    segments = json.loads(project.get("segments_json", "[]"))
    if item_index >= len(segments):
        raise HTTPException(400, "段索引越界")

    seg = segments[item_index]
    sid = seg.get("id", item_index)
    title = seg.get("title", "")
    shots = seg.get("shots", [])
    video_model = project["video_model"]
    duration = project["duration"]
    resolution = project["resolution"]
    ratio = project["ratio"]
    cost = _calc_video_cost(video_model, duration, resolution)
    project_id = project["id"]

    script_data = json.loads(project.get("script", "{}"))
    style = script_data.get("style", "Photorealistic, cinematic")
    scene_map = script_data.get("scene_map", {})

    # Collect reference images (absolute URLs)
    results = json.loads(project.get("results_json", "{}"))
    phase2_results = results.get("phase2", [])
    seg_assets = seg.get("assets", [])

    vp = _build_video_prompt(
        segment=seg, duration=duration, style=style,
        seg_asset_names=seg_assets, phase2_results=phase2_results,
        segment_index=item_index, scene_map=scene_map,
    )
    prompt = vp["prompt"]
    ref_images = vp["ref_images"]
    ref_map = vp["ref_map"]

    if not deduct_points(uid, cost, f"一键成片-重试视频-段{sid}"):
        raise HTTPException(402, "积分不足")

    result = proxy.generate_video(
        prompt=prompt, model=video_model, ratio=ratio,
        resolution=resolution, duration=duration,
        reference_images=ref_images if ref_images else None,
        reference_map=ref_map if ref_map else None,
    )
    if "error" in result:
        add_points(uid, cost, f"重试提交失败退还-段{sid}")
        raise HTTPException(500, result["error"])

    oiioii_id = result.get("task_id", 0)
    ref_imgs_str = json.dumps(ref_images[:3]) if ref_images else ""
    af_id = create_task(uid, "video", video_model, prompt[:500], cost, oiioii_id,
                       reference_images=ref_imgs_str)

    _update_project_result(project_id, 4, "phase4", item_index, {
        "segment_id": sid, "status": "running", "oiioii_task_id": oiioii_id,
        "aiforge_task_id": af_id, "error": ""
    })

    t = threading.Thread(
        target=_poll_and_update_project,
        args=(project_id, 4, oiioii_id, af_id, uid, cost, "phase4", item_index),
        daemon=True
    )
    t.start()

    return {"status": "running", "phase": 4, "item_index": item_index, "cost": cost}


# ==================== Batch Download ====================

@router.get("/{project_id}/download/{phase}")
def download_phase_results(project_id: int, phase: int, user: dict = Depends(auth_required)):
    """Download all completed results from a phase as a zip file."""
    project = _get_project_data(project_id, user["id"])
    results = json.loads(project.get("results_json", "{}"))
    phase_key = f"phase{phase}"
    items = results.get(phase_key, [])

    if not items:
        raise HTTPException(400, "该阶段没有结果")

    # Collect completed result files
    import requests as req
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, item in enumerate(items):
            result_url = item.get("result_url", "")
            if not result_url or item.get("status") != "completed":
                continue

            # Get the actual file from oiioii
            oiioii_task_id = item.get("oiioii_task_id", 0)
            if not oiioii_task_id:
                continue

            try:
                task_info = proxy.get_task(oiioii_task_id)
                local_path = task_info.get("local_path", "")
                task_type = task_info.get("type", "")

                if local_path and os.path.isfile(local_path):
                    ext = os.path.splitext(local_path)[1] or (".mp4" if task_type == "video" else ".png")
                    name = item.get("name", item.get("title", f"item_{i}"))
                    # Sanitize filename
                    safe_name = "".join(c for c in name if c.isalnum() or c in "._- ").strip() or f"item_{i}"
                    filename = f"{safe_name}{ext}"
                    zf.write(local_path, filename)
            except Exception as e:
                print(f"[Download] Failed to get file for item {i}: {e}")
                continue

    if not zf.namelist() if hasattr(zf, 'namelist') else buf.tell() == 0:
        # Check if zip is empty
        buf.seek(0)
        test_zf = zipfile.ZipFile(buf, 'r')
        has_files = len(test_zf.namelist()) > 0
        test_zf.close()
        if not has_files:
            raise HTTPException(400, "没有可下载的文件")

    buf.seek(0)
    phase_labels = {2: "资产", 3: "故事板", 4: "视频"}
    zip_name = f"{project['name']}_{phase_labels.get(phase, f'阶段{phase}')}.zip"

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{zip_name}"}
    )


# ==================== Phase Run Functions ====================

def _run_phase1_split(uid: int, project: dict):
    """Phase1: AI拆段——用ViMax架构：先提取角色，再设计分镜。"""
    raw_script = project.get("raw_script", "")
    if not raw_script:
        raise HTTPException(400, "请先上传或粘贴原始剧本")

    llm_cost = 8  # 两步LLM调用，稍贵一点
    if not deduct_points(uid, llm_cost, "一键成片-阶段1AI拆段"):
        raise HTTPException(402, "积分不足")

    duration = project.get("duration", 10)
    project_id = project["id"]

    try:
        from core.vimax import CharacterExtractor, StoryboardExtractor

        # Get user's LLM config
        llm_config = _get_user_llm(uid)

        # Step 1: Extract characters
        extractor = CharacterExtractor()
        characters = extractor.extract(raw_script, llm_config=llm_config)

        # Step 2: Design storyboard with characters context
        storyboard = StoryboardExtractor()
        result = storyboard.extract(raw_script, duration=duration, characters=characters, llm_config=llm_config)

        assets = result.get("assets", [])
        segments = result.get("segments", [])
        style = result.get("style", "Photorealistic, cinematic")

        # Save style to project script
        script_data = {"style": style, "assets": assets, "segments": segments}

    except Exception as e:
        add_points(uid, llm_cost, "AI拆段失败退还")
        raise HTTPException(500, f"AI拆段失败: {str(e)[:200]}")

    db = _get_conn()
    script_json = json.dumps(script_data, ensure_ascii=False)
    db.execute("""
        UPDATE projects SET script=?, segments_json=?, assets_json=?, phase=1, updated_at=?
        WHERE id=? AND user_id=?
    """, (script_json, json.dumps(segments, ensure_ascii=False),
          json.dumps(assets, ensure_ascii=False), time.time(),
          project_id, uid))
    db.commit()
    db.close()

    return {
        "status": "completed", "phase": 1,
        "assets_count": len(assets), "segments_count": len(segments),
        "assets": assets, "segments": segments
    }


def _run_phase2(uid: int, project: dict, db):
    assets = json.loads(project.get("assets_json", "[]"))
    if not assets:
        db.close()
        raise HTTPException(400, "没有资产定义，请先执行AI拆段或手动编辑脚本添加资产")

    image_model = project["image_model"]
    image_resolution = project.get("image_resolution", "1K")
    total_cost = len(assets) * _calc_image_cost(image_model, image_resolution)

    if not deduct_points(uid, total_cost, f"一键成片-阶段2资产生成({len(assets)}张)"):
        db.close()
        raise HTTPException(402, "积分不足")

    project_id = project["id"]

    results = json.loads(project.get("results_json", "{}"))
    results["phase2"] = [{"name": a.get("name", ""), "type": a.get("type", ""), "status": "pending"} for a in assets]
    db.execute("UPDATE projects SET results_json=?, updated_at=? WHERE id=?",
               (json.dumps(results, ensure_ascii=False), time.time(), project_id))
    db.commit()
    db.close()

    ratio = project.get("ratio", "16:9")

    def _generate_assets():
        # Phase 2: Generate assets with reference image support for derived forms
        # Step 1: Sort assets — primary forms first, derived forms after
        primary_indices = []
        derived_indices = []  # (index, reference_form_name)
        for i, asset in enumerate(assets):
            ref_form = asset.get("reference_form")
            is_primary = asset.get("is_primary", True)
            if ref_form and not is_primary:
                derived_indices.append((i, ref_form))
            else:
                primary_indices.append(i)

        # Step 2: Generate primary forms first (no reference images)
        for i in primary_indices:
            asset = assets[i]
            name = asset.get("name", "unknown")
            prompt = asset.get("prompt", "")
            if not prompt:
                _update_project_result(project_id, 2, "phase2", i, {
                    "name": name, "status": "skipped", "reason": "无prompt"
                })
                continue

            result = proxy.generate_image(prompt, image_model, ratio, image_resolution)
            if "error" in result:
                _update_project_result(project_id, 2, "phase2", i, {
                    "name": name, "status": "failed", "error": result["error"]
                })
                cost = _calc_image_cost(image_model, image_resolution)
                add_points(uid, cost, f"资产生图提交失败退还-{name}")
                continue

            oiioii_id = result.get("task_id", 0)
            cost = _calc_image_cost(image_model, image_resolution)
            af_id = create_task(uid, "image", image_model, prompt[:500], cost, oiioii_id)

            _update_project_result(project_id, 2, "phase2", i, {
                "name": name, "status": "running", "oiioii_task_id": oiioii_id,
                "aiforge_task_id": af_id, "prompt": prompt
            })

            t = threading.Thread(
                target=_poll_and_update_project,
                args=(project_id, 2, oiioii_id, af_id, uid, cost, "phase2", i),
                daemon=True
            )
            t.start()
            time.sleep(0.5)

        # Step 3: Wait for primary forms to complete (poll up to 120s)
        if derived_indices:
            time.sleep(5)  # Initial wait
            for _ in range(24):  # 24 x 5s = 120s max
                all_done = True
                current_results = _get_project_results(project_id)
                phase2_res = current_results.get("phase2", [])
                for i in primary_indices:
                    if i < len(phase2_res):
                        st = phase2_res[i].get("status", "pending")
                        if st in ("pending", "running"):
                            all_done = False
                            break
                if all_done:
                    break
                time.sleep(5)

        # Step 4: Generate derived forms with reference images from their primary form
        if derived_indices:
            current_results = _get_project_results(project_id)
            phase2_res = current_results.get("phase2", [])

            # Build name→result_url mapping from completed primary forms
            name_to_url = {}
            for i in primary_indices:
                if i < len(phase2_res) and phase2_res[i].get("result_url"):
                    asset_name = assets[i].get("name", "")
                    name_to_url[asset_name] = phase2_res[i]["result_url"]

            for i, ref_form_name in derived_indices:
                asset = assets[i]
                name = asset.get("name", "unknown")
                prompt = asset.get("prompt", "")
                if not prompt:
                    _update_project_result(project_id, 2, "phase2", i, {
                        "name": name, "status": "skipped", "reason": "无prompt"
                    })
                    continue

                # Find reference image from primary form
                ref_images = []
                ref_url = name_to_url.get(ref_form_name)
                if ref_url:
                    ref_images.append(_to_absolute_url(ref_url))

                result = proxy.generate_image(prompt, image_model, ratio, image_resolution,
                                              reference_images=ref_images if ref_images else None)
                if "error" in result:
                    _update_project_result(project_id, 2, "phase2", i, {
                        "name": name, "status": "failed", "error": result["error"]
                    })
                    cost = _calc_image_cost(image_model, image_resolution)
                    add_points(uid, cost, f"资产生图提交失败退还-{name}")
                    continue

                oiioii_id = result.get("task_id", 0)
                cost = _calc_image_cost(image_model, image_resolution)
                af_id = create_task(uid, "image", image_model, prompt[:500], cost, oiioii_id)

                ref_imgs_str = json.dumps(ref_images) if ref_images else ""
                _update_project_result(project_id, 2, "phase2", i, {
                    "name": name, "status": "running", "oiioii_task_id": oiioii_id,
                    "aiforge_task_id": af_id, "prompt": prompt, "reference_images": ref_imgs_str
                })

                t = threading.Thread(
                    target=_poll_and_update_project,
                    args=(project_id, 2, oiioii_id, af_id, uid, cost, "phase2", i),
                    daemon=True
                )
                t.start()
                time.sleep(0.5)

    t = threading.Thread(target=_generate_assets, daemon=True)
    t.start()

    return {"status": "running", "phase": 2, "assets_count": len(assets), "cost": total_cost}


def _run_phase3(uid: int, project: dict, db):
    segments = json.loads(project.get("segments_json", "[]"))
    if not segments:
        db.close()
        raise HTTPException(400, "没有分镜数据，请先编辑分镜脚本")

    image_model = project["image_model"]
    image_resolution = project.get("image_resolution", "1K")
    total_cost = len(segments) * _calc_image_cost(image_model, image_resolution)

    if not deduct_points(uid, total_cost, f"一键成片-阶段3故事板生成({len(segments)}张)"):
        db.close()
        raise HTTPException(402, "积分不足")

    project_id = project["id"]

    results = json.loads(project.get("results_json", "{}"))
    results["phase3"] = [{"segment_id": s.get("id", i), "title": s.get("title", ""), "status": "pending"}
                         for i, s in enumerate(segments)]
    db.execute("UPDATE projects SET results_json=?, updated_at=? WHERE id=?",
               (json.dumps(results, ensure_ascii=False), time.time(), project_id))
    db.commit()
    db.close()

    def _generate_storyboards():
        for i, seg in enumerate(segments):
            sid = seg.get("id", i)
            title = seg.get("title", "")
            shots = seg.get("shots", [])

            # Build storyboard prompt with style and asset references
            script_data = json.loads(project.get("script", "{}"))
            style = script_data.get("style", "Photorealistic, cinematic")

            prompt_parts = [
                f"Professional film storyboard for segment: {title}",
                f"Style: {style}",
                "",
                "Layout: Vertical film storyboard strip, 9:16 ratio. Each shot is a separate panel arranged top-to-bottom.",
                "Each panel must show: exact composition, character positions, lighting, camera angle as described.",
                "Character appearances must match their reference images exactly.",
                "Scene atmosphere and lighting must match scene reference images.",
                "",
            ]

            for j, sh in enumerate(shots):
                time_range = sh.get("time", "")
                camera = sh.get("camera", "locked-off")
                visual = sh.get("visual", "")[:200]
                lighting = sh.get("lighting", "")
                dialogue = sh.get("dialogue", "")
                transition = sh.get("transition", "[cut]")

                panel_desc = f"Panel {j+1} ({time_range}): [{camera}] {visual}"
                if lighting:
                    panel_desc += f". Lighting: {lighting}"
                if dialogue:
                    panel_desc += f". Dialogue: {dialogue[:60]}"
                panel_desc += f" → {transition}"
                prompt_parts.append(panel_desc)

            prompt_parts.append("")
            prompt_parts.append("Photorealistic movie stills, cinematic composition, consistent character appearance across all panels. Clean professional storyboard layout.")
            prompt = "\n".join(prompt_parts)

            # Collect reference images from phase2 results for this segment's assets
            seg_asset_names = seg.get("assets", [])
            ref_images = []
            phase2_results = results.get("phase2", [])
            for r in phase2_results:
                if r.get("result_url") and r.get("name"):
                    # Only include assets referenced by this segment
                    if not seg_asset_names or r["name"] in seg_asset_names:
                        ref_images.append(_to_absolute_url(r["result_url"]))

            result = proxy.generate_image(prompt, image_model, ratio, project.get("image_resolution", "1K"),
                                          reference_images=ref_images[:3] if ref_images else None)
            if "error" in result:
                _update_project_result(project_id, 3, "phase3", i, {
                    "segment_id": sid, "status": "failed", "error": result["error"]
                })
                cost = _calc_image_cost(image_model, image_resolution)
                add_points(uid, cost, f"故事板提交失败退还-段{sid}")
                continue

            oiioii_id = result.get("task_id", 0)
            cost = _calc_image_cost(image_model, image_resolution)
            af_id = create_task(uid, "image", image_model, prompt[:500], cost, oiioii_id)

            ref_imgs_str = json.dumps(ref_images[:3]) if ref_images else ""
            _update_project_result(project_id, 3, "phase3", i, {
                "segment_id": sid, "status": "running", "oiioii_task_id": oiioii_id,
                "aiforge_task_id": af_id, "prompt": prompt, "reference_images": ref_imgs_str
            })

            t = threading.Thread(
                target=_poll_and_update_project,
                args=(project_id, 3, oiioii_id, af_id, uid, cost, "phase3", i),
                daemon=True
            )
            t.start()
            time.sleep(0.5)

    t = threading.Thread(target=_generate_storyboards, daemon=True)
    t.start()

    return {"status": "running", "phase": 3, "segments_count": len(segments), "cost": total_cost}


def _run_phase4(uid: int, project: dict, db):
    segments = json.loads(project.get("segments_json", "[]"))
    if not segments:
        db.close()
        raise HTTPException(400, "没有分镜数据，请先编辑分镜脚本")

    # 检查phase2资产是否全部完成（有失败的不能继续生成视频）
    results = json.loads(project.get("results_json", "{}"))
    phase2_results = results.get("phase2", [])
    assets = json.loads(project.get("assets_json", "[]"))
    failed_assets = [r for r in phase2_results if r.get("status") == "failed"]
    running_assets = [r for r in phase2_results if r.get("status") == "running"]
    pending_assets = [r for r in phase2_results if r.get("status") == "pending"]
    # 检查是否有资产还没有生成结果
    missing_assets = len(assets) - len(phase2_results)

    if failed_assets:
        failed_names = [r.get("name", "?") for r in failed_assets]
        db.close()
        raise HTTPException(400, f"有{len(failed_assets)}个资产生图失败（{', '.join(failed_names[:5])}），请先重试失败资产再生成视频")
    if running_assets or pending_assets or missing_assets > 0:
        db.close()
        raise HTTPException(400, f"资产生图尚未全部完成（生成中{len(running_assets)}，待生成{len(pending_assets) + missing_assets}），请等待资产图全部完成后再生成视频")

    video_model = project["video_model"]
    duration = project["duration"]
    resolution = project["resolution"]
    ratio = project["ratio"]
    total_cost = len(segments) * _calc_video_cost(video_model, duration, resolution)

    if not deduct_points(uid, total_cost, f"一键成片-阶段4视频生成({len(segments)}段)"):
        db.close()
        raise HTTPException(402, "积分不足")

    project_id = project["id"]

    results["phase4"] = [{"segment_id": s.get("id", i), "title": s.get("title", ""), "status": "pending"}
                         for i, s in enumerate(segments)]
    db.execute("UPDATE projects SET results_json=?, updated_at=? WHERE id=?",
               (json.dumps(results, ensure_ascii=False), time.time(), project_id))
    db.commit()
    db.close()

    # Pre-load phase2 results for reference images (convert to absolute URLs)
    phase2_results = results.get("phase2", [])

    def _generate_videos():
        script_data = json.loads(project.get("script", "{}"))
        style = script_data.get("style", "Photorealistic, cinematic")
        scene_map = script_data.get("scene_map", {})

        for i, seg in enumerate(segments):
            sid = seg.get("id", i)
            seg_assets = seg.get("assets", [])

            vp = _build_video_prompt(
                segment=seg, duration=duration, style=style,
                seg_asset_names=seg_assets, phase2_results=phase2_results,
                segment_index=i, scene_map=scene_map,
            )
            video_prompt = vp["prompt"]
            ref_images = vp["ref_images"]
            ref_map = vp["ref_map"]

            result = proxy.generate_video(
                prompt=video_prompt, model=video_model, ratio=ratio,
                resolution=resolution, duration=duration,
                reference_images=None if ("gemini" in video_model.lower() or "omni" in video_model.lower()) else (ref_images if ref_images else None),
                reference_map=None if ("gemini" in video_model.lower() or "omni" in video_model.lower()) else (ref_map if ref_map else None),
            )
            if "error" in result:
                _update_project_result(project_id, 4, "phase4", i, {
                    "segment_id": sid, "status": "failed", "error": result["error"]
                })
                cost = _calc_video_cost(video_model, duration, resolution)
                add_points(uid, cost, f"视频提交失败退还-段{sid}")
                continue

            oiioii_id = result.get("task_id", 0)
            cost = _calc_video_cost(video_model, duration, resolution)
            ref_imgs_str = json.dumps(ref_images[:3]) if ref_images else ""
            af_id = create_task(uid, "video", video_model, video_prompt[:500], cost, oiioii_id,
                               reference_images=ref_imgs_str)

            _update_project_result(project_id, 4, "phase4", i, {
                "segment_id": sid, "status": "running", "oiioii_task_id": oiioii_id,
                "aiforge_task_id": af_id, "prompt": video_prompt[:500], "reference_images": ref_imgs_str
            })

            t = threading.Thread(
                target=_poll_and_update_project,
                args=(project_id, 4, oiioii_id, af_id, uid, cost, "phase4", i),
                daemon=True
            )
            t.start()
            time.sleep(1)

    t = threading.Thread(target=_generate_videos, daemon=True)
    t.start()

    return {"status": "running", "phase": 4, "segments_count": len(segments), "cost": total_cost}


# ==================== Single Asset / Segment Operations ====================

@router.post("/{project_id}/asset/{asset_index}/reference")
def upload_asset_reference(project_id: int, asset_index: int, req: AssetRefReq, user: dict = Depends(auth_required)):
    """上传资产参考图。前端先上传图片到oiioii拿到URL，再传过来保存到assets_json中对应资产的reference_image字段。"""
    db = _get_conn()
    r = db.execute("SELECT assets_json FROM projects WHERE id=? AND user_id=?", (project_id, user["id"])).fetchone()
    if not r:
        db.close()
        raise HTTPException(404, "项目不存在")
    assets = json.loads(r["assets_json"] if r["assets_json"] else "[]")
    if asset_index < 0 or asset_index >= len(assets):
        db.close()
        raise HTTPException(400, "资产索引越界")
    assets[asset_index]["reference_image"] = req.image_url
    db.execute("UPDATE projects SET assets_json=?, updated_at=? WHERE id=?",
               (json.dumps(assets, ensure_ascii=False), time.time(), project_id))
    db.commit()
    db.close()
    return {"status": "ok", "asset_index": asset_index, "reference_image": req.image_url}


@router.post("/{project_id}/asset/{asset_index}/generate")
def generate_single_asset(project_id: int, asset_index: int, user: dict = Depends(auth_required)):
    """单独生成某个资产的图片。读取该资产的prompt和reference_image，调用oiioii生图。"""
    project = _get_project_data(project_id, user["id"])
    assets = json.loads(project.get("assets_json", "[]"))
    if asset_index < 0 or asset_index >= len(assets):
        raise HTTPException(400, "资产索引越界")

    asset = assets[asset_index]
    prompt = asset.get("prompt", "")
    if not prompt:
        raise HTTPException(400, "该资产没有prompt")

    image_model = project["image_model"]
    image_resolution = project.get("image_resolution", "1K")
    cost = _calc_image_cost(image_model, image_resolution)

    if not deduct_points(user["id"], cost, f"资产生图-{asset.get('name', asset_index)}"):
        raise HTTPException(402, "积分不足")

    # 收集参考图
    ref_images = []
    if asset.get("reference_image"):
        ref_images.append(_to_absolute_url(asset["reference_image"]))

    ratio = project.get("ratio", "16:9")
    result = proxy.generate_image(
        prompt=prompt, model=image_model, ratio=ratio,
        resolution=image_resolution, reference_images=ref_images if ref_images else None
    )

    if "error" in result:
        add_points(user["id"], cost, f"资产生图失败退还-{asset_index}")
        raise HTTPException(500, result["error"])

    oiioii_id = result.get("task_id", 0)
    af_id = create_task(user["id"], "image", image_model, prompt[:500], cost, oiioii_id,
                        reference_images=json.dumps(ref_images) if ref_images else "")

    # 更新results_json中phase2对应项
    db = _get_conn()
    row = db.execute("SELECT results_json FROM projects WHERE id=?", (project_id,)).fetchone()
    results = json.loads(row["results_json"]) if row and row["results_json"] else {}
    phase2 = results.get("phase2", [])
    # 确保phase2有足够的项
    while len(phase2) <= asset_index:
        phase2.append({"status": "pending", "name": "", "prompt": ""})
    phase2[asset_index] = {
        "name": asset.get("name", ""),
        "status": "running",
        "oiioii_task_id": oiioii_id,
        "aiforge_task_id": af_id,
        "prompt": prompt,
        "reference_images": json.dumps(ref_images) if ref_images else ""
    }
    results["phase2"] = phase2
    db.execute("UPDATE projects SET results_json=?, updated_at=? WHERE id=?",
               (json.dumps(results, ensure_ascii=False), time.time(), project_id))
    db.commit()
    db.close()

    # 启动轮询线程
    t = threading.Thread(
        target=_poll_and_update_project,
        args=(project_id, 2, oiioii_id, af_id, user["id"], cost, "phase2", asset_index),
        daemon=True
    )
    t.start()

    return {"status": "running", "asset_index": asset_index, "cost": cost}


@router.post("/{project_id}/segment/{seg_index}/generate-storyboard")
def generate_single_storyboard(project_id: int, seg_index: int, user: dict = Depends(auth_required)):
    """单独生成某段的故事板图。"""
    project = _get_project_data(project_id, user["id"])
    segments = json.loads(project.get("segments_json", "[]"))
    if seg_index < 0 or seg_index >= len(segments):
        raise HTTPException(400, "段索引越界")

    seg = segments[seg_index]
    # 构建prompt：从段的shots中提取视觉描述
    shots = seg.get("shots", [])
    prompt_parts = []
    for sh in shots:
        if sh.get("visual"):
            prompt_parts.append(sh["visual"])
        if sh.get("camera"):
            prompt_parts.append(f"Camera: {sh['camera']}")
    prompt = ". ".join(prompt_parts) if prompt_parts else seg.get("title", "storyboard")

    image_model = project["image_model"]
    image_resolution = project.get("image_resolution", "1K")
    cost = _calc_image_cost(image_model, image_resolution)

    if not deduct_points(user["id"], cost, f"故事板生图-段{seg_index}"):
        raise HTTPException(402, "积分不足")

    # 收集参考图：从phase2结果中取
    results = json.loads(project.get("results_json", "{}"))
    ref_images = []
    for r in results.get("phase2", []):
        if r.get("result_url"):
            ref_images.append(_to_absolute_url(r["result_url"]))

    result = proxy.generate_image(
        prompt=prompt, model=image_model, ratio="9:16",
        resolution=image_resolution, reference_images=ref_images[:3] if ref_images else None
    )

    if "error" in result:
        add_points(user["id"], cost, f"故事板生图失败退还-段{seg_index}")
        raise HTTPException(500, result["error"])

    oiioii_id = result.get("task_id", 0)
    af_id = create_task(user["id"], "image", image_model, prompt[:500], cost, oiioii_id,
                        reference_images=json.dumps(ref_images[:3]) if ref_images else "")

    # 更新results_json中phase3对应项
    db = _get_conn()
    row = db.execute("SELECT results_json FROM projects WHERE id=?", (project_id,)).fetchone()
    results = json.loads(row["results_json"]) if row and row["results_json"] else {}
    phase3 = results.get("phase3", [])
    while len(phase3) <= seg_index:
        phase3.append({"status": "pending", "title": "", "prompt": ""})
    phase3[seg_index] = {
        "title": seg.get("title", ""),
        "status": "running",
        "oiioii_task_id": oiioii_id,
        "aiforge_task_id": af_id,
        "prompt": prompt,
        "reference_images": json.dumps(ref_images[:3]) if ref_images else ""
    }
    results["phase3"] = phase3
    db.execute("UPDATE projects SET results_json=?, updated_at=? WHERE id=?",
               (json.dumps(results, ensure_ascii=False), time.time(), project_id))
    db.commit()
    db.close()

    t = threading.Thread(
        target=_poll_and_update_project,
        args=(project_id, 3, oiioii_id, af_id, user["id"], cost, "phase3", seg_index),
        daemon=True
    )
    t.start()

    return {"status": "running", "seg_index": seg_index, "cost": cost}


@router.post("/{project_id}/segment/{seg_index}/generate-video")
def generate_single_video(project_id: int, seg_index: int, req: VideoGenReq, user: dict = Depends(auth_required)):
    """单独生成某段的视频，支持自定义prompt。"""
    project = _get_project_data(project_id, user["id"])
    segments = json.loads(project.get("segments_json", "[]"))
    if seg_index < 0 or seg_index >= len(segments):
        raise HTTPException(400, "段索引越界")

    seg = segments[seg_index]
    video_model = project["video_model"]
    duration = project["duration"]
    resolution = project["resolution"]
    ratio = project["ratio"]
    cost = _calc_video_cost(video_model, duration, resolution)

    if not deduct_points(user["id"], cost, f"视频生成-段{seg_index}"):
        raise HTTPException(402, "积分不足")

    # 构建prompt
    video_prompt = None
    decomposed_result = None
    if req.prompt:
        video_prompt = req.prompt
        ref_images = []
        results = json.loads(project.get("results_json", "{}"))
        for r in results.get("phase2", []):
            if r.get("result_url"):
                ref_images.append(_to_absolute_url(r["result_url"]))
        ref_map = None
    else:
        script_data = json.loads(project.get("script", "{}"))
        style = script_data.get("style", "Photorealistic, cinematic")
        scene_map = script_data.get("scene_map", {})
        characters = script_data.get("characters", None)

        results = json.loads(project.get("results_json", "{}"))
        phase2_results = results.get("phase2", [])
        seg_assets = seg.get("assets", [])

        # Get user's LLM config for decomposer if enabled
        llm_config = None
        if req.use_decomposer:
            llm_config = _get_user_llm(user["id"]) or None

        vp = _build_video_prompt(
            segment=seg, duration=duration, style=style,
            seg_asset_names=seg_assets, phase2_results=phase2_results,
            segment_index=seg_index, scene_map=scene_map,
            use_decomposer=req.use_decomposer,
            characters=characters,
            llm_config=llm_config,
        )
        video_prompt = vp["prompt"]
        ref_images = vp["ref_images"]
        ref_map = vp["ref_map"]
        decomposed_result = vp.get("decomposed")

    # Gemini Omni doesn't support reference images well - skip them for this model
    # User-specified reference_images take priority over auto-matched ones
    if req.reference_images:
        ref_images = [_to_absolute_url(u) for u in req.reference_images if u]
        ref_map = None  # user-specified refs don't need a map
    use_ref_images = ref_images if ref_images else None
    use_ref_map = ref_map if ref_map else None
    if "gemini" in video_model.lower() or "omni" in video_model.lower():
        use_ref_images = None
        use_ref_map = None

    result = proxy.generate_video(
        prompt=video_prompt, model=video_model, ratio=ratio,
        resolution=resolution, duration=duration,
        reference_images=use_ref_images,
        reference_map=use_ref_map,
    )

    if "error" in result:
        add_points(user["id"], cost, f"视频生成失败退还-段{seg_index}")
        raise HTTPException(500, result["error"])

    oiioii_id = result.get("task_id", 0)
    ref_imgs_str = json.dumps(ref_images[:3]) if ref_images else ""
    af_id = create_task(user["id"], "video", video_model, video_prompt[:500], cost, oiioii_id,
                        reference_images=ref_imgs_str)

    # 更新results_json中phase4对应项
    db = _get_conn()
    row = db.execute("SELECT results_json FROM projects WHERE id=?", (project_id,)).fetchone()
    results = json.loads(row["results_json"]) if row and row["results_json"] else {}
    phase4 = results.get("phase4", [])
    while len(phase4) <= seg_index:
        phase4.append({"status": "pending", "title": "", "prompt": ""})
    phase4[seg_index] = {
        "segment_id": seg.get("id", seg_index),
        "title": seg.get("title", ""),
        "status": "running",
        "oiioii_task_id": oiioii_id,
        "aiforge_task_id": af_id,
        "prompt": video_prompt[:500],
        "reference_images": ref_imgs_str,
        "decomposed": decomposed_result,
    }
    results["phase4"] = phase4
    db.execute("UPDATE projects SET results_json=?, updated_at=? WHERE id=?",
               (json.dumps(results, ensure_ascii=False), time.time(), project_id))
    db.commit()
    db.close()

    t = threading.Thread(
        target=_poll_and_update_project,
        args=(project_id, 4, oiioii_id, af_id, user["id"], cost, "phase4", seg_index),
        daemon=True
    )
    t.start()

    return {"status": "running", "seg_index": seg_index, "cost": cost}


@router.post("/{project_id}/asset/{asset_index}/upload-result")
def upload_asset_result(project_id: int, asset_index: int, req: AssetUploadReq, user: dict = Depends(auth_required)):
    """直接上传图片URL作为资产结果（不用AI生成）。"""
    db = _get_conn()
    r = db.execute("SELECT assets_json, results_json FROM projects WHERE id=? AND user_id=?",
                   (project_id, user["id"])).fetchone()
    if not r:
        db.close()
        raise HTTPException(404, "项目不存在")
    assets = json.loads(r["assets_json"] if r["assets_json"] else "[]")
    if asset_index < 0 or asset_index >= len(assets):
        db.close()
        raise HTTPException(400, "资产索引越界")

    results = json.loads(r["results_json"]) if r["results_json"] else {}
    phase2 = results.get("phase2", [])
    while len(phase2) <= asset_index:
        phase2.append({"status": "pending", "name": "", "prompt": ""})
    phase2[asset_index] = {
        "name": assets[asset_index].get("name", ""),
        "status": "completed",
        "result_url": req.image_url,
        "prompt": "用户上传"
    }
    results["phase2"] = phase2
    db.execute("UPDATE projects SET results_json=?, updated_at=? WHERE id=?",
               (json.dumps(results, ensure_ascii=False), time.time(), project_id))
    db.commit()
    db.close()
    return {"status": "ok", "asset_index": asset_index, "result_url": req.image_url}


@router.delete("/{project_id}/asset/{asset_index}")
def delete_asset(project_id: int, asset_index: int, user: dict = Depends(auth_required)):
    """删除指定索引的资产，并更新results_json。"""
    db = _get_conn()
    r = db.execute("SELECT assets_json, script, results_json FROM projects WHERE id=? AND user_id=?",
                   (project_id, user["id"])).fetchone()
    if not r:
        db.close()
        raise HTTPException(404, "项目不存在")

    assets = json.loads(r["assets_json"] if r["assets_json"] else "[]")
    if asset_index < 0 or asset_index >= len(assets):
        db.close()
        raise HTTPException(400, "资产索引越界")

    removed = assets.pop(asset_index)

    # Update results_json — remove the corresponding phase2 result
    results = json.loads(r["results_json"]) if r["results_json"] else {}
    phase2 = results.get("phase2", [])
    if asset_index < len(phase2):
        phase2.pop(asset_index)
    results["phase2"] = phase2

    # Update script JSON
    try:
        script_data = json.loads(r["script"])
        script_data["assets"] = assets
    except (json.JSONDecodeError, TypeError):
        script_data = {"assets": assets, "segments": []}

    db.execute("""
        UPDATE projects SET script=?, assets_json=?, results_json=?, updated_at=?
        WHERE id=? AND user_id=?
    """, (json.dumps(script_data, ensure_ascii=False),
          json.dumps(assets, ensure_ascii=False),
          json.dumps(results, ensure_ascii=False), time.time(),
          project_id, user["id"]))
    db.commit()
    db.close()
    return {"ok": True, "removed": removed.get("name", "?"), "assets_count": len(assets)}


@router.delete("/{project_id}/segment/{seg_index}")
def delete_segment(project_id: int, seg_index: int, user: dict = Depends(auth_required)):
    """删除指定索引的分镜段，并更新results_json。"""
    db = _get_conn()
    r = db.execute("SELECT segments_json, script, results_json FROM projects WHERE id=? AND user_id=?",
                   (project_id, user["id"])).fetchone()
    if not r:
        db.close()
        raise HTTPException(404, "项目不存在")

    segments = json.loads(r["segments_json"] if r["segments_json"] else "[]")
    if seg_index < 0 or seg_index >= len(segments):
        db.close()
        raise HTTPException(400, "段索引越界")

    removed = segments.pop(seg_index)

    # Update results_json — remove the corresponding phase3 and phase4 results
    results = json.loads(r["results_json"]) if r["results_json"] else {}
    phase3 = results.get("phase3", [])
    if seg_index < len(phase3):
        phase3.pop(seg_index)
    results["phase3"] = phase3
    phase4 = results.get("phase4", [])
    if seg_index < len(phase4):
        phase4.pop(seg_index)
    results["phase4"] = phase4

    # Update script JSON
    try:
        script_data = json.loads(r["script"])
        script_data["segments"] = segments
    except (json.JSONDecodeError, TypeError):
        script_data = {"assets": [], "segments": segments}

    db.execute("""
        UPDATE projects SET script=?, segments_json=?, results_json=?, updated_at=?
        WHERE id=? AND user_id=?
    """, (json.dumps(script_data, ensure_ascii=False),
          json.dumps(segments, ensure_ascii=False),
          json.dumps(results, ensure_ascii=False), time.time(),
          project_id, user["id"]))
    db.commit()
    db.close()
    return {"ok": True, "removed": removed.get("title", "?"), "segments_count": len(segments)}
