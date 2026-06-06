import time
import hashlib
import os
import requests
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from api.auth import auth_required
from models.db import create_order, pay_order, get_user, _get_conn
from config import PLANS, POINTS_PER_YUAN, SECRET_KEY, AIFORGE_BASE_URL
from api.alipay_pay import _get_alipay, create_alipay_order, verify_alipay_notify

router = APIRouter(prefix="/api/pay", tags=["payment"])

PAY_URL = ""
PAY_PID = ""
PAY_KEY = ""
PAY_TYPE = "epay"
WECHAT_QR_URL = os.environ.get("AIFORGE_WECHAT_QR", "")
PAY_NOTIFY_KEY = os.environ.get("AIFORGE_NOTIFY_KEY", "aiforge2025")

# 收钱吧配置
from api.sqb_pay import init_sqb, create_sqb_order, handle_sqb_callback, query_sqb_order

def _init_sqb_from_env():
    sn = os.environ.get("SQB_VENDOR_SN", "")
    key = os.environ.get("SQB_VENDOR_KEY", "")
    app_id = os.environ.get("SQB_APP_ID", "")
    qr = os.environ.get("SQB_QR_CODE_URL", "")
    if sn and key:
        init_sqb(sn, key, app_id, qr)
        print(f"[Payment] 收钱吧已配置 vendor_sn={sn[:6]}...")

_init_sqb_from_env()


def init_payment(url: str, pid: str, key: str, ptype: str = "epay"):
    global PAY_URL, PAY_PID, PAY_KEY, PAY_TYPE
    PAY_URL = url.rstrip("/")
    PAY_PID = pid
    PAY_KEY = key
    PAY_TYPE = ptype


class CreateOrderReq(BaseModel):
    plan_id: str


@router.post("/create")
def create_payment(req: CreateOrderReq, user: dict = Depends(auth_required)):
    plan = next((p for p in PLANS if p["id"] == req.plan_id), None)
    if not plan:
        raise HTTPException(400, "套餐不存在")
    oid = create_order(user["id"], plan["id"], plan["price"], plan["points"])

    # 支付宝支付（优先）
    if os.environ.get("ALIPAY_APP_ID") and os.environ.get("ALIPAY_PRIVATE_KEY"):
        return create_alipay_order(oid, plan)

    if PAY_TYPE == "wechat_qr" or (not PAY_URL and WECHAT_QR_URL):
        return {
            "order_id": oid,
            "status": "pending",
            "pay_method": "wechat_qr",
            "qr_url": WECHAT_QR_URL,
            "amount": plan["price"],
            "plan_name": plan["name"],
            "points": plan["points"],
            "user_id": user["id"],
            "msg": f"请扫码支付 ¥{plan['price']}，付款后在订单页面等待确认"
        }

    # 收钱吧支付（优先）
    if os.environ.get("SQB_VENDOR_SN"):
        return create_sqb_order(oid, plan["price"], plan["name"])

    if not PAY_URL:
        raise HTTPException(503, "支付系统暂未开放，请联系客服充值")

    if PAY_TYPE == "xunhu":
        return _create_xunhu(oid, plan)
    return _create_epay(oid, plan)


@router.get("/qr")
def get_wechat_qr():
    if not WECHAT_QR_URL:
        raise HTTPException(404, "未配置微信收款码")
    return {"qr_url": WECHAT_QR_URL}


def _create_epay(oid: int, plan: dict) -> dict:
    notify_url = f"{AIFORGE_BASE_URL}/api/pay/notify"
    return_url = f"{AIFORGE_BASE_URL}/api/pay/return"
    params = {
        "pid": PAY_PID,
        "type": "alipay",
        "out_trade_no": str(oid),
        "notify_url": notify_url,
        "return_url": return_url,
        "name": f"AiForge-{plan['name']}",
        "money": str(plan["price"]),
    }
    sign_str = "".join(f"{k}={v}&" for k, v in sorted(params.items()) if v) + PAY_KEY
    params["sign"] = hashlib.md5(sign_str.encode()).hexdigest()
    params["sign_type"] = "MD5"
    query = "&".join(f"{k}={v}" for k, v in params.items())
    pay_url = f"{PAY_URL}/submit.php?{query}"
    return {"order_id": oid, "pay_url": pay_url, "status": "pending"}


def _create_xunhu(oid: int, plan: dict) -> dict:
    notify_url = f"{PAY_URL}/api/pay/notify"
    return_url = f"{PAY_URL}/api/pay/return"
    params = {
        "appid": PAY_PID,
        "out_trade_no": str(oid),
        "total_fee": str(plan["price"]),
        "notify_url": notify_url,
        "return_url": return_url,
        "title": f"AiForge-{plan['name']}",
        "time": str(int(time.time())),
    }
    sign_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()) if v) + PAY_KEY
    params["hash"] = hashlib.md5(sign_str.encode()).hexdigest()
    pay_url = f"https://api.xunhupay.com/payment/do.html?{ '&'.join(f'{k}={v}' for k, v in params.items())}"
    return {"order_id": oid, "pay_url": pay_url, "status": "pending"}


@router.api_route("/notify", methods=["GET", "POST"])
async def notify(request: Request):
    try:
        body = {}
        try:
            raw = await request.body()
            if raw:
                import json as _json
                body = _json.loads(raw)
        except Exception:
            body = {}
        form = dict(request.query_params)
        if not form and not body:
            return "no data"

        # 收钱吧回调
        if body and isinstance(body, dict) and ("order_status" in body or "terminal_sn" in body):
            result = handle_sqb_callback(body)
            if result.get("status") == "paid":
                try:
                    pay_order(result["order_id"], result.get("trade_no", f"sqb_{result['order_id']}"))
                    print(f"[Payment] SQB callback: paid order #{result['order_id']}")
                except Exception as e:
                    print(f"[Payment] SQB callback pay_order failed: {e}")
            return "success"

        if body and isinstance(body, dict) and ("amount" in body or "money" in body or "price" in body):
            return _handle_free_sign_notify(body)

        sign = form.pop("sign", form.pop("hash", ""))
        form.pop("sign_type", None)
        trade_no = form.get("trade_no", form.get("transaction_id", ""))
        out_trade_no = form.get("out_trade_no", "")

        if PAY_KEY:
            sign_str = "".join(f"{k}={v}" for k, v in sorted(form.items()) if v and k not in ("sign", "hash", "sign_type")) + PAY_KEY
            expected = hashlib.md5(sign_str.encode()).hexdigest()
            if sign != expected:
                return "sign error"

        trade_status = form.get("trade_status", form.get("status", ""))
        if trade_status in ("TRADE_SUCCESS", "OD"):
            try:
                pay_order(int(out_trade_no), trade_no)
            except Exception:
                pass
        return "success"
    except Exception as e:
        print(f"[Payment] notify error: {e}")
        return "error"


def _handle_free_sign_notify(data: dict) -> str:
    amount = float(data.get("amount", data.get("money", data.get("price", 0))))
    key = data.get("key", data.get("sign", ""))
    if PAY_NOTIFY_KEY and key:
        expected = hashlib.md5(f"{amount}{PAY_NOTIFY_KEY}".encode()).hexdigest()
        if key != expected:
            print(f"[Payment] free-sign notify: key mismatch amount={amount}")
            return "key error"

    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, user_id, amount, status FROM orders WHERE status='pending' ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    conn.close()

    matched = None
    for row in rows:
        order_amount = float(row["amount"])
        if abs(order_amount - amount) < 0.05:
            matched = dict(row)
            break
        if abs(order_amount - amount) < 1.0:
            matched = dict(row)

    if matched:
        try:
            pay_order(matched["id"], f"wxqr_{matched['id']}_{amount}")
            print(f"[Payment] free-sign notify: matched order #{matched['id']} amount={amount}")
        except Exception as e:
            print(f"[Payment] free-sign notify: pay_order failed: {e}")
    else:
        print(f"[Payment] free-sign notify: no matching order for amount={amount}")

    return "success"


@router.get("/return")
def pay_return():
    return {"msg": "支付完成，请返回查看余额"}


@router.get("/order/{oid}")
def order_status(oid: int, user: dict = Depends(auth_required)):
    conn = _get_conn()
    row = conn.execute("SELECT * FROM orders WHERE id=? AND user_id=?", (oid, user["id"])).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "订单不存在")
    result = dict(row)
    # 如果还是pending，主动查一下收钱吧
    if result["status"] == "pending" and os.environ.get("SQB_VENDOR_SN"):
        sqb_result = query_sqb_order(oid)
        if sqb_result and sqb_result.get("status") == "paid":
            try:
                pay_order(oid, sqb_result.get("trade_no", f"sqb_{oid}"))
                result["status"] = "paid"
                print(f"[Payment] SQB poll: paid order #{oid}")
            except Exception:
                pass
    return result


@router.get("/orders")
def my_orders(user: dict = Depends(auth_required)):
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, plan_id, amount, points, status, created_at, paid_at FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 20",
        (user["id"],)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/alipay/notify")
async def alipay_notify(request: Request):
    """支付宝异步通知（服务器对服务器）"""
    form = dict(await request.form())
    if not form:
        body = await request.body()
        try:
            form = json.loads(body)
        except Exception:
            form = {}
    result = verify_alipay_notify(form)
    if result.get("verified") and result.get("status") == "paid":
        return "success"
    return "failure"


@router.get("/alipay/return")
def alipay_return():
    """支付宝同步跳转（用户付款后跳回）"""
    return HTMLResponse("""
    <!DOCTYPE html><html><head><meta charset="utf-8">
    <title>支付成功</title>
    <meta http-equiv="refresh" content="3;url=/">
    <style>body{background:#0a0a0f;color:#e2e8f0;display:flex;align-items:center;justify-content:center;min-height:100vh;font-family:sans-serif;text-align:center}
    h1{color:#22c55e;font-size:24px}.p{color:#64748b;font-size:14px}</style></head>
    <body><div><h1>✓ 支付成功</h1><p class="p">积分已到账，3秒后跳转...</p></div></body></html>
    """)
