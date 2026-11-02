# 视频设置变了以后，MCP 仍能保存导演稿和选材

## 为什么
导演稿通过后改了视频设置（如商品主图、素材方式），项目 46 / 作品 90 再经 MCP 保存新导演稿或选材都被拒：`master_context_conflict`。

原因：MCP 的保存（`save_director_draft`、`set_shot_materials` 等走 `video_chain._save` → `edit_handoff._save`）把**上一版导演稿存下的上下文指纹**（`get_revision()["context_hash"]`，即旧版本的 `row.context_hash`）当作「期望上下文」传给 `save_revision`；而 `save_revision` 拿它和**当前**上下文比。设置一改，两者必然不同，于是永远保存不了。

## 改什么
- `edit_handoff._save` 的期望上下文改为保存当下按当前设置算出的上下文指纹（content_masters 已有的 `_context` + `_hash`），新版本按当前设置校验和记录。
- 保存过程中如果设置又被别处改了，`save_revision` 写入后的复核仍会拦下（保留并发保护）。

## 不改什么
- 不改其他入口的上下文校验（渠道版本、阶段采纳等仍按各自冻结规则）。
- 不改已存的导演稿版本。
