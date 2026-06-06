import os
import json
import threading
import time
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from fastapi.responses import StreamingResponse, FileResponse, Response
from pydantic import BaseModel
from api.auth import auth_required
from models.db import deduct_points, create_task, update_task, get_user_tasks, get_user
from core.proxy import OiioiiProxy
from config import OIIOII_API, DATA_DIR

router = APIRouter(prefix="/api/gen", tags=["generate"])
proxy = OiioiiProxy(OIIOII_API)

_task_callbacks = {}


class ImageReq(BaseModel):
    prompt: str
    model: str = "Flux Dev"
    ratio: str = "1:1"
    resolution: str = "1K"
    reference_images: list = []


class VideoReq(BaseModel):
    prompt: str
    model: str = "Vidu Q2"
    ratio: str = "16:9"
    resolution: str = "720p"
    duration: int = 5
    reference_images: list = []
    reference_video: str = ""
    camera_movement: str = ""


def _calc_image_cost(model: str, resolution: str) -> int:
    """Calculate image cost - custom pricing overrides oiioii cost_base."""
    # Custom pricing (not using oiioii cost_base)
    IMAGE_COST_OVERRIDES = {
        "GPT-Image2": {"1K": 4, "2K": 8, "4K": 12},
        "Gpt 4o":     {"1K": 5, "2K": 10, "4K": 20},
    }
    DEFAULT = {"1K": 5, "2K": 10, "4K": 20}
    pricing = IMAGE_COST_OVERRIDES.get(model, DEFAULT)
    if resolution in ("4K", "4k"):
        return pricing["4K"]
    if resolution in ("2K", "1080p"):
        return pricing["2K"]
    return pricing["1K"]


def _calc_video_cost(model: str, duration: int, resolution: str) -> int:
    """Calculate video cost in points (100 points = 1 RMB).
    
    Pricing based on RMB per 10s at 720p, then linear scale by duration and resolution.
    Resolution ratios: 720p=1.0, 1080p=1.29, 4K=2.14 (derived from Gemini Omni pricing).
    """
    # Price per 10s at 720p in RMB, then * 100 = points
    # Grok Imagine: 0.4, Gemini Omni: 0.7, Wan2.7: 0.6
    # Others: proportional to oiioii cost_base (Gemini base=25 → 0.7 RMB)
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
            base_price = 0.7 * (cost_base / 25)  # Proportional to Gemini (base=25 → 0.7 RMB)
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

    # RMB → points (× 100)
    cost_rmb = base_price * duration_scale * res_scale
    return max(1, int(round(cost_rmb * 100)))
def _poll_oiioii(task_id: int, aiforge_task_id: int, uid: int, cost: int):
    from models.db import add_points
    start = time.time()
    max_wait = 1800  # 30 min timeout
    print(f"[Poll] #{aiforge_task_id} OiioiiPool #{task_id}: started, max_wait={max_wait}s")
    try:
        while time.time() - start < max_wait:
            try:
                result = proxy.get_task(task_id)
            except Exception as e:
                print(f"[Poll] #{aiforge_task_id}: proxy.get_task exception: {e}, retrying...")
                time.sleep(10)
                continue

            status = result.get("status", "")
            elapsed = int(time.time() - start)
            if status == "completed":
                file_url = f"/api/gen/file/{task_id}"
                update_task(aiforge_task_id, "completed", file_url)
                print(f"[Poll] #{aiforge_task_id}: completed after {elapsed}s")
                return
            elif status == "failed":
                error_msg = result.get("error", result.get("message", "未知错误"))
                update_task(aiforge_task_id, "failed", "", error=error_msg)
                add_points(uid, cost, f"任务失败退还-#{aiforge_task_id}")
                print(f"[Poll] #{aiforge_task_id}: failed after {elapsed}s, error={error_msg[:80]}")
                return
            elif result.get("error"):
                print(f"[Poll] #{aiforge_task_id}: has error but still processing: {result['error'][:50]}, retrying...")
                time.sleep(5)
                continue
            if elapsed % 60 == 0:
                print(f"[Poll] #{aiforge_task_id}: still {status} after {elapsed}s")
            time.sleep(5)
        # Timeout
        print(f"[Poll] #{aiforge_task_id}: timeout after {max_wait}s")
        update_task(aiforge_task_id, "timeout", "", error=f"任务超时({max_wait}s)，积分已退还")
        add_points(uid, cost, f"任务超时退还-#{aiforge_task_id}")
    except Exception as e:
        # Catch-all: if poll thread crashes, still mark as failed and refund
        print(f"[Poll] #{aiforge_task_id}: CRASHED with exception: {e}")
        try:
            update_task(aiforge_task_id, "failed", "", error=f"内部错误，积分已退还")
            add_points(uid, cost, f"内部错误退还-#{aiforge_task_id}")
        except:
            print(f"[Poll] #{aiforge_task_id}: CRITICAL - failed to refund after crash!")


@router.get("/models")
def get_models():
    return proxy.get_models()


@router.post("/image")
def generate_image(req: ImageReq, user: dict = Depends(auth_required)):
    cost = _calc_image_cost(req.model, req.resolution)
    if not deduct_points(user["id"], cost, f"生成图片-{req.model}"):
        raise HTTPException(402, "积分不足")
    result = proxy.generate_image(req.prompt, req.model, req.ratio, req.resolution, req.reference_images)
    if "error" in result:
        from models.db import add_points
        add_points(user["id"], cost, f"提交失败退还-{req.model}")
        raise HTTPException(500, result["error"])
    oiioii_id = result.get("task_id", 0)
    ref_imgs = json.dumps(req.reference_images) if req.reference_images else ""
    af_id = create_task(user["id"], "image", req.model, req.prompt, cost, oiioii_id, reference_images=ref_imgs)
    t = threading.Thread(target=_poll_oiioii, args=(oiioii_id, af_id, user["id"], cost), daemon=True)
    t.start()
    return {"task_id": af_id, "oiioii_task_id": oiioii_id, "cost": cost, "status": "running"}


@router.post("/video")
def generate_video(req: VideoReq, user: dict = Depends(auth_required)):
    cost = _calc_video_cost(req.model, req.duration, req.resolution)
    if not deduct_points(user["id"], cost, f"生成视频-{req.model}"):
        raise HTTPException(402, "积分不足")
    result = proxy.generate_video(req.prompt, req.model, req.ratio, req.resolution,
                                  req.duration, req.reference_images, req.reference_video,
                                  req.camera_movement)
    if "error" in result:
        from models.db import add_points
        add_points(user["id"], cost, f"提交失败退还-{req.model}")
        raise HTTPException(500, result["error"])
    oiioii_id = result.get("task_id", 0)
    ref_imgs = json.dumps(req.reference_images) if req.reference_images else ""
    ref_vid = req.reference_video or ""
    af_id = create_task(user["id"], "video", req.model, req.prompt, cost, oiioii_id, reference_images=ref_imgs, reference_video=ref_vid)
    t = threading.Thread(target=_poll_oiioii, args=(oiioii_id, af_id, user["id"], cost), daemon=True)
    t.start()
    return {"task_id": af_id, "oiioii_task_id": oiioii_id, "cost": cost, "status": "running"}


@router.get("/task/{task_id}")
def get_task(task_id: int, user: dict = Depends(auth_required)):
    from models.db import _get_conn, add_points
    conn = _get_conn()
    row = conn.execute("SELECT * FROM tasks WHERE id=? AND user_id=?", (task_id, user["id"])).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "任务不存在")
    # If task timed out but OiioiiPool might have completed, re-check
    if row["status"] in ("timeout", "running") and row["oiioii_task_id"]:
        oid = row["oiioii_task_id"]
        conn.close()
        result = proxy.get_task(oid)
        if not result.get("error"):
            pool_status = result.get("status", "")
            if pool_status == "completed":
                file_url = f"/api/gen/file/{oid}"
                update_task(task_id, "completed", file_url)
                print(f"[RePoll] #{task_id} OiioiiPool #{oid}: recovered -> completed!")
                conn2 = _get_conn()
                updated = conn2.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
                conn2.close()
                return dict(updated)
            elif pool_status == "failed":
                error_msg = result.get("error", result.get("message", ""))
                update_task(task_id, "failed", "", error=error_msg)
                add_points(user["id"], row["points_cost"], f"任务失败退还-#{task_id}")
        return dict(row)
    conn.close()
    return dict(row)


@router.get("/tasks")
def list_tasks(user: dict = Depends(auth_required), limit: int = 50):
    return get_user_tasks(user["id"], limit)


@router.delete("/task/{task_id}")
def delete_task(task_id: int, user: dict = Depends(auth_required)):
    from models.db import _get_conn
    conn = _get_conn()
    row = conn.execute("SELECT id, status, points_cost FROM tasks WHERE id=? AND user_id=?", (task_id, user["id"])).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "任务不存在")
    if row["status"] == "running":
        conn.close()
        raise HTTPException(400, "运行中的任务不能删除")
    conn.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (task_id, user["id"]))
    conn.commit()
    conn.close()
    return {"ok": True}



@router.post("/task/{task_id}/retry")
def retry_task(task_id: int, user: dict = Depends(auth_required)):
    """Retry a failed/timeout task by re-submitting to oiioii with same params."""
    from models.db import _get_conn
    conn = _get_conn()
    row = conn.execute("SELECT * FROM tasks WHERE id=? AND user_id=?", (task_id, user["id"])).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "任务不存在")
    if row["status"] not in ("failed", "timeout", "completed"):
        raise HTTPException(400, "运行中的任务不能重试")

    # Re-submit to oiioii
    ref_imgs = []
    if row["reference_images"]:
        try:
            ref_imgs = json.loads(row["reference_images"])
        except:
            pass

    # Safely get optional columns that may not exist in older rows
    def _row_get(key, default=''):
        try:
            return row[key]
        except (IndexError, KeyError):
            return default

    if row["task_type"] == "image":
        result = proxy.generate_image(row["prompt"], row["model"], _row_get("ratio") or "1:1", _row_get("resolution") or "1K", ref_imgs)
    else:
        ref_vid = _row_get("reference_video") or ""
        result = proxy.generate_video(row["prompt"], row["model"], _row_get("ratio") or "16:9", _row_get("resolution") or "720p", _row_get("duration") or 5, ref_imgs, ref_vid)

    if "error" in result:
        raise HTTPException(500, result["error"])

    oiioii_id = result.get("task_id", 0)
    # Deduct points for retry
    cost = row["points_cost"]
    if not deduct_points(user["id"], cost, f"重试任务-#{task_id}"):
        raise HTTPException(402, "积分不足")

    # Update existing task
    from models.db import _get_conn as _get_conn2
    conn2 = _get_conn2()
    now = time.time()
    conn2.execute(
        "UPDATE tasks SET status='running', oiioii_task_id=?, result_url='', error='', created_at=?, finished_at=NULL WHERE id=?",
        (oiioii_id, now, task_id)
    )
    conn2.commit()
    conn2.close()

    t = threading.Thread(target=_poll_oiioii, args=(oiioii_id, task_id, user["id"], cost), daemon=True)
    t.start()
    return {"task_id": task_id, "oiioii_task_id": oiioii_id, "cost": cost, "status": "running"}


class DescribeReq(BaseModel):
    image_url: str


@router.post("/describe")
def describe_image(req: DescribeReq, user: dict = Depends(auth_required)):
    """Reverse prompt from image using oiioii's describe_image MCP method."""
    cost = 2  # Cheap operation
    if not deduct_points(user["id"], cost, "反推提示词"):
        raise HTTPException(402, "积分不足")
    result = proxy.describe_image(req.image_url)
    if "error" in result:
        from models.db import add_points
        add_points(user["id"], cost, "反推提示词失败退还")
        raise HTTPException(500, result["error"])
    oiioii_id = result.get("task_id", 0)
    af_id = create_task(user["id"], "image", "describe_image", req.image_url, cost, oiioii_id)
    t = threading.Thread(target=_poll_oiioii, args=(oiioii_id, af_id, user["id"], cost), daemon=True)
    t.start()
    return {"task_id": af_id, "oiioii_task_id": oiioii_id, "cost": cost, "status": "running"}


REFS_DIR = "/home/ubuntu/oiioii/data/output/refs"

def _verify_token_query(token: str) -> dict:
    """Verify JWT token from query param (for file URLs in img/video tags)."""
    import jwt as _jwt
    from config import SECRET_KEY, JWT_ALGORITHM
    if not token:
        raise HTTPException(401, "not logged in")
    try:
        payload = _jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except _jwt.ExpiredSignatureError:
        raise HTTPException(401, "token expired")
    except _jwt.InvalidTokenError:
        raise HTTPException(401, "invalid token")
    uid = payload.get("uid")
    user = get_user(uid)
    if not user:
        raise HTTPException(401, "user not found")
    return user



@router.get("/refs/{filename}")
def serve_ref(filename: str, token: str = ""):
    if token:
        _verify_token_query(token)
    fpath = os.path.join(REFS_DIR, filename)
    if not os.path.isfile(fpath):
        raise HTTPException(404, "File not found")
    ext = os.path.splitext(filename)[1].lower()
    media_map = {".mp4": "video/mp4", ".webm": "video/webm", ".png": "image/png",
                 ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif"}
    resp = FileResponse(fpath, media_type=media_map.get(ext, "video/mp4"))
    resp.headers["Cache-Control"] = "private, max-age=86400"
    return resp


@router.post("/upload_ref")
async def upload_ref(file: UploadFile = File(...), user: dict = Depends(auth_required)):
    content = await file.read()
    result = proxy.upload_ref(content, file.filename or "img.png")
    if "error" in result:
        raise HTTPException(500, result["error"])
    return result


@router.post("/upload_video_ref")
async def upload_video_ref(file: UploadFile = File(...), user: dict = Depends(auth_required)):
    content = await file.read()
    result = proxy.upload_video_ref(content, file.filename or "video.mp4")
    if "error" in result:
        raise HTTPException(500, result["error"])
    return result


@router.get("/file/{oiioii_task_id}")
def proxy_file(oiioii_task_id: int, request: Request, token: str = ""):
    if token:
        _verify_token_query(token)
    import requests as req

    # Step 1: Get the file's local path from OiioiiPool
    try:
        r = req.get(f"{OIIOII_API}/api/task/{oiioii_task_id}", timeout=10)
        if r.status_code != 200:
            raise HTTPException(502, "上游文件查询失败")
        pool_data = r.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"上游文件查询失败: {e}")

    local_path = pool_data.get("local_path", "")
    task_type = pool_data.get("type", "")
    is_video = task_type == "video"

    # Step 2: Serve file directly from disk (supports Range requests natively)
    if local_path and os.path.isfile(local_path):
        ext = os.path.splitext(local_path)[1].lower()
        media_map = {".mp4": "video/mp4", ".webm": "video/webm", ".png": "image/png",
                     ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif"}
        media_type = media_map.get(ext, "video/mp4" if is_video else "image/png")
        resp = FileResponse(local_path, media_type=media_type)
        resp.headers["Cache-Control"] = "private, max-age=86400"
        return resp

    # Step 3: Fallback to streaming proxy
    try:
        r = req.get(f"{OIIOII_API}/api/task/{oiioii_task_id}/download", stream=True, timeout=60)
        if r.status_code != 200:
            raise HTTPException(502, "上游文件获取失败")
        content_type = r.headers.get("content-type", "video/mp4" if is_video else "image/png")
        resp = StreamingResponse(r.iter_content(chunk_size=65536), media_type=content_type)
        resp.headers["Cache-Control"] = "private, max-age=86400"
        return resp
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"文件代理失败: {e}")
