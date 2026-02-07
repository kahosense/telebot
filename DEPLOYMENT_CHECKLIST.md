# Railway Free Plan 部署检查清单

## 📋 部署前准备

### 1. 提交代码到 Git
```bash
git add .
git commit -m "Adapt for Railway Free Plan with webhook mode"
git push
```

### 2. Railway 环境变量设置

在 Railway 项目 → Variables 中添加：

```
TELEGRAM_BOT_TOKEN=你的_telegram_bot_token
OPENAI_API_KEY=你的_openai_api_key
OPENAI_BASE_URL=https://api.laozhang.ai/v1
OPENAI_MODEL=claude-sonnet-4-5-20250929
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=1000
```

**注意**：不需要设置 `WEBHOOK_URL`，代码会自动生成！

### 3. Railway Settings 配置

- **Start Command**: `python bot.py`
- **Restart Policy**: `On Failure`
- **Serverless**: ✅ Enabled（Free Plan 自动开启）

### 4. 生成公网域名

1. Railway 项目 → Settings → Networking
2. 点击 "Generate Domain"
3. 会得到一个类似 `xxx.railway.app` 的域名

### 5. 部署并验证

Railway 会自动部署，查看日志应该看到：

```
==================================================
Starting bot in WEBHOOK mode
Port: 8000
Webhook URL: https://xxx.railway.app/webhook
Mode: Railway Free Plan (Serverless compatible)
==================================================
```

### 6. 测试 Bot

1. 在 Telegram 找到 bot
2. 发送 `/start`（可能有 2-5 秒延迟，这是冷启动，正常现象）
3. 发送日志文本测试转换功能
4. 等待 30 分钟后再测试（验证容器能否从休眠唤醒）

## ✅ 验证清单

部署成功的标志：
- [x] Railway 日志显示 "WEBHOOK mode"
- [x] Bot 能响应 `/start` 命令
- [x] 消息转换功能正常
- [x] 休眠后能被消息唤醒

## 🐛 问题排查

如果遇到问题，按顺序检查：

1. **Bot 完全不响应**
   - 检查 TELEGRAM_BOT_TOKEN 是否正确
   - 查看 Railway 日志是否有错误

2. **报错 "WEBHOOK_URL or RAILWAY_PUBLIC_DOMAIN must be set"**
   - 确认已在 Settings → Networking 生成域名
   - 重新部署项目

3. **首次消息很慢**
   - 正常现象，这是 Serverless 冷启动（2-5 秒）
   - 后续消息会快很多

4. **LLM 请求失败**
   - 检查 OPENAI_API_KEY 是否正确
   - 检查 OPENAI_BASE_URL 是否可访问

## 📚 相关文档

- 详细部署指南：[RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)
- 代码说明：[bot.py](bot.py)
- 环境变量模板：[.env.example](.env.example)

---

**最后更新**: 2026-02-07
