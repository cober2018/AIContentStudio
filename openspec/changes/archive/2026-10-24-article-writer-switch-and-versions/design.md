## 现状

- 文字/图文的「内容方案」页是 `CreationRecipePanel`：平台阶段逐个运行，用户在页面接受候选，`stage.master.propose` 阶段把采用的候选存成主稿修订（`source_kind=workflow_stage`）。
- 主稿修订不可变，`content_master_revision` 按 `revision_no` 递增；渠道版本、候选冻结会引用具体修订。
- 视频链用 `system_settings["video_chain"]` 按单元记决定；`save_revision` 在视频定稿后拒绝。

## 开关

- 存 `system_settings["article_chain"][unit_id] = {"writer": "platform"|"external", "decisions": [...], "hidden": [master_id...]}`。默认 `platform`。
- `PUT /content-projects/{p}/units/{u}/article-chain/writer {writer}`：定稿后拒绝；记审计。
- 组件 `Switch`（`role="switch"`、`aria-checked`，圆点滑动，左「平台模型」右「第三方模型」），放在内容方案页标题下。

## 第三方模型写作链

状态（`article_chain.state`）：not_started → draft_review → draft_changes → done。
- 当前稿 = 最新一条 `edit_summary.article_chain == "draft"` 的主稿修订。
- `save_article_draft`：开关须为 external，未定稿；校验 payload 后经 `save_revision` 存，`source_kind="user_edit"`、`edit_summary={"article_chain": "draft", "note": ...}`，状态变 draft_review。
- 决定 `POST .../article-chain/decision {decision: approve|changes, notes}`；approve → done（锁定）；changes → draft_changes，第三方模型读到后存下一版。
- 锁：`save_revision` 对文字/图文单元在 `article_chain` done 时拒绝，提示「已定稿，要调整请复制一份」。复制一份对文字放开（带当前稿，从审稿开始）。
- 平台模型方式不走这条链，沿用现有阶段与采用流程。

## 版本列表

- `GET .../article-chain/versions`：该单元全部主稿修订（去掉 hidden），每条：id、版本号、来源（`workflow_stage` → 平台模型；`article_chain` → 第三方模型；其余 → 手动）、时间、是否当前、是否定稿、是否被引用（渠道版本 / 候选冻结）。
- 查看：沿用主稿读取。
- 用这一版：以该修订内容存一条新修订（`edit_summary={"restored_from": id}`），旧的不动。
- 删除：`DELETE .../article-chain/versions/{id}` → 加入 hidden。当前、定稿、被引用的拒绝。修订行本身不物理删除（被历史记录和审计引用），只是不再出现在列表和选择里；对用户表现为删除、不能恢复。

## MCP

`get_article_brief`、`save_article_draft`、`get_article_decision` 加入 `TOOLS` 和 `mcp_settings` 的 article 组；`save_article_draft` 的 payload 按单元形态校验（`text.master.v2` / `graphic.master.v2`），brief 里给出两种格式的最小示例。图文图片：用 `generate_video_image`（项目生图）或素材库素材的 `material_revision_id`。

## 不做

视频不加开关；平台阶段内容不改；不改表结构。
