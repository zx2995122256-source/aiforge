# OiioiiPool AI 生成池管理系统

## 快速启动

### 方式一：便携版（推荐）

1. 解压 `OiioiiPool_便携版.rar`
2. 双击 **`启动.bat`**
3. 自动打开浏览器 → http://localhost:7861
4. 按 `Ctrl+C` 停止服务

### 方式二：Python 源码

```bash
pip install -r requirements.txt
playwright install chromium
python main.py
```

## 功能

- **生图**：支持 GPT-Image2 / Nano2 / Niji7 / Seedream50 / Flux 五种模型
- **生视频**：支持 Vidu Q2 / Kling 2.6 / Hailuo 2.3 / Wan2.7 / Sora2 等十种模型
- **多张垫图**：生图和生视频均支持上传多张参考图
- **自动注册**：积分耗尽自动注册新账号
- **公网访问**：自动 Cloudflare Tunnel，远程可使用

## 目录结构

```
OiioiiPool_便携版/
├── 启动.bat            ← 双击启动
├── 数据备份.bat        ← 手动备份数据
├── OiioiiPool.exe      ← 编译后的主程序
├── cloudflared.exe     ← 隧道工具
├── config.ini          ← 配置文件（可修改端口等）
├── data/               ← 运行时数据（可备份迁移）
│   ├── oiioii_pool.db  ← SQLite 数据库
│   ├── output/         ← 生成结果（按日期分类）
│   │   ├── 2026-05-30/
│   │   └── refs/       ← 垫图目录
│   └── backups/        ← 自动备份
├── logs/               ← 日志文件
└── playwright_browsers/← Playwright 浏览器（自动下载）
```

## 配置

编辑 `config.ini` 可修改：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| port | 7861 | 管理面板端口 |
| tunnel.enabled | true | 是否开启 Cloudflare 隧道 |
| database.backup_enabled | true | 是否自动备份数据库 |
| database.backup_retention_days | 30 | 备份保留天数 |
| logging.level | INFO | 日志级别 (DEBUG/INFO/WARNING/ERROR) |

## 数据备份

- **自动备份**：每次启动自动备份当天数据库
- **手动备份**：双击 `数据备份.bat`
- **备份位置**：`data/backups/db_YYYY-MM-DD.db`
- **导出任务**：备份时会同时导出所有任务记录为 JSON

## 自定义编译

```bash
scripts\build.bat
```

需要安装 PyInstaller：
```bash
pip install pyinstaller
```
