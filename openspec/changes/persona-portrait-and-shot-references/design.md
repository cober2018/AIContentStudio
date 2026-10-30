# 设计

- `content_identity.IdentityProfile` 加 `portrait_material_revision_ids: list[int]`（≤3，须是本人可用、允许模型使用的图片素材）；只对角色有效，账号 / 栏目不用。`NewPersonaForm` 上传照片 → 素材库通用图片 → 写进第一版资料；`IdentityWorkspace` 编辑资料里显示、增删。
- 新函数 `product_video.references(db, user, unit)` → `{product: [主图版本], person: [形象照版本], scene: [...]}`：先取作品「共同视觉参考」里手动选的，没有再取 SKU `primary_image_revision_id` 和所属角色的形象照。
- `shot_image.grid` / `generate_shot_image` / 图生视频首帧都改用 `references()`：
  - 有商品的格子 / 镜头附商品主图，生成后逐个跑现有 `check`，不过关单独重画（最多 3 次，沿用现规则）。
  - 有人物参考时附照片并在提示词里说明「人物长相照参考照片」；没有时提示词写「画面里不出现人物，只出现商品与场景，需要拿取时只出现手部」，`_people` 判为有人的镜头在页面和 MCP 返回里提示「这个角色没有形象照，这一镜不会出现人物」。
- 九宫格去掉商品镜头排除（`shot_grid_product_shot`），保留商品纯特写的建议提示。
- `persona_brief` 把「有没有形象照」带进第三方模型的简报，导演稿阶段就知道能不能写带人的镜头。
