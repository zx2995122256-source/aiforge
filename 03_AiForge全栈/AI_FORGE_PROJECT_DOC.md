# AiForge 项目完整资料

> 最后更新：2026-06-04
> 编写目的：交接给接手程序员，涵盖服务器、部署、代码结构、已知问题

---

## 一、服务器信息

### 1.1 云服务器

| 项目 | 内容 |
|------|------|
| 服务商 | 腾讯云 |
| 公网IP | `122.51.205.94` |
| 内网IP | `10.0.0.4` |
| 操作系统 | Ubuntu（hostname: VM-0-4-ubuntu） |
| 区域 | 上海 |

### 1.2 SSH 连接

```bash
ssh -i "密钥文件路径" ubuntu@122.51.205.94
```

密钥文件在本地路径（用户电脑）：
```
C:\Users\Administrator\Documents\锤子Aicg\02_腾讯云服务器\keys\ssh_key.pem
```

SSH 端口：`22`（默认）

### 1.3 域名

| 域名 | 指向 |
|------|------|
| `xiayeasy0102126.xyz` | 122.51.205.94 |
| `www.xiayeasy0102126.xyz` | 122.51.205.94 |
| `ai.xiayeasy0102126.xyz` | 122.51.205.94 |

当前用户通过 `http://122.51.205.94/` 访问。

---

## 二、端口和服务

### 2.1 端口总览

| 端口 | 协议 | 绑定 | 服务 | PID |
|------|------|------|------|-----|
| **80** | TCP | `0.0.0.0:80` | **Nginx** 反向代理（用户入口） | 3345 |
| **7861** | TCP | `0.0.0.0:7861` | **OiioiiPool API**（第三方AI资源池） | 746 |
| **7862** | TCP | `0.0.0.0:7862` | **AiForge 后端**（主应用，FastAPI） | 338740 |
| **7863** | TCP | `127.0.0.1:7863` | **AiForge 管理后台**（仅内网） | 46402 |

### 2.2 用户访问链路

```
浏览器 → http://122.51.205.94/ (端口80)
                ↓
           Nginx (端口80)
                ↓
           http://127.0.0.1:7862/ (后端主服务)
                ↓
           返回 index.html → 浏览器加载 JS/CSS
                ↓
           前端 API 请求 → http://122.51.205.94/api/... → Nginx → localhost:7862
```

### 2.3 systemd 服务

#### AiForge 主服务（aiforge.service）

```
文件：/etc/systemd/system/aiforge.service
类型：simple
用户：ubuntu
工作目录：/home/ubuntu/aiforge/backend
启动命令：python3 -m uvicorn main:app --host 0.0.0.0 --port 7862
重启策略：always
```

环境变量：

| 变量 | 值 |
|------|-----|
| `AIFORGE_FRONTEND_DIR` | `/home/ubuntu/aiforge/dist` |
| `AIFORGE_NOTIFY_KEY` | `aiforge2025` |
| `AIFORGE_BASE_URL` | `http://122.51.205.94` |
| `AIFORGE_PAY_URL` | `https://pay.gggua.com` |
| `AIFORGE_PAY_PID` | `1764` |
| `AIFORGE_PAY_KEY` | `2z47J3131Fe0J43hjOh3K3cH0413Z66y` |
| `AIFORGE_PAY_TYPE` | `epay` |

#### OiioiiPool API（oiioii.service）

```
文件：/etc/systemd/system/oiioii.service
类型：simple
用户：ubuntu
工作目录：/home/ubuntu/oiioii
启动命令：python3 -m uvicorn api.server:app --host 0.0.0.0 --port 7861
环境变量：TUNNEL_ENABLED=false
```

### 2.4 管理命令

```bash
# 查看服务状态
sudo systemctl status aiforge
sudo systemctl status oiioii

# 重启服务
sudo systemctl restart aiforge
sudo systemctl restart oiioii

# 查看日志
sudo journalctl -u aiforge -n 50 --no-pager
sudo journalctl -u oiioii -n 50 --no-pager

# Nginx
sudo nginx -t        # 测试配置
sudo nginx -s reload # 重载配置
```

---

## 三、Nginx 配置

### 3.1 配置文件位置

```
/etc/nginx/sites-enabled/aiforge
```

### 3.2 配置要点

```nginx
# 80 端口监听，域名：xiayeasy0102126.xyz / www.xiayeasy0102126.xyz / ai.xiayeasy0102126.xyz

# /assets/ — JS/CSS 缓存 30 天（文件名含 hash，放心缓存）
# = / (根路径) — HTML 不缓存（每次请求都从服务器拿最新的）
# /api/gen/file/ — 流式传输，不缓冲
# /api/gen/refs/ — 流式传输
# / — 其余所有路径，HTML 不缓存
# /admin/ — 代理到 7863 管理后台
```

### 3.3 缓存说明

- Nginx 给 HTML 返回 `Cache-Control: no-cache, no-store, must-revalidate` — 浏览器每次都去服务器拿最新的
- Nginx 给 CSS/JS 返回 `Cache-Control: public, immutable` + `expires 30d` — 浏览器缓存30天
- 如果用户还是看到旧版本：需要 Ctrl+F5 强制刷新一次，之后所有用户自动更新

---

## 四、项目代码结构

### 4.1 服务器上的目录

```
/home/ubuntu/
├── aiforge/              ← 主项目（前端 + 后端）
│   ├── backend/          ← 后端 Python 代码
│   │   ├── main.py       ← 入口
│   │   ├── config.py     ← 配置
│   │   ├── admin.py      ← 管理后台
│   │   ├── api/          ← API 路由
│   │   │   ├── auth.py       ← 认证
│   │   │   ├── user.py       ← 用户
│   │   │   ├── project.py    ← 项目（一键成片）
│   │   │   ├── generate.py   ← 生成
│   │   │   ├── payment.py    ← 支付
│   │   │   ├── pool.py       ← 资源池
│   │   │   ├── sqb_pay.py    ← 收钱吧支付
│   │   │   └── alipay_pay.py ← 支付宝支付
│   │   ├── core/         ← 核心逻辑
│   │   │   └── vimax/    ← 视频分解模块
│   │   │       ├── decomposer.py
│   │   │       └── extractor.py
│   │   └── models/       ← 数据模型
│   │       └── db.py
│   │
│   ├── frontend/         ← 前端 Vue 源码
│   │   ├── src/
│   │   │   ├── App.vue       ← 根组件（路由出口 + 侧边栏 + keep-alive）
│   │   │   ├── style.css     ← 全局样式（CSS 变量 + 主题）
│   │   │   ├── main.ts       ← 入口
│   │   │   ├── views/        ← 页面
│   │   │   │   ├── Login.vue
│   │   │   │   ├── Project.vue    ← 一键成片（有 bug）
│   │   │   │   ├── Gallery.vue    ← 画廊
│   │   │   │   ├── Workspace.vue  ← 工作区
│   │   │   │   ├── Pricing.vue    ← 定价
│   │   │   │   ├── Settings.vue   ← 设置
│   │   │   │   └── Admin.vue      ← 管理
│   │   │   ├── router/       ← 路由
│   │   │   ├── stores/       ← 状态管理 (Pinia)
│   │   │   ├── api/          ← API 封装
│   │   │   ├── components/   ← 组件
│   │   │   ├── composables/  ← 组合式函数
│   │   │   └── lib/          ← 工具
│   │   └── dist/         ← 构建产物（编译后的前端）
│   │
│   └── dist/             ← 后端配置引用的前端静态文件目录
│       ├── index.html
│       ├── favicon.svg
│       └── assets/
│
└── oiioii/               ← OiioiiPool API（第三方服务）
    └── api/
        └── server.py
```

### 4.2 本地开发目录（用户电脑）

```
C:\Users\Administrator\Documents\锤子Aicg\
├── 01_本地代码/（项目旧版本/个人备份）
├── 02_腾讯云服务器/
│   └── keys/
│       └── ssh_key.pem       ← SSH 密钥
│
├── 03_AiForge全栈/           ← 当前正在开发的版本
│   ├── frontend/             ← 前端源码
│   └── backend/              ← 后端源码
│   （大量 deploy 验证脚本在根目录）
│
├── AiForge更新日志.md
├── chuanqi2.0.md
└── 更新脚本.py
```

### 4.3 部署流程

**正确的工作流：本地 build → 上传 dist 到服务器**

```bash
# 1. 本地修改源码（frontend/src/views/Project.vue 等）
# 2. 本地构建
cd 03_AiForge全栈/frontend
npm run build

# 3. 将整个 dist 目录上传到服务器
scp -i "C:\Users\Administrator\Documents\锤子Aicg\02_腾讯云服务器\keys\ssh_key.pem" -r dist/* ubuntu@122.51.205.94:/home/ubuntu/aiforge/dist/

# 4. SSH 登录并重启后端
ssh -i "C:\Users\Administrator\Documents\锤子Aicg\02_腾讯云服务器\keys\ssh_key.pem" ubuntu@122.51.205.94 "sudo systemctl restart aiforge.service"

# 5. 验证
curl http://localhost/
```

**不要做的事（之前踩过的坑）：**
- ❌ 不要只 scp 源文件到服务器再在服务器上 npm run build（会导致本地 dist 版本不一致）
- ❌ 不要改完源文件忘了在本地 build 就直接上传（服务器的旧 dist 还在）
- ❌ Nginx 不需要重启（只重启 aiforge.service 即可）

**注意**：服务器 dist 目录是 `/home/ubuntu/aiforge/dist/`，后端 `AIFORGE_FRONTEND_DIR` 环境变量指向这里。每次新 build 后 JS/CSS 文件名 hash 会变，自动生效。

---

## 五、已知问题（需要程序员排查）

### 问题 1：导航切换后右侧空白（一键成片模块）

**现象**：在一键成片（Project.vue）页面，点击左侧导航栏切换其他模块，再切回来，右侧内容空白，只有侧边栏可见。

**根本原因**：
- `App.vue` 中 `<router-view>` 被 `<keep-alive>` 包裹（[App.vue:L138-L144](file:///C:/Users/Administrator/Documents/锤子Aicg/03_AiForge全栈/frontend/src/App.vue#L138-L144)）
- `<keep-alive>` 导致组件切换时不销毁，`onUnmounted` 不会触发
- `Project.vue` 中 `startPolling()` 的 `setInterval` 在组件被 `<keep-alive>` 缓存后还在跑
- 当再次激活时，`onActivated` 回调触发了 fetch，但轮询仍在继续
- 使用了 `<transition mode="out-in">`，过渡动画有时会卡住，导致页面不渲染

**已完成修复**（但未正式验证通过）：
- 在 Project.vue 中使用了 `onActivated` + `onDeactivated` 生命周期
- `onDeactivated` → 停止轮询
- `onActivated` → 重新 fetch 数据

**待排查**：
- `<keep-alive>` 是否应该改为 `exclude="Project"`（排除 Project 组件，让它每次重新挂载）
- 或者 `<transition mode="out-in">` 的 `out-in` 模式是否导致闪烁

**修改过的文件**：
- `frontend/src/views/Project.vue`（最近一次改动加了 `onActivated` / `onDeactivated`）
- `frontend/src/App.vue`（未改，保持 `<keep-alive>` 包裹）

### 问题 2：UI 颜色太暗，用户看不清

**现象**：在默认深色主题（deepspace）下，标签文字、输入框背景、边框等颜色太暗，用户在显示器上看不清楚。

**已做的改动**：
- `frontend/src/style.css`: CSS 变量调亮（text-primary: `#eeeeef`, text-secondary: `#b8b8c0`, text-muted: `#909098`）
- `frontend/src/views/Project.vue`: Agent 对话框输入框改用硬编码颜色 `style="background:#252540;border:2px solid #556688"`（加了 `!important`）

**说明**：部分 Tailwind 类编译成 rgba 硬编码值，CSS 变量改了对它们没用。Project 组件里的 Agent 输入框已经改用 inline style 硬编码。

### 问题 3：Agent 输入框

**现象**：一键成片页面的 Agent 对话框输入框看不见，只有快速提问按钮。

**已重写**：整个 Agent 对话框全部用 inline style `background:#181826` / `#252540` 硬编码颜色，不依赖 Tailwind 编译。

### 问题 4：数据库

- 后端 SQLite 数据库位置：`/home/ubuntu/aiforge/backend/data/aiforge.db`
- 测试用户：`sci_test@aiforge.ai` / `sci2025pw`（~50万积分）

### 问题 5：前端打包检查

`package.json` 中 `npm run build` 包含 `vue-tsc -b`（TypeScript 类型检查）。如果 TS 有类型错误，构建会失败。

---

## 六、后端关键配置

### 6.1 config.py

| 配置 | 值 | 说明 |
|------|-----|------|
| `SECRET_KEY` | 环境变量 `AIFORGE_SECRET` 或默认硬编码 | JWT 密钥 |
| `JWT_ALGORITHM` | `HS256` | JWT 算法 |
| `JWT_EXPIRE_HOURS` | `72` | Token 有效期 |
| `API_PORT` | `7862` | 后端端口 |
| `OIIOII_API` | `http://localhost:7861` | 第三方AI资源池地址 |
| `POINTS_PER_YUAN` | `100` | 积分兑换比例 |
| `LLM_API_URL` | 环境变量 `AIFORGE_LLM_URL` 或默认 | AI 对话 API |
| `LLM_API_KEY` | 环境变量 `AIFORGE_LLM_KEY` 或默认 | AI 对话密钥 |
| `LLM_MODEL` | `deepseek-v4-flash` | AI 模型 |
| `NEW_USER_BONUS` | `50` | 新用户赠送积分 |

### 6.2 支付配置

| 变量 | 值 |
|------|-----|
| `AIFORGE_PAY_URL` | `https://pay.gggua.com` |
| `AIFORGE_PAY_PID` | `1764` |
| `AIFORGE_PAY_KEY` | `2z47J3131Fe0J43hjOh3K3cH0413Z66y` |
| `AIFORGE_PAY_TYPE` | `epay` |

---

## 七、开发须知

### 7.1 技术栈

- **前端**：Vue 3 + TypeScript + Vite + Tailwind CSS + Pinia + Vue Router
- **后端**：Python + FastAPI + Uvicorn + SQLite
- **第三方**：GSAP（动画）、Lucide（图标）、OiioiiPool API（AI资源池）
- **服务器**：Nginx (反向代理) + systemd (服务管理)

### 7.2 本地开发

```bash
# 前端
cd frontend
npm install
npm run dev    # 本地开发（Vite 热更新）

# 后端
cd backend
pip install -r requirements.txt  # 如有
python -m uvicorn main:app --reload
```

### 7.3 测试账号

| 角色 | 邮箱 | 密码 | 积分 |
|------|------|------|------|
| 测试用户 | `sci_test@aiforge.ai` | `sci2025pw` | ~50万 |

---

## 八、补充说明

### 8.1 本地项目文件夹

用户电脑上的项目主文件夹是：
```
C:\Users\Administrator\Documents\锤子Aicg\
```

子文件夹：
- `01_本地代码/` — 旧版本/个人代码
- `02_腾讯云服务器/` — SSH 密钥
- `03_AiForge全栈/` — 当前开发版本（前端+后端源码 + 部署诊断脚本）

### 8.2 端口号说明

| 目的 | 正确路径 |
|------|---------|
| 公网访问 | `http://122.51.205.94/`（端口80，默认） |
| 管理员后台 | `http://122.51.205.94/admin/`（Nginx 代理到 7863） |
| 本地测试 | `http://localhost:7862/`（直接访问后端） |

**不需要带 `:7862` 访问**，Nginx 监听 80 端口会自动转发到 7862。

### 8.3 快速定位

有问题需要改的文件：

| 要改什么 | 文件路径（本地） |
|----------|----------------|
| 左侧导航切换bug | `frontend/src/App.vue`（删 keep-alive 或 exclude Project） |
| Agent 对话框 | `frontend/src/views/Project.vue`（搜索 "Agent面板"） |
| 全局颜色 | `frontend/src/style.css`（CSS 变量） |
| 后端 API | `backend/main.py` + `backend/api/` |
| Nginx 缓存 | 服务器 `/etc/nginx/sites-enabled/aiforge` |
| 数据库 | 服务器 `/home/ubuntu/aiforge/backend/data/aiforge.db` |

---

*文档结束。如有遗漏请联系补充。*