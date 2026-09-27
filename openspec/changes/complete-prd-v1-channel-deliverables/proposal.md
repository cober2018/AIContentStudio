## Why

`03_ai_content_studio_PRD.md` 是本产品的长期需求基线。现有旧链路能生成抖音脚本和小红书文字，但新 M1 的受控成品包、素材、账号授权和人工回填仅支持公众号与 X Thread，尚不能把 PRD 三渠道均作为可交付成果验收。

## What Changes

- 将已批准的抖音口播脚本和小红书图文接入与 M1 一致的冻结候选、目标授权、完整成品包和人工回填链路；保留公众号现有能力。
- 抖音包交付口播文案、分镜、B-roll 提示、配音文本和标记为估算的 SRT；不宣称交付视频成片。
- 小红书包交付正文、标题、标签和有序的实际图片组；只有图片提示词时显示未完成，不能批准为图文成品。
- 每个渠道分别核对引用、素材权限、候选哈希和导出字节；编辑或撤权后，未完成目标不可继续交付旧内容。
- 页面显示每个渠道的成品就绪、待人工发布和回填状态，保留历史旧稿可读。
- 将 PRD 的 15 项 V1 验收和 30 个真实选题发布门槛独立跟踪；本变更完成不自动宣称整个 V1 达标。

## Capabilities

### New Capabilities

- `prd-v1-channel-deliverables`: 抖音脚本和小红书图文的成品、批准快照、交付包、人工回填及渠道验收。

### Modified Capabilities

无。仓库当前没有主规格目录中可修改的既有同名 capability。

## Impact

涉及 `apps/api/app/routers/article_handoff.py`、稿件/素材/导出服务、必要的数据模型及迁移、`apps/web/src/pages/` 中相关工作台与交付入口，以及 README 与 V1 验收记录。沿用现有 FastAPI、React、SQLite/PostgreSQL 和 M1 授权/回填模型；本变更不接入抖音或小红书远端发布 API。
