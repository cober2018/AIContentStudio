## Why
「登记平台公开身份」的平台下拉里没有视频号，角色绑不了视频号账号。知数Talk 在 13 个平台都登记了，唯独缺视频号；审阅与交付里视频号只能显示「未绑账号」，浏览器发布试点也正是拿视频号做。

用户确认（2026-11-10）：视频号只是一个**发布账号的平台**，不做渠道改写——视频本来就没什么可改写的，改写只对文章、图文有意义。

## What Changes
- 新增「只登记发布账号的平台」清单，目前只有视频号（`PUBLISH_ONLY_CHANNELS`）。
- 登记平台账号时，下拉里出现视频号；后端登记账号接受视频号。
- 视频号不进作品渠道清单：作品选渠道、渠道变体、商品创建等仍用原来的渠道清单，看不到视频号。
- 审阅与交付里视频号原本就在发布平台中，登记账号后会显示「账号：<名称>」，交付目标带上这个账号。

## 不做
- 不做视频号的写作、改写、渠道变体，不加渠道档案。
- 快手、YouTube 同样还没登记入口，这次不动。

## Impact
- apps/api/app/services/content_harness/channel_registry.py：`PUBLISH_ONLY_CHANNELS`、`list_account_channels`
- apps/api/app/routers/channels.py：`/channels?for_accounts=true`
- apps/api/app/services/content_identity.py：登记账号放行视频号
- apps/web/src/product/AccountDesk.tsx、IdentityWorkspace.tsx：账号页改读 `for_accounts=true`
