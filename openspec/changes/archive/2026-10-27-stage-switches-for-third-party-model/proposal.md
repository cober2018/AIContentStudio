## Why

视频和第三方模型写稿都由接了 MCP 的第三方模型主导。平台沉淀的写作类 skill（文案、脚本、镜头规划、受众与购买理由等内置 skill）第三方模型现在读不到，也没有人能控制它用不用。用户要求：由人用一个统一开关控制第三方模型能不能用这些 skill；剪辑和特效 skill 必须一直可用。

## What Changes

- **一个统一开关，每条作品一个：** 作品制作页加「平台写作 skill」开关，由人控制，默认开。第三方模型改不了。
- **开：** 第三方模型可以读平台内置的写作类 skill（文案、脚本、镜头规划、受众、购买理由等）的说明来用。
- **关：** 读这些 skill 被平台拒绝，模型只能靠自己写。
- **剪辑和特效 skill 一直开：** craft-resolve、craft-ae 不受开关影响，随时可读；AE 模板出素材也照常。
- **模型知道开关状态：** 读视频需求（`get_video_brief`）和读写稿需求（`get_article_brief`）时，平台附上开关状态和当前能读的 skill 清单及读取方式。
- **读取工具：** `get_craft_skill` 加作品编号，除 craft-resolve、craft-ae 外还能读平台内置写作 skill；开关关闭时读写作 skill 返回「平台写作 skill 已关闭」。

## Impact

- API：作品制作设置里加开关字段（商品作品存在制作设置 `ProductionProfileRevision`；角色作品存在作品级设置）；`creative_mcp.get_craft_skill` 输入加 `project_id`、`unit_id`，支持内置 skill ref 并校验开关；`video_chain.brief`、`article_chain.brief` 附 `platform_skills`；新增读写开关的接口。
- Web：视频与写稿制作页加开关。
- 本地技能：`video-production-handoff`、`article-writing` 写明按 brief 里的 `platform_skills` 用 skill。
- 不改现有「制作阶段方法」开关（仍只作用于平台模型）。
