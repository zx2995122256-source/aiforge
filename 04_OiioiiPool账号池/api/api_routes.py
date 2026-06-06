"""OpenAI 兼容 API + 管理接口"""
import time
import threading
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel
from api.api_db import (
    verify_api_key, create_user, verify_user, get_user, update_balance,
    list_users, create_api_key, list_api_keys, revoke_api_key,
    update_key_used_quota, create_log, update_log_status, get_logs, get_usage_stats,
    create_redeem_codes, redeem_code, list_redeem_codes
)
from api.pricing import get_price, get_internal_model, get_model_type, list_models, ALL_MODELS

router = APIRouter()

# Session存储（内存）
_sessions = {}

# 限速：内存中的简单计数器
_rate_limit_store = {}  # key_id -> [timestamp_list]
_rate_lock = threading.Lock()


def _check_rate_limit(key_id: int, limit: int) -> bool:
    """每分钟 limit 次"""
    now = time.time()
    with _rate_lock:
        if key_id not in _rate_limit_store:
            _rate_limit_store[key_id] = []
        timestamps = _rate_limit_store[key_id]
        # 清理 60s 前的
        _rate_limit_store[key_id] = [t for t in timestamps if now - t < 60]
        if len(_rate_limit_store[key_id]) >= limit:
            return False
        _rate_limit_store[key_id].append(now)
        return True


def _get_key_info(authorization: str) -> dict:
    """从 Authorization header 提取并验证 API Key 或 Session Token"""
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")
    if authorization.startswith("Bearer "):
        raw_key = authorization[7:].strip()
    else:
        raw_key = authorization.strip()

    # Session token (管理接口用)
    if raw_key.startswith("sess-"):
        sess = _sessions.get(raw_key)
        if not sess:
            raise HTTPException(401, "Invalid session token")
        # 刷新余额
        user = get_user(sess["user_id"])
        if user:
            sess["balance"] = user["balance"]
        return {
            "success": True,
            "key_id": 0,
            "user_id": sess["user_id"],
            "username": sess["username"],
            "balance": sess["balance"],
            "role": sess["role"],
            "rate_limit": 999,
            "models": "",
            "quota": 0,
            "used_quota": 0,
        }

    # API Key (OpenAI接口用)
    result = verify_api_key(raw_key)
    if not result["success"]:
        raise HTTPException(401, result["error"])
    return result


# ─── OpenAI 兼容接口 ───

class ImageGenerationRequest(BaseModel):
    model: str = "gpt-image-2"
    prompt: str
    n: int = 1
    size: str = "1024x1024"
    response_format: str = "url"


class VideoGenerationRequest(BaseModel):
    model: str = "grok-imagine"
    prompt: str
    duration: int = 10
    aspect_ratio: str = "16:9"
    resolution: str = "720p"


@router.get("/v1/models")
def api_list_models():
    return {"object": "list", "data": list_models()}


@router.post("/v1/images/generations")
def api_generate_image(req: ImageGenerationRequest, authorization: str = Header(None)):
    key_info = _get_key_info(authorization or "")

    # 模型检查
    if req.model not in ALL_MODELS or get_model_type(req.model) != "image":
        raise HTTPException(400, f"Unsupported image model: {req.model}")

    # 解析分辨率
    resolution = "2K"
    if "4k" in req.size.lower() or "2048" in req.size or "4096" in req.size:
        resolution = "4K"

    # 计价
    price = get_price(req.model, resolution=resolution)
    if price < 0:
        raise HTTPException(400, f"No pricing for {req.model} at {resolution}")

    total_cost = price * req.n

    # 余额检查
    if key_info["balance"] < total_cost:
        raise HTTPException(402, f"Insufficient balance. Need ¥{total_cost:.2f}, have ¥{key_info['balance']:.2f}")

    # 限速
    if not _check_rate_limit(key_info["key_id"], key_info["rate_limit"]):
        raise HTTPException(429, "Rate limit exceeded")

    # 模型权限检查
    if key_info["models"]:
        allowed = [m.strip() for m in key_info["models"].split(",")]
        if req.model not in allowed:
            raise HTTPException(403, f"Model {req.model} not allowed for this key")

    # 预扣费
    if not update_balance(key_info["user_id"], -total_cost):
        raise HTTPException(402, "Insufficient balance")

    # 记日志
    log_id = create_log(
        user_id=key_info["user_id"],
        key_id=key_info["key_id"],
        model=req.model,
        task_type="image",
        resolution=resolution,
        cost_yuan=total_cost,
    )

    # 提交生成
    internal_model = get_internal_model(req.model)
    engine = _get_engine()
    if not engine:
        update_balance(key_info["user_id"], total_cost)
        update_log_status(log_id, "failed", "Engine not available")
        raise HTTPException(503, "Generation engine not available")

    # 解析 ratio
    ratio = "1:1"
    if "x" in req.size:
        w, h = req.size.lower().split("x")
        if int(w) > int(h):
            ratio = "16:9"
        elif int(w) < int(h):
            ratio = "9:16"

    result = engine.submit(
        task_type="image",
        model_name=internal_model,
        prompt=req.prompt,
        ratio=ratio,
        resolution=resolution,
    )

    if not result["success"]:
        update_balance(key_info["user_id"], total_cost)
        update_log_status(log_id, "failed", result.get("error", "Submit failed"))
        raise HTTPException(500, result.get("error", "Submit failed"))

    task_db_id = result["task_db_id"]
    update_log_status(log_id, "processing", task_id=task_db_id)
    update_key_used_quota(key_info["key_id"], total_cost)

    # 异步等待结果
    _start_result_poller(task_db_id, log_id, key_info["user_id"], key_info["key_id"], total_cost, req.response_format)

    # 立即返回任务 ID
    return {
        "object": "list",
        "data": [{
            "id": str(task_db_id),
            "object": "image",
            "status": "processing",
            "model": req.model,
            "prompt": req.prompt,
            "size": req.size,
            "cost": total_cost,
        }],
        "task_id": str(task_db_id),
    }


@router.post("/v1/videos/generations")
def api_generate_video(req: VideoGenerationRequest, authorization: str = Header(None)):
    key_info = _get_key_info(authorization or "")

    if req.model not in ALL_MODELS or get_model_type(req.model) != "video":
        raise HTTPException(400, f"Unsupported video model: {req.model}")

    price = get_price(req.model, duration=req.duration, resolution=req.resolution)
    if price < 0:
        raise HTTPException(400, f"No pricing for {req.model} {req.duration}s {req.resolution}")

    if key_info["balance"] < price:
        raise HTTPException(402, f"Insufficient balance. Need ¥{price:.2f}, have ¥{key_info['balance']:.2f}")

    if not _check_rate_limit(key_info["key_id"], key_info["rate_limit"]):
        raise HTTPException(429, "Rate limit exceeded")

    if key_info["models"]:
        allowed = [m.strip() for m in key_info["models"].split(",")]
        if req.model not in allowed:
            raise HTTPException(403, f"Model {req.model} not allowed for this key")

    if not update_balance(key_info["user_id"], -price):
        raise HTTPException(402, "Insufficient balance")

    log_id = create_log(
        user_id=key_info["user_id"],
        key_id=key_info["key_id"],
        model=req.model,
        task_type="video",
        duration=req.duration,
        resolution=req.resolution,
        cost_yuan=price,
    )

    internal_model = get_internal_model(req.model)
    engine = _get_engine()
    if not engine:
        update_balance(key_info["user_id"], price)
        update_log_status(log_id, "failed", "Engine not available")
        raise HTTPException(503, "Generation engine not available")

    result = engine.submit(
        task_type="video",
        model_name=internal_model,
        prompt=req.prompt,
        ratio=req.aspect_ratio,
        resolution=req.resolution,
        duration=req.duration,
    )

    if not result["success"]:
        update_balance(key_info["user_id"], price)
        update_log_status(log_id, "failed", result.get("error", "Submit failed"))
        raise HTTPException(500, result.get("error", "Submit failed"))

    task_db_id = result["task_db_id"]
    update_log_status(log_id, "processing", task_id=task_db_id)
    update_key_used_quota(key_info["key_id"], price)

    return {
        "id": str(task_db_id),
        "object": "video.generation",
        "status": "processing",
        "model": req.model,
        "prompt": req.prompt,
        "duration": req.duration,
        "resolution": req.resolution,
        "cost": price,
    }


@router.get("/v1/videos/generations/{task_id}")
def api_get_video_status(task_id: str, authorization: str = Header(None)):
    _get_key_info(authorization or "")
    engine = _get_engine()
    if not engine:
        raise HTTPException(503, "Engine not available")

    task = engine.get_task(int(task_id))
    if not task:
        raise HTTPException(404, "Task not found")

    status_map = {
        "pending": "processing",
        "processing": "processing",
        "completed": "completed",
        "failed": "failed",
    }

    resp = {
        "id": task_id,
        "object": "video.generation",
        "status": status_map.get(task["status"], task["status"]),
        "model": task.get("model_name", ""),
    }

    if task["status"] == "completed":
        result_uri = task.get("result_uri", "")
        local_path = task.get("local_path", "")
        if local_path:
            resp["url"] = f"/api/file/{task_id}"
        elif result_uri:
            resp["url"] = result_uri
        resp["result_uri"] = result_uri
    elif task["status"] == "failed":
        resp["error"] = task.get("error_message", "Unknown error")

    return resp


@router.get("/v1/images/generations/{task_id}")
def api_get_image_status(task_id: str, authorization: str = Header(None)):
    return api_get_video_status(task_id, authorization)


# ─── 管理接口 ───

class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateKeyRequest(BaseModel):
    name: str = ""
    quota: float = 0
    rate_limit: int = 10
    models: str = ""
    expires_days: int = 0


class RechargeRequest(BaseModel):
    user_id: int
    amount: float


class SelfRegisterRequest(BaseModel):
    username: str
    password: str


# 新用户初始余额（元）
NEW_USER_BALANCE = 0.0


@router.post("/api/user/self-register")
def api_self_register(req: SelfRegisterRequest):
    """用户自助注册 — 自动创建账号 + 自动生成API Key + 初始余额"""
    if len(req.username) < 3 or len(req.username) > 32:
        raise HTTPException(400, "用户名需3-32个字符")
    if len(req.password) < 6:
        raise HTTPException(400, "密码至少6位")

    # 创建用户
    result = create_user(req.username, req.password)
    if not result["success"]:
        raise HTTPException(400, result["error"])

    user_id = result["user_id"]

    # 初始余额
    if NEW_USER_BALANCE > 0:
        update_balance(user_id, NEW_USER_BALANCE)

    # 自动创建一个API Key
    key_result = create_api_key(
        user_id=user_id,
        name="default",
        quota=0,
        rate_limit=10,
        models="",
        expires_at=0,
    )

    return {
        "success": True,
        "user_id": user_id,
        "username": req.username,
        "balance": NEW_USER_BALANCE,
        "api_key": key_result.get("key", "") if key_result.get("success") else "",
        "message": "注册成功！请保存好你的API Key",
    }


@router.post("/api/user/register")
def api_register(req: RegisterRequest, authorization: str = Header(None)):
    """注册用户（仅管理员）"""
    admin = _get_key_info(authorization or "")
    if admin["role"] != "admin":
        raise HTTPException(403, "Admin only")
    result = create_user(req.username, req.password)
    if not result["success"]:
        raise HTTPException(400, result["error"])
    return result


@router.post("/api/user/login")
def api_login(req: LoginRequest):
    result = verify_user(req.username, req.password)
    if not result["success"]:
        raise HTTPException(401, result["error"])
    # 生成session token: "sess-{user_id}-{random}"
    import secrets as _s
    session_token = f"sess-{result['user_id']}-{_s.token_hex(16)}"
    _sessions[session_token] = {
        "user_id": result["user_id"],
        "username": result["username"],
        "role": result["role"],
        "balance": result["balance"],
    }
    result["token"] = session_token
    return result


@router.get("/api/user/info")
def api_user_info(authorization: str = Header(None)):
    key_info = _get_key_info(authorization or "")
    user = get_user(key_info["user_id"])
    return user


@router.get("/api/user/balance")
def api_user_balance(authorization: str = Header(None)):
    key_info = _get_key_info(authorization or "")
    user = get_user(key_info["user_id"])
    return {"balance": user.get("balance", 0)}


@router.post("/api/key/create")
def api_create_key(req: CreateKeyRequest, authorization: str = Header(None)):
    key_info = _get_key_info(authorization or "")
    expires_at = 0
    if req.expires_days > 0:
        expires_at = time.time() + req.expires_days * 86400
    result = create_api_key(
        user_id=key_info["user_id"],
        name=req.name,
        quota=req.quota,
        rate_limit=req.rate_limit,
        models=req.models,
        expires_at=expires_at,
    )
    if not result["success"]:
        raise HTTPException(400, result["error"])
    return result


@router.get("/api/key/list")
def api_key_list(authorization: str = Header(None)):
    key_info = _get_key_info(authorization or "")
    keys = list_api_keys(user_id=key_info["user_id"])
    return {"keys": keys}


@router.delete("/api/key/{key_id}")
def api_key_revoke(key_id: int, authorization: str = Header(None)):
    key_info = _get_key_info(authorization or "")
    keys = list_api_keys(user_id=key_info["user_id"])
    if not any(k["id"] == key_id for k in keys):
        if key_info["role"] != "admin":
            raise HTTPException(403, "Not your key")
    revoke_api_key(key_id)
    return {"success": True}


@router.post("/api/user/recharge")
def api_recharge(req: RechargeRequest, authorization: str = Header(None)):
    """充值（仅管理员）"""
    admin = _get_key_info(authorization or "")
    if admin["role"] != "admin":
        raise HTTPException(403, "Admin only")
    if req.amount <= 0:
        raise HTTPException(400, "Amount must be positive")
    ok = update_balance(req.user_id, req.amount)
    if not ok:
        raise HTTPException(400, "Recharge failed")
    return {"success": True, "new_balance": get_user(req.user_id).get("balance", 0)}


@router.get("/api/admin/users")
def api_admin_users(authorization: str = Header(None)):
    admin = _get_key_info(authorization or "")
    if admin["role"] != "admin":
        raise HTTPException(403, "Admin only")
    return {"users": list_users()}


@router.get("/api/admin/keys")
def api_admin_keys(authorization: str = Header(None)):
    admin = _get_key_info(authorization or "")
    if admin["role"] != "admin":
        raise HTTPException(403, "Admin only")
    return {"keys": list_api_keys()}


@router.get("/api/logs")
def api_logs(authorization: str = Header(None), limit: int = 100):
    key_info = _get_key_info(authorization or "")
    if key_info["role"] == "admin":
        logs = get_logs(limit=limit)
    else:
        logs = get_logs(user_id=key_info["user_id"], limit=limit)
    return {"logs": logs}


@router.get("/api/stats")
def api_stats(authorization: str = Header(None)):
    key_info = _get_key_info(authorization or "")
    if key_info["role"] == "admin":
        stats = get_usage_stats()
    else:
        stats = get_usage_stats(user_id=key_info["user_id"])
    return stats


@router.get("/api/pricing")
def api_pricing():
    return {"models": list_models()}


# ─── 兑换码 ───

class CreateRedeemCodeRequest(BaseModel):
    amount: float
    count: int = 1


class RedeemRequest(BaseModel):
    code: str


@router.post("/api/redeem/create")
def api_create_redeem_codes(req: CreateRedeemCodeRequest, authorization: str = Header(None)):
    """批量生成兑换码（仅管理员）"""
    admin = _get_key_info(authorization or "")
    if admin["role"] != "admin":
        raise HTTPException(403, "Admin only")
    if req.amount <= 0:
        raise HTTPException(400, "金额必须大于0")
    if req.count < 1 or req.count > 100:
        raise HTTPException(400, "数量1-100")
    codes = create_redeem_codes(req.amount, req.count, created_by=admin["user_id"])
    return {"success": True, "codes": codes, "count": len(codes)}


@router.post("/api/redeem/use")
def api_use_redeem_code(req: RedeemRequest, authorization: str = Header(None)):
    """用户兑换码"""
    key_info = _get_key_info(authorization or "")
    result = redeem_code(req.code.strip().upper(), key_info["user_id"])
    if not result["success"]:
        raise HTTPException(400, result["error"])
    return result


@router.get("/api/redeem/list")
def api_list_redeem_codes(status: str = "", authorization: str = Header(None)):
    """查看兑换码列表（仅管理员）"""
    admin = _get_key_info(authorization or "")
    if admin["role"] != "admin":
        raise HTTPException(403, "Admin only")
    return {"codes": list_redeem_codes(status=status)}


# ─── 内部工具 ───

_engine_ref = None


def set_engine(engine):
    global _engine_ref
    _engine_ref = engine


def _get_engine():
    return _engine_ref


# 结果轮询：异步等待生成完成后更新日志
_result_pollers = {}


def _start_result_poller(task_db_id: int, log_id: int, user_id: int, key_id: int, cost: float, response_format: str):
    """后台线程等待生成结果，失败则退费"""
    if task_db_id in _result_pollers:
        return
    _result_pollers[task_db_id] = True

    def _poll():
        engine = _get_engine()
        if not engine:
            return
        max_wait = 600
        start = time.time()
        while time.time() - start < max_wait:
            time.sleep(5)
            task = engine.get_task(task_db_id)
            if not task:
                update_log_status(log_id, "failed", "Task not found")
                update_balance(user_id, cost)  # 退费
                break
            if task["status"] == "completed":
                update_log_status(log_id, "completed")
                break
            if task["status"] == "failed":
                update_log_status(log_id, "failed", task.get("error_message", ""))
                update_balance(user_id, cost)  # 退费
                break
        else:
            update_log_status(log_id, "failed", "Timeout")
            update_balance(user_id, cost)  # 退费
        _result_pollers.pop(task_db_id, None)

    threading.Thread(target=_poll, daemon=True).start()
