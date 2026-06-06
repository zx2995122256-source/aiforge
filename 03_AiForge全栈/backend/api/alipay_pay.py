import os
import time
import json
from urllib.parse import quote
from fastapi import HTTPException
from models.db import pay_order

ALIPAY_APP_ID = os.environ.get("ALIPAY_APP_ID", "")

def _read_key(key_var: str) -> str:
    """Read key from env var or from file path in env var."""
    val = os.environ.get(key_var, "")
    if not val:
        return ""
    if val.startswith("file:"):
        fpath = val[5:]
        if os.path.isfile(fpath):
            with open(fpath) as f:
                return f.read().strip()
        return ""
    if "-----BEGIN" in val:
        return val
    # Might be raw base64, try to construct PEM format
    if not val.startswith("MII"):
        return val
    # Check if it's a private key or public key
    key_type = "RSA PRIVATE KEY" if val.startswith("MIIEv") else "PUBLIC KEY"
    formatted = f"-----BEGIN {key_type}-----\n"
    for i in range(0, len(val), 64):
        formatted += val[i:i+64] + "\n"
    formatted += f"-----END {key_type}-----"
    return formatted

ALIPAY_PRIVATE_KEY = _read_key("ALIPAY_PRIVATE_KEY")
ALIPAY_PUBLIC_KEY = _read_key("ALIPAY_PUBLIC_KEY")
ALIPAY_GATEWAY = "https://openapi.alipay.com/gateway.do"
AIFORGE_BASE_URL = os.environ.get("AIFORGE_BASE_URL", "http://122.51.205.94")

_ali_pay = None


def _get_alipay():
    global _ali_pay
    if _ali_pay is not None:
        return _ali_pay
    if not ALIPAY_APP_ID or not ALIPAY_PRIVATE_KEY:
        return None
    from alipay import AliPay
    _ali_pay = AliPay(
        appid=ALIPAY_APP_ID,
        app_notify_url=None,
        app_private_key_string=ALIPAY_PRIVATE_KEY,
        alipay_public_key_string=ALIPAY_PUBLIC_KEY,
        sign_type="RSA2",
        debug=False,
    )
    return _ali_pay


def create_alipay_order(oid: int, plan: dict) -> dict:
    alipay = _get_alipay()
    if not alipay:
        raise HTTPException(503, "支付宝支付暂未配置")

    notify_url = f"{AIFORGE_BASE_URL}/api/pay/alipay/notify"
    return_url = f"{AIFORGE_BASE_URL}/api/pay/alipay/return"
    order_string = alipay.api_alipay_trade_page_pay(
        out_trade_no=str(oid),
        total_amount=plan["price"],
        subject=f"AiForge-{plan['name']}",
        return_url=return_url,
        notify_url=notify_url,
    )
    pay_url = f"{ALIPAY_GATEWAY}?{order_string}"
    return {"order_id": oid, "pay_url": pay_url, "status": "pending", "pay_method": "alipay"}


def verify_alipay_notify(data: dict) -> dict:
    """Verify and process Alipay async notification."""
    alipay = _get_alipay()
    if not alipay:
        raise HTTPException(500, "支付宝未配置")

    sign = data.pop("sign", "")
    sign_type = data.pop("sign_type", "")
    data["sign"] = sign
    data["sign_type"] = sign_type

    verified = alipay.verify(data, sign)
    if not verified:
        return {"verified": False, "msg": "sign verification failed"}

    trade_status = data.get("trade_status", "")
    out_trade_no = data.get("out_trade_no", "")
    trade_no = data.get("trade_no", "")
    total_amount = data.get("total_amount", "0")

    if trade_status == "TRADE_SUCCESS":
        try:
            oid = int(out_trade_no)
            pay_order(oid, trade_no)
            print(f"[Alipay] paid: order={oid} trade_no={trade_no} amount={total_amount}")
            return {"verified": True, "order_id": oid, "status": "paid"}
        except Exception as e:
            print(f"[Alipay] pay failed: {e}")
            return {"verified": True, "order_id": 0, "status": "error", "msg": str(e)}

    return {"verified": True, "order_id": 0, "status": trade_status}