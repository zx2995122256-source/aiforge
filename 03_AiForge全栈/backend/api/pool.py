from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from api.auth import admin_required
from config import OIIOII_API

router = APIRouter(prefix="/api/pool", tags=["pool"])


class AddAccountReq(BaseModel):
    email: str
    password: str


def _oiioii(method: str, path: str, json_body: dict = None, timeout: int = 10):
    import requests
    url = f"{OIIOII_API}{path}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=timeout)
        elif method == "POST":
            r = requests.post(url, json=json_body, timeout=timeout)
        elif method == "DELETE":
            r = requests.delete(url, timeout=timeout)
        else:
            return {"error": f"Unsupported method {method}"}
        if r.status_code == 200:
            return r.json()
        return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"error": str(e)}


@router.get("/status")
def pool_status(admin: dict = Depends(admin_required)):
    return _oiioii("GET", "/api/pool/status")


@router.post("/add")
def add_account(req: AddAccountReq, admin: dict = Depends(admin_required)):
    result = _oiioii("POST", "/api/pool/add", {"email": req.email, "password": req.password}, 15)
    if "error" in result:
        raise HTTPException(500, result["error"])
    return result


@router.post("/register")
def register_account(count: int = 1, admin: dict = Depends(admin_required)):
    result = _oiioii("POST", "/api/pool/register", None, 30)
    if "error" in result:
        raise HTTPException(500, result["error"])
    return result


@router.post("/refresh")
def refresh_pool(admin: dict = Depends(admin_required)):
    result = _oiioii("POST", "/api/pool/refresh", None, 60)
    if "error" in result:
        raise HTTPException(500, result["error"])
    return result


@router.delete("/{account_id}")
def remove_account(account_id: int, admin: dict = Depends(admin_required)):
    result = _oiioii("DELETE", f"/api/pool/{account_id}")
    if "error" in result:
        raise HTTPException(500, result["error"])
    return result
