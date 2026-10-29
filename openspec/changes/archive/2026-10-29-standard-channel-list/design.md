# 设计

## 清单放在哪

`content_harness/channel_registry.py` 已是渠道合法性的唯一入口。新增 `PLANNED_CHANNELS`（渠道键 → 名称 + 待接入形态列表），只做登记：

- `list_channels` 不变，仍只返回已接入渠道，现有各处下拉不受影响。
- 新增 `list_channel_catalog(db)`：已接入渠道（`status: "ready"`）加待接入条目（`status: "planned"`）。同一渠道既有已接入形态又有待接入形态时（如抖音：口播已接入，视频、图文待接入），合在一个渠道下按形态分别标状态。
- `GET /api/v1/channels?catalog=true` 返回完整清单；不带参数行为不变。
- 某渠道接入后（发布了 Channel Profile 或注册了渠道方法），它自动出现在已接入里；`PLANNED_CHANNELS` 里对应条目随接入那次改动删掉，不留两处登记。

## 形态对应

作品形态 → 渠道形态的产物类型：文字 → text；图文 → image；视频 → script、video。待接入条目按这个类型登记，下拉据此过滤。

## 后端校验

`content_projects.py` 新建、修改作品时，在现有 `ensure_channel_in_service` 之后加一步：渠道非空时必须在 `list_channel_keys(db)` 里，否则 422「渠道不在平台清单里或还没接入」。复制作品沿用源作品的旧值，不校验。

## 前端

- `PersistentProjectPage.tsx`：渠道文字框换成下拉（读 `/channels?catalog=true`，按形态过滤，待接入 disabled）；改形态时清掉不支持的渠道。
- 叫法：本页与 `ProjectMatrixTab.tsx` 里的「内容身份」「内容单元」「新增内容单元」改成「角色」「作品」「新增作品」。
- 删 `personaModal`、`createPersona`、`personaName` 和矩阵的 `onAddPersona`；换成跳 `/identities` 新建角色的链接。
