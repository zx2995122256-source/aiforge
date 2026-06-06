import os
import sys
import time
import sqlite3
from fastapi import APIRouter, FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from config import DB_PATH, OIIOII_API, PLANS
from models.db import (
    get_user, get_all_users, add_points, create_redeem_code,
    _get_conn,
)
from api.auth import auth_required

router = APIRouter(prefix="/admin")

ADMIN_PASSWORD = os.environ.get("AIFORGE_ADMIN_PW", "aiforge2026")


def _admin_auth(request: Request):
    auth = request.headers.get("X-Admin-Key", "") or request.query_params.get("key", "")
    if auth != ADMIN_PASSWORD:
        raise HTTPException(401, "管理密钥错误")
    return True


def _oiioii_request(path: str, method: str = "GET", json_body: dict = None, timeout: int = 10):
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
            return None
        if r.status_code == 200:
            return r.json()
        return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"error": str(e)}


@router.get("/")
def admin_index(key: str = ""):
    if key != ADMIN_PASSWORD:
        return HTMLResponse("<h1>403 Forbidden</h1>", status_code=403)
    return HTMLResponse(ADMIN_HTML, headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"})


@router.get("/api/dashboard")
def dashboard(auth=Depends(_admin_auth)):
    conn = _get_conn()
    now = time.time()
    day_ago = now - 86400
    week_ago = now - 86400 * 7

    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    new_users_today = conn.execute("SELECT COUNT(*) FROM users WHERE created_at>?", (day_ago,)).fetchone()[0]
    new_users_week = conn.execute("SELECT COUNT(*) FROM users WHERE created_at>?", (week_ago,)).fetchone()[0]

    total_tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    tasks_today = conn.execute("SELECT COUNT(*) FROM tasks WHERE created_at>?", (day_ago,)).fetchone()[0]
    completed_today = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='completed' AND finished_at>?", (day_ago,)).fetchone()[0]
    failed_today = conn.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('failed','timeout') AND finished_at>?", (day_ago,)).fetchone()[0]

    points_consumed_today = conn.execute(
        "SELECT COALESCE(SUM(ABS(amount)),0) FROM point_logs WHERE amount<0 AND created_at>?", (day_ago,)
    ).fetchone()[0]
    points_recharged_today = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM point_logs WHERE amount>0 AND reason LIKE '%购买套餐%' AND created_at>?", (day_ago,)
    ).fetchone()[0]

    revenue_today = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM orders WHERE status='paid' AND paid_at>?", (day_ago,)
    ).fetchone()[0]
    revenue_week = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM orders WHERE status='paid' AND paid_at>?", (week_ago,)
    ).fetchone()[0]
    revenue_total = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM orders WHERE status='paid'"
    ).fetchone()[0]

    daily_stats = []
    for i in range(7):
        day_start = now - (i + 1) * 86400
        day_end = now - i * 86400
        tasks_count = conn.execute("SELECT COUNT(*) FROM tasks WHERE created_at BETWEEN ? AND ?", (day_start, day_end)).fetchone()[0]
        points_used = conn.execute(
            "SELECT COALESCE(SUM(ABS(amount)),0) FROM point_logs WHERE amount<0 AND created_at BETWEEN ? AND ?", (day_start, day_end)
        ).fetchone()[0]
        revenue = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM orders WHERE status='paid' AND paid_at BETWEEN ? AND ?", (day_start, day_end)
        ).fetchone()[0]
        new_users = conn.execute("SELECT COUNT(*) FROM users WHERE created_at BETWEEN ? AND ?", (day_start, day_end)).fetchone()[0]
        daily_stats.append({
            "date": time.strftime("%m-%d", time.localtime(day_start)),
            "tasks": tasks_count, "points_used": points_used,
            "revenue": revenue, "new_users": new_users,
        })

    pool = _oiioii_request("/api/pool/status")

    conn.close()

    return {
        "users": {"total": total_users, "today": new_users_today, "week": new_users_week},
        "tasks": {"total": total_tasks, "today": tasks_today, "completed": completed_today, "failed": failed_today},
        "points": {"consumed_today": points_consumed_today, "recharged_today": points_recharged_today},
        "revenue": {"today": revenue_today, "week": revenue_week, "total": revenue_total},
        "daily": list(reversed(daily_stats)),
        "pool": pool if not isinstance(pool, dict) or "error" not in pool else {"error": pool.get("error", "unavailable")},
    }


@router.get("/api/users")
def list_users(auth=Depends(_admin_auth), limit: int = 200):
    return get_all_users(limit)


@router.post("/api/users/{uid}/points")
def admin_add_points(uid: int, points: int, reason: str = "管理员调整", auth=Depends(_admin_auth)):
    add_points(uid, points, reason)
    u = get_user(uid)
    return {"uid": uid, "points": u["points"] if u else 0}


@router.get("/api/pool")
def pool_status(auth=Depends(_admin_auth)):
    return _oiioii_request("/api/pool/status")


@router.post("/api/pool/add")
def pool_add(email: str, password: str, auth=Depends(_admin_auth)):
    return _oiioii_request("/api/pool/add", "POST", {"email": email, "password": password})


@router.post("/api/pool/register")
def pool_register(count: int = 1, auth=Depends(_admin_auth)):
    return _oiioii_request("/api/pool/register", "POST", {"count": count})


@router.post("/api/pool/refresh")
def pool_refresh(auth=Depends(_admin_auth)):
    return _oiioii_request("/api/pool/refresh", "POST", timeout=60)


@router.post("/api/pool/continuous_reg")
def pool_continuous_reg(enable: bool = True, target_count: int = 50, auth=Depends(_admin_auth)):
    return _oiioii_request(f"/api/pool/continuous_reg?enable={'true' if enable else 'false'}&target_count={target_count}", "POST", timeout=10)


@router.delete("/api/pool/{account_id}")
def pool_remove(account_id: int, auth=Depends(_admin_auth)):
    return _oiioii_request(f"/api/pool/{account_id}", "DELETE")


@router.post("/api/redeem")
def create_redeem(points: int, auth=Depends(_admin_auth)):
    code = create_redeem_code(points)
    return {"code": code, "points": points}


@router.get("/api/orders")
def list_orders(auth=Depends(_admin_auth), limit: int = 50):
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/api/orders/{oid}/confirm")
def confirm_order(oid: int, auth=Depends(_admin_auth)):
    from models.db import pay_order
    conn = _get_conn()
    row = conn.execute("SELECT status FROM orders WHERE id=?", (oid,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "订单不存在")
    if row["status"] == "paid":
        return {"msg": "订单已确认过"}
    pay_order(oid, f"admin_confirm_{oid}")
    return {"msg": "已确认到账，积分已发放"}


# ==================== Agent Management ====================

@router.post("/api/agent/create")
def admin_create_agent(user_id: int, commission_rate: float = 20.0, auth=Depends(_admin_auth)):
    from models.db import create_agent
    result = create_agent(user_id, commission_rate)
    if not result:
        raise HTTPException(400, "创建失败，用户可能已是代理")
    return {"msg": "代理创建成功", "agent": result}


@router.get("/api/agents")
def admin_get_agents(auth=Depends(_admin_auth)):
    from models.db import get_agents
    return get_agents()


@router.get("/api/agents/{aid}")
def admin_get_agent_detail(aid: int, auth=Depends(_admin_auth)):
    from models.db import get_agent_referrals, get_agent_orders
    return {
        "referrals": get_agent_referrals(aid),
        "orders": get_agent_orders(aid),
    }


@router.post("/api/agents/{aid}/settle")
def admin_settle_agent(aid: int, auth=Depends(_admin_auth)):
    from models.db import settle_agent_commission
    return settle_agent_commission(aid)


# ==================== User-side Agent API ====================

@router.get("/api/my-agent")
def my_agent_info(user: dict = Depends(auth_required)):
    """获取当前用户的代理信息（普通用户可访问）"""
    from models.db import get_agent_by_user_id
    agent = get_agent_by_user_id(user["id"])
    if not agent:
        return {"is_agent": False}
    return {
        "is_agent": True,
        "invite_code": agent["invite_code"],
        "invite_link": f"/register?ref={agent['invite_code']}",
        "commission_rate": agent["commission_rate"],
        "total_referrals": agent["total_referrals"],
        "total_commission": agent["total_commission"],
        "settled_commission": agent["settled_commission"],
        "unsettled_commission": round(agent["total_commission"] - agent["settled_commission"], 2),
    }


@router.get("/api/my-agent/referrals")
def my_agent_referrals(user: dict = Depends(auth_required)):
    """获取当前代理的邀请列表"""
    from models.db import get_agent_by_user_id, get_agent_referrals
    agent = get_agent_by_user_id(user["id"])
    if not agent:
        raise HTTPException(403, "您不是代理")
    return get_agent_referrals(agent["id"])


@router.get("/api/my-agent/orders")
def my_agent_orders(user: dict = Depends(auth_required)):
    """获取当前代理的佣金订单"""
    from models.db import get_agent_by_user_id, get_agent_orders
    agent = get_agent_by_user_id(user["id"])
    if not agent:
        raise HTTPException(403, "您不是代理")
    return get_agent_orders(agent["id"])


ADMIN_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>AiForge Admin</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
body{background:#0a0a0f;color:#e2e8f0;font-family:'Noto Sans SC',system-ui,sans-serif;margin:0}
.glass{background:rgba(26,26,46,.6);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:20px}
.stat{background:#111127;border-radius:10px;padding:14px;text-align:center}
.stat .val{font-size:24px;font-weight:700;font-family:Outfit,system-ui}
.stat .lbl{font-size:11px;color:#64748b;margin-top:4px}
.btn{padding:6px 16px;border-radius:8px;font-size:13px;cursor:pointer;transition:all .2s;display:inline-flex;align-items:center;gap:4px}
.btn-p{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border:none}
.btn-p:hover{opacity:.85}
.btn-s{background:rgba(99,102,241,.15);color:#818cf8;border:1px solid rgba(99,102,241,.3)}
.btn-s:hover{background:rgba(99,102,241,.25)}
.btn-d{background:rgba(239,68,68,.15);color:#f87171;border:1px solid rgba(239,68,68,.3)}
.btn-g{background:rgba(34,197,94,.15);color:#22c55e;border:1px solid rgba(34,197,94,.3)}
.inp{background:#111127;border:1px solid rgba(255,255,255,.08);border-radius:8px;padding:8px 12px;color:#e2e8f0;font-size:13px;width:100%;box-sizing:border-box}
.inp:focus{outline:none;border-color:#6366f1}
table{width:100%;font-size:13px;border-collapse:collapse}
th{text-align:left;color:#64748b;padding:6px 10px;border-bottom:1px solid rgba(255,255,255,.06);font-weight:500;font-size:12px}
td{padding:6px 10px;border-bottom:1px solid rgba(255,255,255,.04)}
.badge{padding:2px 8px;border-radius:6px;font-size:11px}
.badge-g{background:rgba(34,197,94,.15);color:#22c55e}
.badge-y{background:rgba(245,158,11,.15);color:#f59e0b}
.badge-r{background:rgba(239,68,68,.15);color:#f87171}
.tab{padding:6px 16px;cursor:pointer;border-bottom:2px solid transparent;color:#64748b;transition:all .2s;font-size:13px;white-space:nowrap}
.tab.active{color:#818cf8;border-bottom-color:#6366f1}
.section{display:none}.section.active{display:block}
.toggle{cursor:pointer;user-select:none;transition:transform .2s}
.toggle.open{transform:rotate(90deg)}
</style>
</head>
<body>
<div id="app" style="max-width:1200px;margin:0 auto;padding:16px">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
    <h1 style="font-family:Outfit;font-size:22px;font-weight:700;background:linear-gradient(135deg,#6366f1,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent">AiForge Admin</h1>
    <div style="display:flex;align-items:center;gap:12px">
      <span id="pool-status-dot" style="width:8px;height:8px;border-radius:50%;display:inline-block;background:#22c55e"></span>
      <span style="color:#64748b;font-size:13px" id="clock"></span>
    </div>
  </div>

  <div id="stats" style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px"></div>

  <div style="display:flex;gap:4px;margin-bottom:16px;border-bottom:1px solid rgba(255,255,255,.06);overflow-x:auto">
    <div class="tab active" onclick="switchTab('pool',this)">账号池</div>
    <div class="tab" onclick="switchTab('users',this)">用户</div>
    <div class="tab" onclick="switchTab('orders',this)">订单</div>
    <div class="tab" onclick="switchTab('redeem',this)">兑换码</div>
    <div class="tab" onclick="switchTab('daily',this)">日报</div>
    <div class="tab" id="tab-agents" onclick="switchTab('agents',this)">代理</div>
  </div>

  <!-- ====== Pool Tab ====== -->
  <div id="sec-pool" class="section active">
    <div class="glass" style="padding:16px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px">
        <h2 style="font-size:15px;font-weight:600">账号池</h2>
        <div style="display:flex;gap:6px;flex-wrap:wrap">
          <div style="display:flex;align-items:center;gap:4px">
            <input class="inp" id="batch-count" type="number" value="10" min="1" max="100" style="width:60px;padding:4px 8px;text-align:center">
            <button class="btn btn-p" onclick="batchRegister()">批量注册</button>
          </div>
          <button class="btn btn-s" onclick="toggleContinuousReg()" id="cont-reg-btn">🔄 连续注册</button>
          <button class="btn btn-s" onclick="refreshPool()">刷新</button>
        </div>
      </div>

      <div id="pool-stats" style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:12px"></div>

      <div id="reg-progress" style="display:none;margin-bottom:12px">
        <div style="display:flex;justify-content:space-between;font-size:12px;color:#94a3b8;margin-bottom:4px">
          <span id="reg-status-text">注册中...</span>
          <span id="reg-progress-text">0/0</span>
        </div>
        <div style="background:#111127;border-radius:6px;height:6px;overflow:hidden">
          <div id="reg-progress-bar" style="background:linear-gradient(135deg,#6366f1,#8b5cf6);height:100%;width:0%;border-radius:6px;transition:width .3s"></div>
        </div>
      </div>

      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
        <span class="toggle" id="pool-toggle" onclick="togglePoolList()">▶</span>
        <span style="font-size:13px;color:#94a3b8;cursor:pointer" onclick="togglePoolList()">查看账号列表（<span id="pool-count-label">0</span>个）</span>
      </div>
      <div id="pool-list" style="display:none;max-height:300px;overflow-y:auto">
        <table style="font-size:12px"><thead><tr><th>ID</th><th>邮箱</th><th>积分</th><th>状态</th><th>操作</th></tr></thead>
        <tbody id="pool-table"></tbody></table>
      </div>

      <div style="margin-top:12px;padding-top:12px;border-top:1px solid rgba(255,255,255,.06);display:flex;gap:8px;flex-wrap:wrap">
        <input class="inp" id="add-email" placeholder="邮箱" style="flex:1;min-width:150px">
        <input class="inp" id="add-pw" placeholder="密码" style="flex:1;min-width:150px">
        <button class="btn btn-p" onclick="addAccount()">手动添加</button>
      </div>
    </div>
  </div>

  <!-- ====== Users Tab ====== -->
  <div id="sec-users" class="section">
    <div class="glass" style="padding:16px">
      <h2 style="font-size:15px;font-weight:600;margin-bottom:12px">用户管理</h2>
      <div style="max-height:500px;overflow-y:auto">
        <table><thead><tr><th>用户ID</th><th>邮箱</th><th>昵称</th><th>积分</th><th>角色</th><th>操作</th></tr></thead>
        <tbody id="users-table"></tbody></table>
      </div>
    </div>
  </div>

  <!-- ====== Orders Tab ====== -->
  <div id="sec-orders" class="section">
    <div class="glass" style="padding:16px">
      <h2 style="font-size:15px;font-weight:600;margin-bottom:12px">订单记录</h2>
      <div style="max-height:500px;overflow-y:auto">
        <table><thead><tr><th>ID</th><th>用户</th><th>套餐</th><th>金额</th><th>积分</th><th>状态</th><th>时间</th></tr></thead>
        <tbody id="orders-table"></tbody></table>
      </div>
    </div>
  </div>

  <!-- ====== Redeem Tab ====== -->
  <div id="sec-redeem" class="section">
    <div class="glass" style="padding:16px">
      <h2 style="font-size:15px;font-weight:600;margin-bottom:12px">兑换码生成</h2>
      <div style="display:flex;gap:8px;align-items:end;flex-wrap:wrap">
        <div><label style="font-size:12px;color:#64748b">积分数量</label><input class="inp" id="redeem-pts" type="number" value="500" style="width:120px"></div>
        <button class="btn btn-p" onclick="genRedeem()">生成</button>
      </div>
      <div id="redeem-result" style="margin-top:12px;display:none" class="stat">
        <div class="lbl">兑换码</div>
        <div class="val" id="redeem-code" style="color:#818cf8;font-size:18px;word-break:break-all"></div>
        <button class="btn btn-s" style="margin-top:6px" onclick="copyRedeem()">复制</button>
      </div>
    </div>
  </div>

  <!-- ====== Daily Tab ====== -->
  <div id="sec-daily" class="section">
    <div class="glass" style="padding:16px">
      <h2 style="font-size:15px;font-weight:600;margin-bottom:12px">近7日数据</h2>
      <table><thead><tr><th>日期</th><th>新用户</th><th>任务数</th><th>消耗积分</th><th>收入</th></tr></thead>
      <tbody id="daily-table"></tbody></table>
    </div>
  </div>

  <!-- ====== Agents Tab ====== -->
  <div id="sec-agents" class="section">
    <div class="glass" style="padding:16px">
      <h2 style="font-size:15px;font-weight:600;margin-bottom:12px">代理管理</h2>

      <div style="display:flex;gap:8px;margin-bottom:12px;align-items:center;flex-wrap:wrap">
        <input id="agent-uid" class="inp" style="width:120px" placeholder="用户数字ID" type="number" />
        <span id="agent-uid-label" style="font-size:12px;color:#818cf8;min-width:100px"></span>
        <input id="agent-rate" class="inp" style="width:80px" value="20" placeholder="佣金%" type="number" />
        <button class="btn btn-p" onclick="createAgent()">设为代理</button>
        <button class="btn btn-s" onclick="loadAgents()">刷新</button>
        <span style="font-size:11px;color:#64748b">可在用户列表中直接点"设为代理"按钮</span>
      </div>

      <table><thead><tr>
        <th>ID</th><th>邀请码</th><th>用户</th><th>积分</th><th>佣金%</th>
        <th>邀请人数</th><th>总佣金</th><th>已结算</th><th>未结算</th><th>操作</th>
      </tr></thead>
      <tbody id="agent-table"></tbody></table>

      <div id="agent-detail" style="display:none;margin-top:16px"></div>
    </div>
  </div>
</div>

<script>
const KEY='aiforge2026';
function ak(path){const sep=path.includes('?')?'&':'?';return '/admin/api'+path+sep+'key='+KEY;}

let poolData = null;

function fmt(ts){if(!ts)return'-';const d=new Date(ts*1000);return d.toLocaleDateString('zh-CN')+' '+d.toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'})}
function fmtMoney(v){return '¥'+(v||0).toFixed(2)}

async function loadDashboard(){
  try{
    const d=await fetch(ak('/dashboard')).then(r=>r.json());
    const s=document.getElementById('stats');
    s.innerHTML=[
      {v:d.users.total,l:'总用户',c:'#818cf8'},
      {v:d.tasks.today,l:'今日任务',c:'#22c55e'},
      {v:fmtMoney(d.revenue.today),l:'今日收入',c:'#f59e0b'},
      {v:d.pool?.total_accounts||0,l:'账号池',c:'#818cf8'},
    ].map(x=>'<div class="stat"><div class="val" style="color:'+x.c+'">'+x.v+'</div><div class="lbl">'+x.l+'</div></div>').join('');

    const pool=d.pool||{};
    poolData = pool;
    const ps=document.getElementById('pool-stats');
    if(pool.error){
      ps.innerHTML='<div style="color:#f87171;font-size:13px;grid-column:1/-1">账号池: '+pool.error+'</div>';
      document.getElementById('pool-status-dot').style.background='#f87171';
    }else{
      const isRegRunning = pool.continuous_reg_running;
      document.getElementById('pool-status-dot').style.background=isRegRunning?'#22c55e':'#f59e0b';
      const regBtn = document.getElementById('cont-reg-btn');
      regBtn.textContent = isRegRunning ? '⏹ 停止连续注册' : '▶ 启动连续注册';
      regBtn.className = isRegRunning ? 'btn btn-d' : 'btn btn-g';
      ps.innerHTML=[
        {v:pool.total_accounts||0,l:'总账号',c:'#818cf8'},
        {v:pool.active_accounts||0,l:'活跃',c:'#22c55e'},
        {v:pool.total_points||0,l:'总积分',c:'#f59e0b'},
        {v:isRegRunning?'运行中':'已停止',l:'连续注册',c:isRegRunning?'#22c55e':'#f59e0b'},
      ].map(x=>'<div class="stat"><div class="val" style="color:'+x.c+'">'+x.v+'</div><div class="lbl">'+x.l+'</div></div>').join('');
      const accounts = pool.accounts||[];
      document.getElementById('pool-count-label').textContent = accounts.length;
      if(document.getElementById('pool-list').style.display !== 'none'){
        loadPoolTable(accounts);
      }
    }
    loadUsersTable();
    loadOrders();
    loadDaily(d.daily||[]);
  }catch(e){console.error(e)}
}

function togglePoolList(){
  const list=document.getElementById('pool-list');
  const tog=document.getElementById('pool-toggle');
  const show=list.style.display!=='block';
  list.style.display=show?'block':'none';
  tog.classList.toggle('open',show);
  if(show && poolData && poolData.accounts){
    loadPoolTable(poolData.accounts);
  }
}

function loadPoolTable(accounts){
  const tb=document.getElementById('pool-table');
  tb.innerHTML=accounts.map(a=>'<tr>'+
    '<td style="color:#64748b">'+a.id+'</td><td>'+a.email+'</td>'+
    '<td style="color:'+(a.points<60?'#f87171':'#818cf8')+'">'+a.points+(a.points<60?' <span class="badge badge-r">仅生图</span>':'')+'</td>'+
    '<td><span class="badge '+(a.status==='active'?'badge-g':a.status==='exhausted'?'badge-y':'badge-r')+'">'+(a.status==='active'?'活跃':a.status==='exhausted'?'耗尽':'异常')+'</span></td>'+
    '<td><button class="btn btn-d" style="padding:2px 8px;font-size:11px" onclick="removeAccount('+a.id+')">删除</button></td>'+
  '</tr>').join('')
}

async function loadUsersTable(){
  try{
    const users=await fetch(ak('/users')).then(r=>r.json());
    document.getElementById('users-table').innerHTML=users.map(u=>{
      const nn=u.nickname||'';
      const em=u.email||'';
      const safeName=nn.replace(/'/g,"\\'").replace(/"/g,'&quot;');
      const safeEmail=em.replace(/'/g,"\\'").replace(/"/g,'&quot;');
      return '<tr>'+
      '<td style="color:#818cf8;font-weight:700;font-size:15px">#'+u.id+'</td><td>'+em+'</td><td>'+nn+'</td>'+
      '<td style="color:#818cf8">'+u.points+'</td>'+
      '<td><span class="badge '+(u.role==='admin'?'badge-y':'badge-g')+'">'+(u.role==='admin'?'管理员':'用户')+'</span></td>'+
      '<td>'+
        '<button class="btn btn-s" style="padding:2px 8px;font-size:11px" onclick="addPts('+u.id+')">加积分</button>'+
        '<button class="btn btn-p" style="padding:2px 8px;font-size:11px;margin-left:4px" onclick="makeAgent('+u.id+',\''+safeName+'\',\''+safeEmail+'\')">设为代理</button>'+
      '</td>'+
    '</tr>';
    }).join('')
  }catch(e){console.error('loadUsersTable error:',e)}
}

async function loadOrders(){
  try{
    const orders=await fetch(ak('/orders')).then(r=>r.json());
    if(!Array.isArray(orders)){console.error('orders not array:',orders);return}
    document.getElementById('orders-table').innerHTML=orders.map(o=>'<tr>'+
      '<td style="color:#64748b">'+o.id+'</td><td>#'+o.user_id+'</td><td>'+(o.plan_id||'')+'</td>'+
      '<td style="color:#f59e0b">'+fmtMoney(o.amount)+'</td><td style="color:#818cf8">'+(o.points||0)+'</td>'+
      '<td><span class="badge '+(o.status==='paid'?'badge-g':'badge-y')+'">'+(o.status==='paid'?'已付':'待付')+'</span></td>'+
      '<td style="color:#64748b;font-size:12px">'+fmt(o.paid_at||o.created_at)+'</td>'+
      '<td>'+(o.status!=='paid'?'<button class="btn btn-p" onclick="confirmOrder('+o.id+')" style="padding:2px 10px;font-size:11px">确认到账</button>':'')+'</td>'+
    '</tr>').join('')
  }catch(e){console.error('loadOrders error:',e)}
}

async function confirmOrder(oid){
  if(!confirm('确认用户已付款？积分将自动发放。'))return;
  const r=await fetch(ak('/orders/'+oid+'/confirm'),{method:'POST'}).then(r=>r.json());
  alert(r.msg||'操作完成');
  loadOrders();
}

function loadDaily(data){
  document.getElementById('daily-table').innerHTML=data.map(d=>'<tr>'+
    '<td>'+d.date+'</td><td style="color:#818cf8">'+d.new_users+'</td>'+
    '<td style="color:#22c55e">'+d.tasks+'</td><td style="color:#f59e0b">'+d.points_used+'</td>'+
    '<td style="color:#f87171">'+fmtMoney(d.revenue)+'</td>'+
  '</tr>').join('')
}

async function refreshPool(){
  await fetch(ak('/pool/refresh'),{method:'POST'});
  const d=await fetch(ak('/dashboard')).then(r=>r.json());
  poolData = d.pool||{};
  if(poolData.accounts && document.getElementById('pool-list').style.display === 'block'){
    loadPoolTable(poolData.accounts);
  }
  alert('刷新完成');
  loadDashboard();
}

async function batchRegister(){
  const count=parseInt(document.getElementById('batch-count').value)||10;
  if(count<1||count>100){alert('数量1-100');return}
  const p=document.getElementById('reg-progress');
  p.style.display='block';
  document.getElementById('reg-status-text').textContent='正在注册 '+count+' 个账号...';
  document.getElementById('reg-progress-text').textContent='0/'+count;
  document.getElementById('reg-progress-bar').style.width='0%';
  let done=0,failed=0;
  for(let i=0;i<count;i++){
    try{
      const r=await fetch(ak('/pool/register?count=1'),{method:'POST'}).then(r=>r.json());
      if(r.status==='running'||r.job_id){done++}else{failed++}
    }catch(e){failed++}
    document.getElementById('reg-progress-text').textContent=(done+failed)+'/'+count;
    document.getElementById('reg-progress-bar').style.width=((done+failed)/count*100)+'%';
    document.getElementById('reg-status-text').textContent='注册中... 成功'+done+' 失败'+failed;
    await new Promise(r=>setTimeout(r,3000));
  }
  document.getElementById('reg-status-text').textContent='注册完成! 成功'+done+'个, 失败'+failed+'个';
  document.getElementById('reg-progress-bar').style.width='100%';
  setTimeout(()=>{p.style.display='none'},3000);
  loadDashboard();
}

async function toggleContinuousReg(){
  const btn=document.getElementById('cont-reg-btn');
  const isRunning=btn.textContent.includes('停止');
  const action=isRunning?'stop':'start';
  await fetch(ak('/pool/continuous_reg?enable='+(action==='start'?'true':'false')+'&target_count=50'),{method:'POST'}).catch(()=>{});
  alert(action==='start'?'已启动连续注册':'已停止连续注册');
  loadDashboard();
}

async function registerAccount(){
  const r=await fetch(ak('/pool/register?count=1'),{method:'POST'}).then(r=>r.json());
  alert(JSON.stringify(r));
  loadDashboard();
}

async function addAccount(){
  const email=document.getElementById('add-email').value;
  const pw=document.getElementById('add-pw').value;
  if(!email||!pw)return alert('请填写邮箱和密码');
  const r=await fetch(ak('/pool/add?email='+encodeURIComponent(email)+'&password='+encodeURIComponent(pw)),{method:'POST'}).then(r=>r.json());
  alert(JSON.stringify(r));
  document.getElementById('add-email').value='';
  document.getElementById('add-pw').value='';
  loadDashboard();
}

async function removeAccount(id){
  if(!confirm('确定删除账号#'+id+'?'))return;
  await fetch(ak('/pool/'+id),{method:'DELETE'});
  loadDashboard();
}

async function addPts(uid){
  const pts=prompt('输入要增加的积分:');
  if(!pts||isNaN(+pts))return;
  await fetch(ak('/users/'+uid+'/points?points='+pts+'&reason=管理员调整'),{method:'POST'});
  loadUsersTable();
}

async function genRedeem(){
  const pts=document.getElementById('redeem-pts').value;
  const r=await fetch(ak('/redeem?points='+pts),{method:'POST'}).then(r=>r.json());
  document.getElementById('redeem-code').textContent=r.code;
  document.getElementById('redeem-result').style.display='block';
}

function copyRedeem(){
  const code=document.getElementById('redeem-code').textContent;
  navigator.clipboard.writeText(code);
  alert('已复制: '+code);
}

// ====== Agent ======
async function loadAgents(){
  const agents=await fetch(ak('/agents')).then(r=>r.json());
  const html=agents.map(a=>{
    const unsettled=(a.total_commission-a.settled_commission).toFixed(2);
    const inviteLink=location.origin+'/register?ref='+a.invite_code;
    return '<tr>'+
      '<td>'+a.id+'</td>'+
      '<td><span class="badge badge-g" style="cursor:pointer" onclick="copyText(\''+inviteLink+'\')" title="点击复制邀请链接">'+a.invite_code+'</span></td>'+
      '<td>'+a.nickname+'<br><span style="font-size:11px;color:#64748b">'+a.email+'</span></td>'+
      '<td>'+a.points+'</td>'+
      '<td>'+a.commission_rate+'%</td>'+
      '<td>'+a.total_referrals+'</td>'+
      '<td>¥'+a.total_commission.toFixed(2)+'</td>'+
      '<td>¥'+a.settled_commission.toFixed(2)+'</td>'+
      '<td>¥'+unsettled+'</td>'+
      '<td>'+
        '<button class="btn btn-s" style="font-size:11px;padding:4px 10px" onclick="copyText(\''+inviteLink+'\')">复制链接</button>'+
        '<button class="btn btn-s" style="font-size:11px;padding:4px 10px;margin-left:4px" onclick="viewAgent('+a.id+')">详情</button>'+
        (parseFloat(unsettled)>0?'<button class="btn btn-g" style="font-size:11px;padding:4px 10px;margin-left:4px" onclick="settleAgent('+a.id+')">结算</button>':'')+
      '</td></tr>';
  }).join('');
  document.getElementById('agent-table').innerHTML=html||'<tr><td colspan="10" style="text-align:center;color:#64748b;padding:20px">暂无代理</td></tr>';
}

function copyText(text){
  navigator.clipboard.writeText(text).then(()=>alert('已复制邀请链接: '+text)).catch(()=>prompt('请手动复制:',text));
}

function makeAgent(uid, nickname, email){
  // 切到代理tab，自动填入用户ID
  switchTab('agents');
  // 高亮代理tab
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('tab-agents').classList.add('active');
  document.getElementById('agent-uid').value=uid;
  document.getElementById('agent-uid-label').textContent=nickname+' ('+email+')';
  if(confirm('将用户 #'+uid+' ('+nickname+') 设为代理？'))createAgent();
}

async function createAgent(){
  const uid=document.getElementById('agent-uid').value;
  const rate=document.getElementById('agent-rate').value||20;
  if(!uid)return alert('请输入用户ID');
  const r=await fetch(ak('/agent/create?user_id='+uid+'&commission_rate='+rate),{method:'POST'}).then(r=>r.json());
  if(r.error||r.detail)return alert(r.error||r.detail);
  alert('代理创建成功！邀请码: '+r.agent.invite_code);
  document.getElementById('agent-uid').value='';
  loadAgents();
}

async function viewAgent(aid){
  const detail=document.getElementById('agent-detail');
  detail.style.display='block';
  const data=await fetch(ak('/agents/'+aid)).then(r=>r.json());
  let html='<h3 style="font-size:14px;font-weight:600;margin-bottom:8px">邀请详情</h3>';
  html+='<table><thead><tr><th>用户</th><th>注册时间</th><th>积分</th><th>累计消费</th></tr></thead><tbody>';
  for(const u of data.referrals){
    html+='<tr><td>'+u.nickname+'<br><span style="font-size:11px;color:#64748b">'+u.email+'</span></td>'+
      '<td>'+fmt(u.created_at)+'</td><td>'+u.points+'</td><td>¥'+u.total_spent.toFixed(2)+'</td></tr>';
  }
  html+='</tbody></table>';
  html+='<h3 style="font-size:14px;font-weight:600;margin:12px 0 8px">佣金记录</h3>';
  html+='<table><thead><tr><th>订单#</th><th>用户</th><th>金额</th><th>佣金</th><th>时间</th><th>结算</th></tr></thead><tbody>';
  for(const o of data.orders){
    html+='<tr><td>#'+o.id+'</td><td>'+o.user_email+'</td><td>¥'+o.amount.toFixed(2)+'</td>'+
      '<td>¥'+o.commission_amount.toFixed(2)+'</td><td>'+fmt(o.created_at)+'</td>'+
      '<td>'+(o.commission_settled?'<span class="badge badge-g">已结算</span>':'<span class="badge badge-y">未结算</span>')+'</td></tr>';
  }
  html+='</tbody></table>';
  detail.innerHTML=html;
}

async function settleAgent(aid){
  if(!confirm('确认结算该代理的所有未结佣金？'))return;
  const r=await fetch(ak('/agents/'+aid+'/settle'),{method:'POST'}).then(r=>r.json());
  alert(r.ok?'已结算 ¥'+r.amount:'结算失败: '+r.msg);
  loadAgents();
  viewAgent(aid);
}

function switchTab(name, el){
  try {
    document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
    document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
    if(el)el.classList.add('active');
    var sec=document.getElementById('sec-'+name);
    if(sec){sec.classList.add('active')}else{console.error('Section not found: sec-'+name);return}
    if(name==='agents')loadAgents();
    if(name==='users')loadUsersTable();
    if(name==='orders')loadOrders();
  }catch(e){console.error('switchTab error:',e);alert('Tab切换出错: '+e.message)}
}

setInterval(()=>{document.getElementById('clock').textContent=new Date().toLocaleString('zh-CN')},1000);
window.onerror=function(msg,url,line){console.error('JS Error:',msg,'line:',line);return false};
try{loadDashboard();}catch(e){console.error('loadDashboard error:',e);document.getElementById('stats').innerHTML='<div style="color:#f87171">加载失败: '+e.message+'</div>';}
</script>
</body>
</html>"""


if __name__ == "__main__":
    import uvicorn
    _app = FastAPI(title="AiForge Admin", version="1.0.0")
    _app.include_router(router)
    uvicorn.run(_app, host="127.0.0.1", port=7863)
