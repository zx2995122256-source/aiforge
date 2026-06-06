# 锤子Aicg — AI 视频/图片生成平台

## 项目简介

锤子Aicg 是一个基于第三方 AI 模型 API（oiioii.ai）的图片与视频生成平台。  
提供 Web 前端操作界面 + 后端任务调度 + 账号池管理三位一体服务。

**生产环境：** [http://122.51.205.94](http://122.51.205.94)  
**架构：** 前端(Vue3) + 后端(FastAPI) + 账号池(OiioiiPool)

---

## 目录结构

```
锤子Aicg/
├── README.md                          ← 本文件（项目总文档）
│
├── 01_项目概述/                        ← 架构图、需求文档
│
├── 02_腾讯云服务器/                     ← 服务器配置
│   ├── keys/ssh_key.pem               ← SSH 私钥
│   ├── aiforge.service                ← AiForge systemd 服务文件
│   ├── oiioii.service                 ← OiioiiPool systemd 服务文件
│   ├── nginx_aiforge.conf             ← Nginx 反向代理配置
│   ├── 服务器信息.txt                   ← 系统规格
│   ├── aiforge_main.py                ← 服务器端 AiForge 入口文件（参考）
│   └── aiforge_config.py              ← 服务器端 AiForge 配置（参考）
│
├── 03_AiForge全栈/                     ← 主项目（前后端一体）
│   ├── backend/                       ← FastAPI 后端
│   │   ├── main.py                    ← 入口（启动 Uvicorn）
│   │   ├── config.py                  ← 配置（端口、积分定价、模型定价）
│   │   ├── admin.py                   ← 管理后台路由
│   │   ├── api/
│   │   │   ├── auth.py                ← 注册/登录/用户信息
│   │   │   ├── generate.py            ← 文生图/文生视频/文件代理/任务查询
│   │   │   ├── payment.py             ← 支付集成
│   │   │   ├── pool.py                ← 账号池状态 API
│   │   │   └── user.py                ← 用户积分/兑换码
│   │   ├── core/
│   │   │   └── proxy.py               ← OiioiiPool 通信封装
│   │   └── models/
│   │       └── db.py                  ← 数据库操作（SQLite）
│   │
│   └── frontend/                      ← Vue3 前端
│       ├── src/
│       │   ├── api/index.ts           ← API 调用封装
│       │   ├── components/            ← 通用组件
│       │   ├── composables/           ← 组合式函数（主题等）
│       │   ├── lib/utils.ts           ← 工具函数
│       │   ├── pages/                 ← 页面组件
│       │   ├── router/index.ts        ← 路由
│       │   ├── stores/                ← Pinia 状态管理
│       │   │   ├── auth.ts            ← 认证状态
│       │   │   ├── gallery.ts         ← 画廊状态
│       │   │   ├── generate.ts        ← 生成任务状态
│       │   │   └── theme.ts           ← 主题状态
│       │   ├── views/                 ← 页面视图
│       │   │   ├── Login.vue          ← 登录页
│       │   │   ├── Workspace.vue      ← 工作台（生成页）
│       │   │   ├── Gallery.vue        ← 作品展示
│       │   │   ├── Pricing.vue        ← 套餐定价
│       │   │   ├── Admin.vue          ← 管理后台
│       │   │   └── HomePage.vue       ← 首页
│       │   ├── App.vue
│       │   ├── main.ts
│       │   └── style.css
│       ├── package.json
│       ├── vite.config.ts
│       ├── tsconfig.json
│       ├── tailwind.config.js
│       └── index.html
│
├── 04_OiioiiPool账号池/                ← AI 账号池（核心引擎）
│   ├── main.py                        ← 入口
│   ├── config.py                      ← 配置（API地址、模型列表、定价）
│   ├── config.ini                     ← 可配置项（端口、隧道）
│   ├── requirements.txt
│   ├── start.bat / 启动.bat            ← 本地启动脚本
│   ├── api/
│   │   └── server.py                  ← FastAPI 路由（上传/生成/任务查询）
│   └── core/
│       ├── client.py                  ← 账号客户端（登录/提交/轮询/文件上传）
│       ├── db.py                      ← 数据库操作（账号管理、积分管理）
│       ├── engine.py                  ← 任务引擎（提交→轮询→下载全流程）
│       ├── pool.py                    ← 账号池管理（取号、注册、刷新）
│       └── registrar.py               ← 自动注册新账号
│
├── 05_数据库/                          ← 数据库结构说明
│
├── 06_运维脚本/                        ← 部署和维护脚本
│   ├── 部署/                          ← 部署到服务器用的脚本
│   └── 维护/                          ← 日常维护脚本
│
└── 07_归档_临时脚本/                   ← 历史临时测试脚本（可安全删除）
```

---

## 架构全景

```
用户浏览器
    │
    ├── http://122.51.205.94:80
    │       │
    │       ├── Nginx (端口 80)
    │       │   ├── / → 静态文件 (/home/ubuntu/aiforge/dist)
    │       │   └── /api/* → proxy_pass → localhost:7862
    │       │
    │       └── AiForge 后端 (端口 7862)
    │               ├── FastAPI + Uvicorn
    │               ├── SQLite 数据库 (aiforge.db)
    │               │   ├── users 表 — 用户/积分/角色
    │               │   └── tasks 表 — 任务记录
    │               └── OiioiiProxy → OiioiiPool (localhost:7861)
    │
    └── OiioiiPool (端口 7861)
            ├── FastAPI + Uvicorn
            ├── SQLite 数据库 (oiioii_pool.db)
            │   ├── accounts 表 — 约 290 个 AI 账号
            │   └── tasks 表 — 任务队列
            ├── 账号池管理（轮询取号、积分管理）
            ├── 任务引擎（提交→轮询→下载）
            └── → 外部 API (api.oiioii.ai)
```

---

## 部署指南

### 连接服务器

```bash
ssh -i "02_腾讯云服务器/keys/ssh_key.pem" ubuntu@122.51.205.94
```

### 服务管理

```bash
# 查看状态
sudo systemctl status aiforge
sudo systemctl status oiioii

# 重启
sudo systemctl restart aiforge
sudo systemctl restart oiioii

# 查看日志
sudo journalctl -u aiforge -n 50 --no-pager
sudo journalctl -u oiioii -n 50 --no-pager
```

### 代码部署

服务器源码路径：
- AiForge: `/home/ubuntu/aiforge/`
- OiioiiPool: `/home/ubuntu/oiioii/`
- Nginx 配置: `/etc/nginx/sites-enabled/aiforge`

部署方式：本地修改后打包 tar.gz → scp 到服务器 → 解压覆盖 → 重启服务

---

## 核心数据流

### 用户提交图片生成
```
用户 → 前端表单 → POST /api/gen/image
    → AiForge 后端 (generate.py)
        → 验证积分、创建任务记录
        → proxy.generate_image() → OiioiiPool
            → engine.submit("image", ...)
                → 选号（优先低分账号）
                → client.generate_image() → api.oiioii.ai
                → 轮询结果 → 下载文件
            → 返回 task_id
        → 启动后台线程轮询 OiioiiPool
        → 完成时更新 task 状态 + 返回文件 URL
```

### 用户提交视频生成
```
用户 → 前端表单 → POST /api/gen/video
    → 流程同上，但：
        → 选号（优先高分账号，最低60分）
        → 可传参考图片 + 参考视频
        → 参考视频上传存本地磁盘（不走外部API）
        → 参考图片 → base64 嵌入请求
        → 超时最长 1800s（含参考视频时）
```

---

## 账号池分配策略 (OiioiiPool)

| 任务类型 | 选号策略 | 最低积分要求 |
|---------|---------|------------|
| 图片 | 积分最低但够用的账号 | `= 费用` |
| 视频 | 积分最高的账号 | `max(费用, 60)` |

实现文件：[core/db.py](file:///C:/Users/Administrator/Documents/锤子Aicg/04_OiioiiPool账号池/core/db.py) 的 `get_available()` 方法

---

## 数据库

### AiForge (`aiforge.db`)

**users 表：** id, email, password_hash, nickname, points, role, created_at, updated_at

**tasks 表：** id, user_id, task_type, model, prompt, status, points_cost, oiioii_task_id, result_url, created_at, completed_at

### OiioiiPool (`oiioii_pool.db`)

**accounts 表：** id, email, password, token, points, points_remaining, workspace_id, status, last_used

**tasks 表：** id, account_id, task_type, model_name, prompt, status, task_id(remote), result_uri, local_path, points_cost, created_at

---

## 关键端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Nginx | 80 | 公网入口 |
| AiForge | 7862 | 主后端 |
| OiioiiPool | 7861 | 账号池 |
| 前端开发 | 5173 | Vite 开发服务器 |

---

## 管理员账号

- **邮箱：** `xiaye@aiforge.com`
- **密码：** `zx4579561`
- **角色：** admin
- **积分：** 99,999

---

## 本地开发

### 启动方式

```powershell
# 1. 启动 OiioiiPool（端口 7861）
cd OiioiiPool
python main.py

# 2. 启动 AiForge 后端（端口 7862）
cd AiForge/backend
python main.py

# 3. 启动前端开发服务器（端口 5173）
cd AiForge/frontend
npm run dev
```

浏览器打开 http://localhost:5173

---

## 常见问题

1. **参考视频上传失败？** 检查 OiioiiPool 是否在运行。视频存本地不走外部 API，大小上限 100MB
2. **任务一直 processing？** 重启服务：`sudo systemctl restart oiioii`
3. **账号积分用完了？** OiioiiPool 会自动注册新账号
4. **Nginx 502？** 检查 AiForge 后端是否在运行（端口 7862）
