# DocMind 后端 API（Skill 客户端）

## 健康检查

`GET /health` → `{"status":"ok"}`

## 开启整理会话（正式整理前）

`POST /api/v1/organize/begin`

```json
{ "platform_user_id": "user-1", "platform": "workbuddy" }
```

响应：`organize_session_id`、`billing_type`、`max_files`（默认 500）、`expires_at`

整轮 `run` 只扣 **1 次**额度；后续分类均携带 `organize_session_id`。

## 分类

`POST /api/v1/classify`

```json
{
  "platform_user_id": "user-1",
  "platform": "workbuddy",
  "filename": "合同.pdf",
  "content_preview": "文本预览…",
  "industry": "建筑业",
  "job_title": "专业技术人员",
  "custom_categories": {},
  "existing_archive_paths": ["工作/东方广场改造/图纸"],
  "preview_only": true,
  "organize_session_id": "uuid-from-begin"
}
```

- `preview_only: true` → 免费，无需 `organize_session_id`
- `preview_only: false` → 必须先 `organize/begin`，并传入 `organize_session_id`

响应：`{"target_path":"工作/…","billing_type":"free","preview_only":false}`

额度不足时 HTTP 402；会话无效/过期 HTTP 400。

## 文件查找（索引 search）

`POST /api/v1/search/consume`

```json
{ "platform_user_id": "user-1", "platform": "workbuddy" }
```

每次 `search` 扣 **1 次查找额度**（试用期内每月 20 次，超出 0.05 元/次；订阅无限）。

响应：`billing_type`、`free_search_remaining`、`search_credits`

额度不足时 HTTP 402。

## 用户额度

`GET /api/v1/user/{platform_user_id}`

返回 `free_trial_active`、`free_trial_expire`、`free_trial_days_remaining`、整理与查找的已用/剩余免费次数、`organize_credits`、`search_credits` 及 `pricing`（含 `free_trial_months`、`subscription_annual_yuan`）。

## 可购产品

`GET /api/v1/products`

返回 SKU 列表（整理按次、查找包、月订、年订 ¥99），供客户端在 402 时展示。

## 运营充值

`POST /api/v1/admin/grant`（Header: `X-Admin-Key` = `ADMIN_SECRET_KEY`）

```json
{
  "platform_user_id": "user-1",
  "organize_credits": 5,
  "search_credits": 20,
  "subscription_days": 30
}
```

## 支付 Webhook

`POST /api/v1/webhook/payment`（平台侧，需 `BILLING_SECRET` 签名）

- `event: credits` — 增加整理按次余额（2 元/次）
- `event: search_credits` — 增加查找按次余额（0.05 元/次）
- `event: subscription` — 延长订阅（`subscription_days` 天）
- `event: subscription_monthly` — +30 天
- `event: subscription_annual` — +365 天（¥99 年订）
