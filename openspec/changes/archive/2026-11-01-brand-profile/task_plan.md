# 实施计划

1. 先处理现有数据（任务 1），等用户决定。
2. `services/content_identity.py`：`BrandProfile`（extra=forbid）；`save_revision` 按 kind 选模型；`effective` 跳过品牌、返回 `brand_profile`；`create_snapshot` 把品牌资料放进快照（新快照才有）。
3. `services/persona_brief.py` 加 `brand`；`creative_packages` / `text_master_ai` 的身份上下文带品牌块；`text_master_checks._identity` 合并品牌禁用词与红线。
4. `web/src/product/IdentityWorkspace.tsx` 品牌分支：概览、编辑表单、Logo 选择（复用形象照的通用库选择）。
5. 验证并回写 progress / README。
