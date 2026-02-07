# Railway Free Plan 部署指南

## 🎯 架构说明

### 自动模式切换
Bot 会自动检测运行环境并选择合适的模式：

| 环境 | 检测方式 | 运行模式 |
|------|---------|---------|
| **Railway** | 存在 `PORT` 环境变量 | Webhook 模式 |
| **本地开发** | 不存在 `PORT` 环境变量 | Polling 模式 |

### Railway Free Plan 架构
```
Telegram API
    ↓ (HTTP POST /webhook)
Railway Free Plan Container (Serverless)
    ↓ (唤醒容器)
Bot 处理消息
    ↓ (调用 LLM)
Claude API
    ↓ (返回结果)
回复用户
```

## ⚙️ Railway 配置步骤

### 1. 环境变量设置

在 Railway 项目的 Variables 面板中添加：

```bash
# 必需的环境变量
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.laozhang.ai/v1
OPENAI_MODEL=claude-sonnet-4-5-20250929

# 可选的环境变量
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=1000

# Railway 自动设置（无需手动添加）
# PORT=<自动分配>
# RAILWAY_PUBLIC_DOMAIN=<自动分配>
# RAILWAY_ENVIRONMENT=production
```

### 2. Settings 配置

#### Start Command
```bash
python bot.py
```

#### Restart Policy
```
On Failure
```

#### Serverless
```
✅ Enabled (Free Plan 强制开启)
```

### 3. 生成公网域名

1. 进入 Railway 项目的 Settings
2. 找到 Networking 部分
3. 点击 "Generate Domain"
4. Railway 会自动分配一个 `.railway.app` 域名
5. Bot 会自动使用 `RAILWAY_PUBLIC_DOMAIN` 环境变量

**注意**：不需要手动设置 `WEBHOOK_URL`，代码会自动生成！

### 4. 部署

```bash
# 提交代码
git add .
git commit -m "Support Railway Free Plan with webhook mode"
git push

# Railway 会自动部署
```

## 📊 验证部署

### 查看日志

在 Railway 的 Deployments 标签中，点击最新的部署，查看日志：

**成功的日志应该显示：**
```
==================================================
TeleBot Configuration
==================================================
Model: claude-sonnet-4-5-20250929
API Base URL: https://api.laozhang.ai/v1
Temperature: 0.7
Max Tokens: 1000
Deployment: Railway
==================================================
==================================================
Starting bot in WEBHOOK mode
Port: 8000
Webhook URL: https://your-app.railway.app/webhook
Mode: Railway Free Plan (Serverless compatible)
==================================================
Application started
```

### 测试 Bot

1. 在 Telegram 中找到你的 bot
2. 发送 `/start` 命令
3. **首次消息可能有 2-5 秒延迟**（冷启动，这是正常的）
4. 发送一些日志文本，测试转换功能
5. 等待 15-30 分钟后再测试（验证容器休眠后能否正常唤醒）

## 🔍 常见问题

### Q1: 首次消息响应很慢？
**A**: 这是 Serverless 的正常行为。容器休眠后，首次请求需要冷启动（2-5 秒）。后续消息会快很多。

### Q2: 如何确认是 Webhook 模式？
**A**: 查看 Railway 日志，应该看到 "Starting bot in WEBHOOK mode"。

### Q3: 报错 "WEBHOOK_URL or RAILWAY_PUBLIC_DOMAIN must be set"？
**A**:
1. 确认已经在 Railway Settings → Networking 中生成域名
2. 重新部署项目（Railway 会自动设置 `RAILWAY_PUBLIC_DOMAIN`）

### Q4: Bot 不响应消息？
**A**:
1. 检查 Railway 日志是否有错误
2. 确认环境变量设置正确
3. 验证 Telegram bot token 是否有效
4. 检查域名是否生成成功

### Q5: 想切换回 Polling 模式？
**A**: 升级到 Hobby Plan ($5/月)，然后在 Settings 中关闭 Serverless。

## 💰 成本优化

| Plan | 月费 | Serverless | 适用模式 |
|------|------|-----------|---------|
| Free | $0 | 强制开启 | Webhook ✅ |
| Hobby | $5 | 可关闭 | Polling/Webhook |

**建议**：如果 Free Plan 够用（可以接受冷启动延迟），就保持 Free Plan + Webhook 模式。

## 🚀 性能优化建议

### 1. 减少冷启动时间
- ✅ 已优化：使用轻量级依赖
- ✅ 已优化：快速初始化（无需数据库）

### 2. 保持容器活跃（可选）
如果不想要冷启动延迟，可以：
- 使用外部服务每 5 分钟 ping 一次 webhook URL
- 或者升级到 Hobby Plan 关闭 Serverless

### 3. 监控和日志
- Railway 自动提供日志
- 可以使用 Railway CLI 查看实时日志：
  ```bash
  railway logs
  ```

## 📝 本地开发

本地开发时，bot 会自动使用 Polling 模式：

```bash
# 1. 创建 .env 文件
cp .env.example .env
# 编辑 .env，填入真实的 tokens

# 2. 启动 bot
./start_bot.command

# 3. 日志应该显示：
# Starting bot in POLLING mode
# Mode: Local development
```

## ✅ 检查清单

部署前确认：
- [x] Railway 项目已创建
- [x] 所有环境变量已设置
- [x] 已生成公网域名
- [x] Start Command 设置为 `python bot.py`
- [x] Restart Policy 设置为 `On Failure`
- [x] 代码已推送到 Git 仓库

部署后确认：
- [x] 日志显示 "Starting bot in WEBHOOK mode"
- [x] Telegram bot 响应 `/start` 命令
- [x] 消息转换功能正常工作
- [x] 等待 30 分钟后仍能正常响应（验证唤醒机制）

---

**最后更新**: 2026-02-07
**适用版本**: Railway Free Plan (Serverless Enabled)
