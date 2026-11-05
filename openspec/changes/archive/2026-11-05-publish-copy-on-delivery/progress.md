# progress

- 2026-11-05 核对：发布文案只在 ProductShotPanel view="draft"；交付步骤只有 ChannelVariantsPanel；主稿 cover 只有 material_revision_id，显示图片要 material_id。写好方案，待确认。
- 2026-11-05 用户确认后实现：新组件 `ProductPublishCopy.tsx`（五栏、保存、空提示、旁边封面）；`ProductShotPanel` 删去发布文案块；交付步骤（仅商品视频）在渠道适配上面挂上；`GET product-video` 带 `cover`（最新主稿的 cover 及 material_id）；MCP `save_publish_copy` 说明改成交付页。
- 核对：作品 93 交付页有 1 处「保存发布文案」、导演稿页 0 处；交付页显示已存的五栏文案；封面查询返回作品 93 → 素材 426 / 版本 467（重启后页面才显示图）。相关测试通过，前端 tsc、build 通过。
- 2026-11-05 重启 API 和 worker，健康检查正常；作品 93 交付页显示封面图（素材 426 / 版本 467），在发布文案右边。
