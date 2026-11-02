# findings（写 PRD 时的探查结果）

- 新建入口：商品视频工作台 ProductWorkbench.tsx 约 89 行「属于哪个账号角色（声音跟着角色走）」，可选「不指定」；POST /product-skus/{id}/works 的 WorkIn.persona_id 可选；product_creation.py 约 91、191 行校验并写入 unit.persona_id。
- 改不了：routers/content_projects.py 约 715 行，商品作品 PATCH 含 persona_id 直接 422「商品作品请使用商品配置与工作流入口，不绑定内容角色」。
- 依赖角色的地方：voiceover.settings_for（声音）、product_video.references 约 228 行（形象照）、direction 的人物规则；copy_unit 复制会沿用原作品角色（2026-11-02 已修为无角色不建快照）。
- 正式库商品作品：83（角色 5 懒羊羊小王）、84、85、90、91、92（无角色）；90 成片已定稿。
- 角色声音（voice_presets.personas）：懒羊羊小王→女声，阿玲聊生活→阅历姐姐，其余→男声。
- 商品作品 identity_snapshot_id 一律为空；商品资料来自商品版本，不来自角色资料。
