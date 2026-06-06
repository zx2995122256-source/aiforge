from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from api.auth import auth_required, admin_required
from models.db import get_user, add_points, redeem_code, create_redeem_code, get_all_users, get_user_tasks, cleanup_old_tasks, get_stats, _get_conn
from config import PLANS, POINTS_PER_YUAN
import json

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/profile")
def profile(user: dict = Depends(auth_required)):
    u = get_user(user["id"])
    if not u:
        raise HTTPException(404, "用户不存在")
    return u


@router.get("/points")
def points(user: dict = Depends(auth_required)):
    u = get_user(user["id"])
    return {"points": u["points"] if u else 0}


@router.post("/redeem")
def redeem(code: str, user: dict = Depends(auth_required)):
    result = redeem_code(code, user["id"])
    if not result["ok"]:
        raise HTTPException(400, result["msg"])
    return result


@router.get("/history")
def history(user: dict = Depends(auth_required), limit: int = 50):
    return get_user_tasks(user["id"], limit)


@router.get("/point_logs")
def point_logs(user: dict = Depends(auth_required), limit: int = 50):
    """查询积分变动记录"""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM point_logs WHERE uid = ? ORDER BY id DESC LIMIT ?",
        (user["id"], limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/plans")
def plans():
    return PLANS


@router.get("/admin/users")
def admin_users(admin: dict = Depends(admin_required), limit: int = 100):
    return get_all_users(limit)


@router.post("/admin/redeem")
def admin_create_redeem(points: int, admin: dict = Depends(admin_required)):
    code = create_redeem_code(points)
    return {"code": code, "points": points}


@router.post("/admin/add_points")
def admin_add_points(uid: int, points: int, reason: str = "管理员调整", admin: dict = Depends(admin_required)):
    add_points(uid, points, reason)
    u = get_user(uid)
    return {"uid": uid, "points": u["points"] if u else 0}


@router.post("/admin/cleanup")
def admin_cleanup(days: int = 30, admin: dict = Depends(admin_required)):
    deleted = cleanup_old_tasks(days)
    return {"deleted": deleted, "msg": f"已清理 {days} 天前的 {deleted} 条记录"}


@router.get("/admin/stats")
def admin_stats(admin: dict = Depends(admin_required)):
    return get_stats()


# ─── LLM Settings ───

class LLMSettingsReq(BaseModel):
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


@router.get("/llm-settings")
def get_llm_settings(user: dict = Depends(auth_required)):
    conn = _get_conn()
    row = conn.execute("SELECT llm_settings FROM users WHERE id=?", (user["id"],)).fetchone()
    conn.close()
    if row and row["llm_settings"]:
        try:
            return json.loads(row["llm_settings"])
        except Exception:
            pass
    return {}


@router.put("/llm-settings")
def update_llm_settings(req: LLMSettingsReq, user: dict = Depends(auth_required)):
    conn = _get_conn()
    row = conn.execute("SELECT llm_settings FROM users WHERE id=?", (user["id"],)).fetchone()
    existing = {}
    if row and row["llm_settings"]:
        try:
            existing = json.loads(row["llm_settings"])
        except Exception:
            pass
    # Merge: only update non-None fields
    if req.api_url is not None:
        existing["api_url"] = req.api_url
    if req.api_key is not None:
        existing["api_key"] = req.api_key
    if req.model is not None:
        existing["model"] = req.model
    if req.temperature is not None:
        existing["temperature"] = req.temperature
    if req.max_tokens is not None:
        existing["max_tokens"] = req.max_tokens
    conn.execute("UPDATE users SET llm_settings=?, updated_at=? WHERE id=?",
                 (json.dumps(existing, ensure_ascii=False), __import__('time').time(), user["id"]))
    conn.commit()
    conn.close()
    return existing
