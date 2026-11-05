# 商品视频的发布文案移到「交付」步骤

## Why
发布文案（标题、话题、封面字、互动引导、简介）现在只在「导演稿」步骤最底下（`VideoChainPanel` showDraft 时渲染的 `ProductShotPanel` view="draft"）。成片定稿后，用户到「交付」步骤找不到它。

## What Changes
1. 新组件 `ProductPublishCopy.tsx`：把发布文案那块从 `ProductShotPanel` 搬出来，五栏可编辑、「保存发布文案」按钮，数据仍走 `GET / PUT product-video/publish-copy`，字数限制和存储格式不变。
2. 商品视频的「交付」步骤（`ProductionWorkspace` 里 step.id === "delivery"）显示它，放在渠道适配上面；「导演稿」步骤不再显示（只留这一处）。
3. 旁边显示这次定稿的封面（作品主稿的 cover），方便对照封面字：`GET product-video` 多返回 `cover {material_id, material_revision_id}`（取最新主稿的 cover），页面用已有的素材原图接口显示；还没有封面就写「还没有封面」。
4. 还没写文案时提示「模型定稿后会写一版，你也可以先自己填」；MCP `save_publish_copy` 说明里「The user can edit it on the page」改成「on the 交付 page」。

## 不在本次范围
- 不改字数限制、存储格式，不加按渠道多版本；角色作品（非商品）不加发布文案。

## Impact
- 前端：`ProductPublishCopy.tsx`（新）、`ProductShotPanel.tsx`（删去发布文案块）、`ProductionWorkspace.tsx`（交付步骤挂上）。
- 后端：`routers/product_skus.py`（view 带 cover）、`services/creative_mcp.py`（说明文字）。
- 生效要重启 API（前端热更新）。
