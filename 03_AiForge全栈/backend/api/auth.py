import time
import jwt
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from config import SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_HOURS
from models.db import create_user, verify_user, get_user, count_registrations_by_ip, get_agent_by_code
from config import MAX_REGISTER_PER_IP

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterReq(BaseModel):
    email: str
    password: str
    nickname: str = ""


class LoginReq(BaseModel):
    email: str
    password: str


def _make_token(uid: int, role: str) -> str:
    payload = {"uid": uid, "role": role, "exp": int(time.time()) + JWT_EXPIRE_HOURS * 3600}
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def auth_required(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "未登录")
    try:
        payload = jwt.decode(auth[7:], SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "登录已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "无效Token")
    uid = payload.get("uid")
    user = get_user(uid)
    if not user:
        raise HTTPException(401, "用户不存在")
    return user


def admin_required(user: dict = Depends(auth_required)):
    if user["role"] != "admin":
        raise HTTPException(403, "需要管理员权限")
    return user


@router.post("/register")
def register(req: RegisterReq, request: Request, ref: str = ""):
    if len(req.password) < 6:
        raise HTTPException(400, "密码至少6位")
    if "@" not in req.email:
        raise HTTPException(400, "邮箱格式不正确")
    # Anti-abuse: check IP registration limit
    client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else "unknown")
    reg_count = count_registrations_by_ip(client_ip)
    if reg_count >= MAX_REGISTER_PER_IP:
        raise HTTPException(429, "该网络注册次数已达上限，请明日再试")

    # Check referral code
    inviter_agent_id = 0
    if ref:
        agent = get_agent_by_code(ref)
        if agent:
            inviter_agent_id = agent["id"]

    result = create_user(req.email, req.password, req.nickname, register_ip=client_ip, inviter_agent_id=inviter_agent_id)
    if not result:
        raise HTTPException(400, "该邮箱已注册")
    token = _make_token(result["id"], result["role"])
    return {"token": token, "user": result}


@router.post("/login")
def login(req: LoginReq):
    user = verify_user(req.email, req.password)
    if not user:
        raise HTTPException(401, "邮箱或密码错误")
    token = _make_token(user["id"], user["role"])
    return {"token": token, "user": {"id": user["id"], "email": user["email"],
                                      "nickname": user["nickname"], "points": user["points"],
                                      "role": user["role"]}}


@router.get("/me")
def me(user: dict = Depends(auth_required)):
    return user
