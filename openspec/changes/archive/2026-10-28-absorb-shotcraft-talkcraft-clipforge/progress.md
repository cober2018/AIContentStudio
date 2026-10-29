# 进度

- 2026-10-28 写好方案，等用户确认。
- 2026-10-28 第 1 步完成：skill 分商品 / 角色 / 通用三类（`studio_creative_catalog.skill_system`、`SHARED_SKILLS`），第三方模型可读清单、`get_craft_skill` 校验、阶段方法可选列表都按作品类型过滤。实测：商品作品 42/83 可读 剪辑 2 + 通用 5 + 商品 5，读角色脚本被拒；角色作品 41/80 读商品脚本被拒。相关测试 421 通过；`tsc` 通过。
- 第 2 步完成：三个仓库稀疏下载到 `output/absorb/`（只取文字）：shotcraft@43bd349a1366、talkcraft@a7c29edfb240、clipforge@1aab133dd75f。
- 第 3 步：clipforge 映射表写好（`clipforge-mapping.md`），等用户确认。
- 第 3 步完成（用户 2026-10-28 确认映射表）：写好 6 个 skill 包并登记到 `studio_creative_catalog.SKILLS`。
  | skill | 类别 | 内容 |
  |---|---|---|
  | `studio.video.product-script@2` | 商品 | 先选形态 / 开头 / 渠道；参考 `forms.md`、`hooks.md`、`channels.md` |
  | `studio.video.product-shots@2` | 商品 | 素材模式、商品原图不变形、真实素人；参考 `categories.md` |
  | `studio.product.compliance-check@1` | 商品 | 带货合规逐句检查，只提示不代改 |
  | `studio.video.script-review@1` | 通用 | 四评委口播评审与改写规则 |
  | `studio.video.stock-scout@1` | 通用 | 免费素材找挑、版权分级；参考 `sources.md` |
  | `studio.video.digital-human@1` | 通用 | 数字人出镜规则（生成功能未上线，只用于规划） |
  验证：6 个包 `load_skill` 全部通过；商品作品 83 可读 16 项（剪辑 2 + 通用 8 + 商品 6），读角色脚本返回 404；角色视频可读通用 8 + 角色 10。`test_aco_creative_mcp.py` + `test_persona_creative_studio.py` 437 通过；ruff 通过。商品脚本 / 镜头 @1 保持不动（`workflow_templates` 仍引用 @1）。
- 第 4 步前半：232 张卡（shotcraft 124、talkcraft 108）逐张归类，写成 `cards-triage.md`：新增 26 节、合并进 14 个现有节或模板，舍弃 57 张。等用户确认后再换算写入。
- 第 4 步完成（用户 2026-10-28 确认梳理表）：按梳理表写入武器库，全部「试用」。craft-ae：`titles.md` 新增 8 节、合并 3 节；新文件 `annotate.md`、`material.md`、`data.md`；`compositing.md`、`keyframes.md` 各补一节。craft-resolve：新文件 `transitions.md`；`cutting.md`、`beat-and-speed.md` 合并与新增；`choose.md` 补 33 行问题；`finishing.md` 加交付前检查（clipforge #9）。两个 SKILL.md 目录同步。
- 第 5 步：新节字段齐全；`skill_entry` 读得到 4 个新文件和改过的 choose / finishing；相关测试 503 通过。craft-arsenal `log.md` 已记。
