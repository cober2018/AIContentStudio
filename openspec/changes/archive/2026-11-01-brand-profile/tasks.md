///
- [x] 1. 数据：把「母婴博主nina」旧品牌字段给用户看，按用户决定处理
- [x] 2. 后端：`content_identity` 品牌资料模型 `BrandProfile`，品牌修订只收新字段；`effective` 不再合并品牌字段，另给 `brand_profile`；身份快照冻结品牌资料
- [x] 3. 后端：`persona_brief` 加 `brand` 块（视频 / 文章简报）；平台写稿任务包带品牌块；`text_master_checks` 加品牌禁用词与红线硬检查
- [x] 4. 前端：`IdentityWorkspace` 品牌概览与编辑改成品牌字段（Logo 选通用素材库图片）
- [x] 5. 验证：知数造物填一版资料 → 新建作品读简报看到品牌块；禁用词命中被拦；相关测试、tsc
- [ ] 6. 用户验收后提交、归档
