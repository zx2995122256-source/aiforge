import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional
from core.db import init_db, TaskDB, AccountDB
from core.pool import AccountPool
from core.engine import GenEngine
from config import (IMAGE_MODELS, VIDEO_MODELS_DIRECT,
                    API_PORT, API_HOST, BASE_DIR, OUTPUT_DIR, REFS_DIR, LOGS_DIR,
                    VIDEO_MIN_POINTS)
from core.models_cache import init as init_models_cache, get_models as get_cached_models
from api.api_db import init_api_tables
from api.api_routes import router as api_router, set_engine as set_api_engine

app = FastAPI(title="夏夜专属API", version="3.0.0")
app.include_router(api_router)

# 静态文件
from fastapi.staticfiles import StaticFiles
import os as _os
_static_dir = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "static")
if _os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

pool: Optional[AccountPool] = None
engine: Optional[GenEngine] = None
_reg_jobs: dict = {}
_continuous_reg_running = False
_continuous_reg_thread = None
_public_url = ""


def set_public_url(url: str):
    global _public_url
    _public_url = url
    print(f"[Server] Public URL set to: {url}")


def init():
    global pool, engine
    init_db()
    init_api_tables()
    pool = AccountPool()
    engine = GenEngine(pool)
    engine.cleanup_stale_tasks()
    set_api_engine(engine)
    init_models_cache()


class ImageRequest(BaseModel):
    prompt: str
    model: str = "GPT-Image2"
    ratio: str = "16:9"
    resolution: str = "2K"
    reference_images: list = []


class VideoRequest(BaseModel):
    prompt: str
    model: str = "Vidu Q2"
    ratio: str = "16:9"
    resolution: str = "720p"
    duration: int = 5
    reference_images: list = []
    reference_video: str = ""
    reference_map: dict = None


class AddAccountRequest(BaseModel):
    email: str
    password: str


@app.on_event("startup")
def startup():
    init()


@app.get("/")
def index():
    html_path = os.path.join(BASE_DIR, "frontend", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Frontend not found</h1>")


@app.get("/output/{file_path:path}")
def serve_output(file_path: str):
    full_path = os.path.join(OUTPUT_DIR, file_path)
    if os.path.exists(full_path):
        return FileResponse(full_path)
    if os.path.isdir(OUTPUT_DIR):
        for entry in sorted(os.listdir(OUTPUT_DIR), reverse=True):
            sub = os.path.join(OUTPUT_DIR, entry, file_path)
            if os.path.exists(sub):
                return FileResponse(sub)
    raise HTTPException(404, "File not found")


@app.post("/api/upload_ref")
async def upload_reference(file: UploadFile = File(...)):
    os.makedirs(REFS_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "img.png")[1] or ".png"
    fname = f"ref_{int(time.time())}_{hash(file.filename) % 10000}{ext}"
    fpath = os.path.join(REFS_DIR, fname)
    content = await file.read()
    with open(fpath, "wb") as f:
        f.write(content)
    if _public_url:
        url = f"{_public_url}/output/refs/{fname}"
    else:
        url = f"/output/refs/{fname}"
    return {"url": url, "filename": fname}


@app.post("/api/upload_video_ref")
async def upload_video_reference(file: UploadFile = File(...)):
    content = await file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(400, "Video file too large (max 100MB)")
    ext = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
    fname = f"vidref_{int(time.time())}_{hash(file.filename) % 10000}{ext}"
    fpath = os.path.join(REFS_DIR, fname)
    os.makedirs(REFS_DIR, exist_ok=True)
    with open(fpath, "wb") as f:
        f.write(content)
    if _public_url:
        url = f"{_public_url}/output/refs/{fname}"
    else:
        url = f"/output/refs/{fname}"
    print(f"[Upload] video ref saved: {fpath} ({len(content)} bytes) -> {url}")
    return {"uri": url, "filename": fname}


@app.post("/api/generate_image")
def generate_image(req: ImageRequest):
    # 不区分大小写+去连字符匹配模型名（兼容 gpt-image-2 ↔ GPT-Image2）
    model_normalized = req.model.lower().replace("-", "")
    match = next((k for k in IMAGE_MODELS if k.lower().replace("-", "") == model_normalized), None)
    if not match:
        raise HTTPException(400, f"Unknown model: {req.model}. Available: {list(IMAGE_MODELS.keys())}")
    result = engine.submit("image", match, req.prompt, req.ratio, req.resolution,
                           reference_images=req.reference_images)
    if not result["success"]:
        raise HTTPException(500, result["error"])
    return {"task_id": result["task_db_id"], "status": "submitted"}


@app.post("/api/generate_video")
def generate_video(req: VideoRequest):
    model_normalized = req.model.lower().replace("-", "")
    match = next((k for k in VIDEO_MODELS_DIRECT if k.lower().replace("-", "") == model_normalized), None)
    if not match:
        raise HTTPException(400, f"Model not available: {req.model}. Available: {list(VIDEO_MODELS_DIRECT.keys())}")
    result = engine.submit(
        "video", match, req.prompt, req.ratio, req.resolution, req.duration,
        reference_images=req.reference_images,
        reference_video=req.reference_video,
        reference_map=req.reference_map)
    if not result["success"]:
        raise HTTPException(500, result["error"])
    return {"task_id": result["task_db_id"], "status": "submitted"}


class ImageEditRequest(BaseModel):
    image_url: str  # 用户上传的图片URL
    generate_type: str  # image_inpaint, image_outpaint, image_relight, remove_bg_comfy
    prompt: str = ""
    ratio: str = "1:1"
    resolution: str = "2K"
    reference_images: list = []

class ImageEnhanceRequest(BaseModel):
    image_url: str
    resolution: str = "4K"

class PromptReverseRequest(BaseModel):
    image_url: str


@app.post("/api/image_edit")
def image_edit(req: ImageEditRequest):
    """图片编辑：局部重绘/外扩/重光照/抠图等。"""
    client = pool.get_available_client()
    if not client:
        raise HTTPException(503, "No available account")
    ok, result = client.image_edit(
        req.image_url, req.generate_type, req.prompt,
        req.ratio, req.resolution, req.reference_images)
    if not ok:
        raise HTTPException(500, result)
    return {"task_id": result, "status": "submitted"}

@app.post("/api/image_enhance")
def image_enhance(req: ImageEnhanceRequest):
    """图片高清化。"""
    client = pool.get_available_client()
    if not client:
        raise HTTPException(503, "No available account")
    ok, result = client.image_enhance(req.image_url, req.resolution)
    if not ok:
        raise HTTPException(500, result)
    return {"task_id": result, "status": "submitted"}

@app.post("/api/prompt_reverse")
def prompt_reverse(req: PromptReverseRequest):
    """提示词反推。"""
    client = pool.get_available_client()
    if not client:
        raise HTTPException(503, "No available account")
    ok, result = client.prompt_reverse(req.image_url)
    if not ok:
        raise HTTPException(500, result)
    return {"task_id": result, "status": "submitted"}


class VideoCombineRequest(BaseModel):
    video_urls: list  # 视频URL列表
    output_name: str = "combined"

class VideoTrimRequest(BaseModel):
    video_url: str
    trim_start_ms: int  # 起始毫秒
    trim_end_ms: int    # 结束毫秒

class VideoSubtitleEraseRequest(BaseModel):
    video_url: str

class VideoEnhanceRequest(BaseModel):
    video_url: str
    resolution: str = "1080p"


@app.post("/api/video_combine")
def video_combine(req: VideoCombineRequest):
    """视频合并。"""
    client = pool.get_available_client()
    if not client:
        raise HTTPException(503, "No available account")
    ok, result = client.video_combine(req.video_urls, req.output_name)
    if not ok:
        raise HTTPException(500, result)
    return {"task_id": result, "status": "submitted"}

@app.post("/api/video_trim")
def video_trim(req: VideoTrimRequest):
    """视频裁剪。"""
    client = pool.get_available_client()
    if not client:
        raise HTTPException(503, "No available account")
    ok, result = client.video_trim(req.video_url, req.trim_start_ms, req.trim_end_ms)
    if not ok:
        raise HTTPException(500, result)
    return {"task_id": result, "status": "submitted"}

@app.post("/api/video_subtitle_erase")
def video_subtitle_erase(req: VideoSubtitleEraseRequest):
    """视频字幕擦除。"""
    client = pool.get_available_client()
    if not client:
        raise HTTPException(503, "No available account")
    ok, result = client.video_subtitle_erase(req.video_url)
    if not ok:
        raise HTTPException(500, result)
    return {"task_id": result, "status": "submitted"}

@app.post("/api/video_enhance")
def video_enhance(req: VideoEnhanceRequest):
    """视频增强/高清化。"""
    client = pool.get_available_client()
    if not client:
        raise HTTPException(503, "No available account")
    ok, result = client.video_enhance(req.video_url, req.resolution)
    if not ok:
        raise HTTPException(500, result)
    return {"task_id": result, "status": "submitted"}


class PollEditTaskRequest(BaseModel):
    task_id: str       # oiioii.ai返回的编辑任务ID（字符串格式）
    task_type: str = "image"  # image 或 video
    account_id: int = 0  # 提交时使用的账号ID（可选，用于复用client）


@app.post("/api/poll_edit_task")
def poll_edit_task(req: PollEditTaskRequest):
    """轮询编辑任务状态（图片编辑/视频编辑等）。
    
    编辑任务的task_id是字符串格式（如image_edit_xxx），不在TaskDB中，
    需要通过OiioiiClient直接查询oiioii.ai的async_tasks接口。
    """
    client = pool.get_available_client(min_points=0)
    if not client:
        raise HTTPException(503, "No available account")

    try:
        # 用check_result_once查询oiioii.ai的async_tasks
        asset_type = "image" if req.task_type == "image" else "video"
        status, uri = client.check_result_once(
            asset_type, set(), remote_task_id=req.task_id)

        if status == "completed" and uri:
            # 下载结果到本地
            ok_dl, local_path = client.download(uri)
            return {
                "status": "completed",
                "uri": uri,
                "local_path": local_path if ok_dl else "",
            }
        elif status == "failed":
            return {"status": "failed", "error": uri}
        else:
            return {"status": "pending"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


class MusicGenRequest(BaseModel):
    prompt: str
    style: str = ""
    duration: int = 0
    instrumental: bool = False


@app.post("/api/generate_music")
def generate_music(req: MusicGenRequest):
    """音乐生成（Suno）。"""
    client = pool.get_available_client()
    if not client:
        raise HTTPException(503, "No available account")
    ok, result = client.generate_music(req.prompt, req.style, req.duration, req.instrumental)
    if not ok:
        if result == "INSUFFICIENT_POINTS":
            raise HTTPException(402, "Insufficient points")
        raise HTTPException(500, result)
    return {"task_id": result, "status": "submitted"}


@app.get("/api/task/{task_id}")
def get_task(task_id: int):
    task = TaskDB.get_by_id(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return {
        "task_id": task["id"],
        "type": task["task_type"],
        "model": task["model_name"],
        "prompt": task["prompt"],
        "status": task["status"],
        "result_uri": task["result_uri"],
        "local_path": task["local_path"],
        "points_cost": task["points_cost"],
        "error": task["error_message"],
        "created_at": task["created_at"],
        "completed_at": task["completed_at"],
    }


@app.get("/api/task/{task_id}/download")
def download_task(task_id: int):
    task = TaskDB.get_by_id(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task["status"] != "completed":
        raise HTTPException(400, f"Task status is {task['status']}, not completed")
    if task["local_path"] and os.path.exists(task["local_path"]):
        return FileResponse(task["local_path"], filename=os.path.basename(task["local_path"]))
    if task["result_uri"] and task["result_uri"].startswith("hogi://"):
        from core.pool import AccountPool
        _pool = AccountPool()
        client = _pool.get_available_client(min_points=0)
        if client:
            ok, local_path = client.download(task["result_uri"])
            if ok and local_path:
                TaskDB.update_status(task_id, "completed", result_uri=task["result_uri"], local_path=local_path)
                return FileResponse(local_path, filename=os.path.basename(local_path))
    raise HTTPException(404, "File not found on disk")


@app.post("/api/task/{task_id}/retry")
def retry_task(task_id: int):
    result = engine.retry(task_id)
    if not result["success"]:
        raise HTTPException(500, result["error"])
    return {"task_id": result["task_db_id"], "status": "submitted"}


@app.delete("/api/task/{task_id}")
def delete_task(task_id: int):
    """删除任务记录及磁盘文件"""
    task = TaskDB.get_by_id(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    # 删除磁盘文件
    local_path = task.get("local_path", "")
    if local_path and os.path.isfile(local_path):
        try:
            os.remove(local_path)
        except Exception:
            pass
    # 删除数据库记录
    TaskDB.delete(task_id)
    return {"success": True}


@app.post("/api/tasks/batch_delete")
def batch_delete_tasks(req: dict):
    """批量删除任务记录及磁盘文件"""
    ids = req.get("ids", [])
    deleted = 0
    for tid in ids:
        try:
            tid = int(tid)
            task = TaskDB.get_by_id(tid)
            if task:
                local_path = task.get("local_path", "")
                if local_path and os.path.isfile(local_path):
                    try:
                        os.remove(local_path)
                    except Exception:
                        pass
                TaskDB.delete(tid)
                deleted += 1
        except (ValueError, TypeError):
            pass
    return {"success": True, "deleted": deleted}


@app.get("/api/pool/status")
def pool_status(sync: bool = False):
    accounts = AccountDB.get_all()
    now_ts = time.time()
    last_sync_at = None

    if sync:
        from core.client import OiioiiClient
        last_sync_at = now_ts
        for a in accounts:
            if a.get("status") != "active":
                continue
            try:
                client = OiioiiClient(
                    email=a["email"],
                    password=a["password"],
                    token=a.get("token", ""),
                    workspace_id=a.get("workspace_id", ""),
                    account_id=a["id"],
                )
                real_points = client.get_points()
                if real_points >= 0:
                    AccountDB.update_points_with_sync(a["id"], real_points, now_ts)
                    a["points_remaining"] = real_points
            except Exception:
                pass
        accounts = AccountDB.get_all()

    return {
        "total_accounts": len(accounts),
        "active_accounts": AccountDB.active_count(),
        "total_points": AccountDB.total_points(),
        "continuous_reg_running": _continuous_reg_running,
        "last_sync_at": last_sync_at,
        "accounts": [
            {
                "id": a["id"],
                "email": a["email"],
                "points": a["points_remaining"],
                "status": a["status"],
                "total_earned": a["total_earned"],
                "last_used_at": a["last_used_at"],
                "created_at": a["created_at"],
                "last_sync_at": a.get("last_sync_at", 0),
            }
            for a in accounts
        ],
    }


@app.post("/api/pool/sync_points")
def sync_points():
    from core.client import OiioiiClient
    accounts = AccountDB.get_all()
    active = [a for a in accounts if a.get("status") == "active"]
    now_ts = time.time()
    success_count = 0
    fail_count = 0
    details = []

    for a in active:
        try:
            client = OiioiiClient(
                email=a["email"],
                password=a["password"],
                token=a.get("token", ""),
                workspace_id=a.get("workspace_id", ""),
                account_id=a["id"],
            )
            real_points = client.get_points()
            if real_points >= 0:
                AccountDB.update_points_with_sync(a["id"], real_points, now_ts)
                success_count += 1
                details.append({
                    "id": a["id"],
                    "email": a["email"],
                    "previous_points": a["points_remaining"],
                    "current_points": real_points,
                })
            else:
                fail_count += 1
                details.append({
                    "id": a["id"],
                    "email": a["email"],
                    "error": "get_points returned -1 (login or API failure)",
                })
        except Exception as e:
            fail_count += 1
            details.append({
                "id": a["id"],
                "email": a["email"],
                "error": str(e),
            })

    return {
        "success": True,
        "total_accounts": len(active),
        "synced": success_count,
        "failed": fail_count,
        "last_sync_at": now_ts,
        "details": details,
    }


@app.get("/api/models")
def list_models():
    cache = get_cached_models()
    return {
        "image": cache.get("image", {}),
        "video": cache.get("video", {}),
        "video_min_points": VIDEO_MIN_POINTS,
    }


@app.get("/api/tasks")
def list_tasks(limit: int = 50):
    tasks = TaskDB.get_all(limit)
    return {
        "tasks": [
            {
                "id": t["id"],
                "type": t["task_type"],
                "model": t["model_name"],
                "prompt": t["prompt"],
                "status": t["status"],
                "ratio": t["ratio"],
                "resolution": t["resolution"],
                "duration": t["duration"],
                "points_cost": t["points_cost"],
                "result_uri": t["result_uri"],
                "local_path": t["local_path"],
                "error": t["error_message"],
                "account_email": t.get("account_email", ""),
                "created_at": t["created_at"],
                "completed_at": t["completed_at"],
            }
            for t in tasks
        ]
    }


@app.post("/api/pool/add")
def add_account(req: AddAccountRequest):
    result = pool.add_account(req.email, req.password)
    if not result["success"]:
        raise HTTPException(500, result["error"])
    return {"success": True, "account_id": result["account_id"], "points": result["points"]}


class BulkImportAccounts(BaseModel):
    accounts: list  # [{"email": "...", "password": "..."}]


@app.post("/api/pool/bulk_add")
def bulk_add_accounts(req: BulkImportAccounts):
    """批量导入账号（从本地注册结果文件直接导入）"""
    results = []
    ok = 0
    fail = 0
    for acc in req.accounts:
        try:
            result = pool.add_account(acc.get("email", ""), acc.get("password", ""))
            if result["success"]:
                ok += 1
                results.append({"email": acc.get("email"), "success": True, "account_id": result["account_id"], "points": result["points"]})
            else:
                fail += 1
                results.append({"email": acc.get("email"), "success": False, "error": result.get("error", "")})
        except Exception as e:
            fail += 1
            results.append({"email": acc.get("email"), "success": False, "error": str(e)})
        if len(req.accounts) > 1:
            import time as _t
            _t.sleep(0.5)  # 避免触发限流
    return {"success": ok, "failed": fail, "total": len(req.accounts), "details": results}


@app.post("/api/pool/register")
def register_account(count: int = 1, concurrent: int = 1):
    job_id = str(int(time.time() * 1000))
    workers = max(1, min(concurrent, 10))  # 最多10个并发
    _reg_jobs[job_id] = {"status": "running", "result": None, "progress": [0, count], "details": []}

    def _do_one(idx):
        try:
            result = pool.auto_register()
            return {"index": idx, "success": result["success"], "email": result.get("email", ""), "points": result.get("points", 0), "error": result.get("error", "")}
        except Exception as e:
            return {"index": idx, "success": False, "email": "", "points": 0, "error": str(e)}

    def _do():
        ok_count = 0
        fail_count = 0
        details = []
        if workers <= 1 or count <= 1:
            # 串行模式
            for i in range(count):
                r = _do_one(i)
                details.append(r)
                if r["success"]:
                    ok_count += 1
                else:
                    fail_count += 1
                _reg_jobs[job_id]["progress"] = [i + 1, count]
                if i < count - 1:
                    time.sleep(2)
        else:
            # 并发模式
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {executor.submit(_do_one, i): i for i in range(count)}
                done_count = 0
                for future in as_completed(futures):
                    r = future.result()
                    details.append(r)
                    if r["success"]:
                        ok_count += 1
                    else:
                        fail_count += 1
                    done_count += 1
                    _reg_jobs[job_id]["progress"] = [done_count, count]
        # 按index排序
        details.sort(key=lambda x: x["index"])
        _reg_jobs[job_id] = {
            "status": "done",
            "result": {"success": True, "registered": ok_count, "failed": fail_count},
            "progress": [count, count],
            "details": details
        }

    threading.Thread(target=_do, daemon=True).start()
    return {"job_id": job_id, "status": "running", "count": count, "concurrent": workers}


@app.get("/api/pool/register/{job_id}")
def register_status(job_id: str):
    job = _reg_jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job["status"] == "running":
        return {"status": "running", "progress": job.get("progress", [0, 0])}
    result = job["result"]
    details = job.get("details", [])
    if result and result.get("success"):
        return {"status": "done", "registered": result.get("registered", 0), "failed": result.get("failed", 0), "details": details}
    return {"status": "failed", "error": (result or {}).get("error", "Unknown"), "details": details}


@app.post("/api/pool/continuous_reg")
def toggle_continuous_reg(enable: bool = True, target_count: int = 10):
    global _continuous_reg_running, _continuous_reg_thread

    if not enable:
        _continuous_reg_running = False
        return {"status": "stopped"}

    if _continuous_reg_running:
        return {"status": "already_running"}

    _continuous_reg_running = True

    def _continuous_loop():
        global _continuous_reg_running
        registered = 0
        while _continuous_reg_running and registered < target_count:
            try:
                result = pool.auto_register()
                if result["success"]:
                    registered += 1
                    print(f"[ContinuousReg] #{registered}/{target_count} ok")
                else:
                    print(f"[ContinuousReg] failed: {result.get('error', 'unknown')}")
            except Exception as e:
                print(f"[ContinuousReg] error: {e}")
            if _continuous_reg_running and registered < target_count:
                time.sleep(3)
        _continuous_reg_running = False
        print(f"[ContinuousReg] finished: {registered}/{target_count}")

    _continuous_reg_thread = threading.Thread(target=_continuous_loop, daemon=True)
    _continuous_reg_thread.start()
    return {"status": "running", "target": target_count}


@app.get("/api/pool/continuous_reg/status")
def continuous_reg_status():
    return {"running": _continuous_reg_running}


@app.post("/api/pool/refresh")
def refresh_all():
    results = pool.refresh_all()
    ok = sum(1 for r in results if r.get("alive"))
    return {"success": True, "alive": ok, "total": len(results)}


@app.post("/api/pool/daily_claim_all")
def daily_claim_all():
    """为所有活跃账号领取每日签到积分"""
    accounts = AccountDB.get_all()
    active = [a for a in accounts if a.get("status") == "active"]
    from core.client import OiioiiClient
    results = []
    claimed = 0
    skipped = 0
    failed = 0
    for a in active:
        try:
            client = OiioiiClient(
                email=a["email"],
                password=a["password"],
                token=a.get("token", ""),
                workspace_id=a.get("workspace_id", ""),
                account_id=a["id"],
            )
            r = client.daily_claim()
            if r["success"]:
                if r.get("added", 0) > 0:
                    claimed += 1
                    AccountDB.update_points(a["id"], r.get("total", 0))
                    results.append({"email": a["email"], "added": r.get("added", 0)})
                else:
                    skipped += 1
            else:
                failed += 1
                results.append({"email": a["email"], "error": r.get("error", "?")})
        except Exception as e:
            failed += 1
            results.append({"email": a["email"], "error": str(e)})
    return {
        "success": True,
        "total": len(accounts),
        "claimed": claimed,
        "skipped": skipped,
        "failed": failed,
        "details": results,
    }


@app.delete("/api/pool/{account_id}")
def remove_account(account_id: int):
    pool.remove_account(account_id)
    return {"success": True}


@app.get("/api/file/{task_id}")
def serve_task_file(task_id: int):
    """下载生成结果文件（API 客户用）"""
    task = TaskDB.get_by_id(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    local_path = task.get("local_path", "")
    if not local_path or not os.path.exists(local_path):
        result_uri = task.get("result_uri", "")
        if result_uri:
            return {"url": result_uri}
        raise HTTPException(404, "File not found")
    return FileResponse(local_path)


def run_api():
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)


if __name__ == "__main__":
    run_api()
