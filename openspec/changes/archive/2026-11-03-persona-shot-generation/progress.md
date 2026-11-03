# 进展

- 2026-11-03：读完相关代码，写好 proposal / spec / tasks，等用户确认。
- 2026-11-03：按用户意见改方案：去掉 AI 标记；手动分文生视频 / 图生视频两种；九宫格给角色作品；验收不调计费模型，改打桩。
- 2026-11-03：九宫格改为按一致性分组（模型写进导演稿 consistency_groups，用户审）、弹框里做，商品作品一起换、旧面板删除。用户「确认」。
- 2026-11-03：开发完成，本地验证通过。用户「重启吧」后重启 API 和 worker，健康检查 200；线上读作品 94 的镜头状态：persona true、没有分组、没有形象照。未提交。

## 改动的文件（工作区，未提交）
| 文件 | 改了什么 |
| --- | --- |
| apps/api/app/services/video_documents.py | 导演稿加 `consistency_groups` 校验 |
| apps/api/app/services/product_video.py | 角色作品放行；提示词按组带共用人物 / 场景、角色作品不提商品并返回文生视频提示词；生首帧角色作品不带商品、不检查；没首帧提示；镜头状态返回 `persona`、`groups`、`grid_sheets`；改运镜只给商品作品 |
| apps/api/app/services/product_motion.py、app/product_catalog/motion.json | `motion_prompt` 加场景和不提商品的规则 |
| apps/api/app/services/shot_image.py | 九宫格按组（`group_id`），角色作品放行，保持一致说明和人物规则不提商品 |
| apps/api/app/routers/product_skus.py | 九宫格接口改传 `group_id` |
| apps/api/app/services/creative_mcp.py、mcp_settings.py | 7 个工具说明；`generate_storyboard_grid` 改传 `group_id` |
| apps/api/app/services/video_chain.py | 规则第 3 条改两类作品、加分组规则、加角色作品规则 |
| apps/api/app/studio_skills/studio.video.prompt-direction/v1/SKILL.md、references/examples.md | 九宫格改成按组 |
| apps/api/tests/test_f6d_video_documents.py | 九宫格两条旧测试按「按组出图」改预期 |
| apps/web/src/product/ShotWork.tsx（新） | 每镜一块的共用部分：手动 / 自动、首帧、九宫格候选、提示词（角色作品文生 / 图生两栏带复制）、上传 |
| apps/web/src/product/StoryboardGridDialog.tsx（新） | 九宫格弹框 |
| apps/web/src/product/StoryboardGridPanel.tsx（删） | 旧九宫格面板 |
| apps/web/src/product/ProductShotPanel.tsx | 用 ShotWork；角色作品文字和无形象照提示；归组镜头「打开九宫格」 |
| apps/web/src/product/ProductionWorkspace.tsx、VideoMaterialSteps.tsx | 素材步骤两类作品都挂镜头面板，去掉旧九宫格面板 |
| apps/web/src/product/VideoChainPanel.tsx、VideoStudioModel.ts | 导演稿审阅页列出分组；分组类型；删镜头时同步删出分组 |

## 验证结果（数据库副本 + 临时素材目录，模型调用打桩，未花钱）
| 项 | 结果 |
| --- | --- |
| 作品 94 入口 | 通过：`persona: true`，缺素材镜头正好是 shot-5、10、14、18、21，没分组；没有形象照，5 镜都有人物提示 |
| 两种提示词 | 通过：文生、图生（中英文）、首帧提示词都不含「商品 / product」，都带「不出现人物，只拍场景」；文生视频开头写画幅和时长 |
| 改运镜 | 角色作品被拒：「运镜、光线、强度只给商品作品」 |
| 生首帧 | 通过：不带参考图、不调商品检查、不存一致性结果，生成后设为首帧；人物规则不重复 |
| 自动图生视频 | 没首帧时被拒并提示「先生成首帧，或切到手动」；有首帧后用这张提交（提供方打桩） |
| 手动上传 | 通过：标「上传」，放到 shot-5；`get_shot_slots` 读到 chosen、绑定这条 |
| prepare_video_edit | 作品 94 现在开不出剪辑任务，原因是它本身缺任务书和事实边界（未改动的线上副本也是 `incomplete_context: evidence_missing, brief_missing`，再往下是 `creative_boundary_unavailable`），和这次改动无关。绕过就绪检查后，开剪的「镜头缺素材」检查已经把上传的 shot-5 算作有素材 |
| 分组校验 | 1 个镜头、镜头不存在、一个镜头两组、素材库镜头都被拒，原因写清楚；正常分组保留 |
| 角色作品九宫格 | 副本上存带分组的导演稿并采用后，按组 g1 出图：只画组内 2 镜，不带参考、不做商品检查，提示词带共用场景、不提商品，候选可用作首帧 |
| 商品作品照旧 | 作品 93（项目 48）只读比对：镜头状态和 8 个镜头的提示词，改动前后逐字一致；商品九宫格逐格检查、商品首帧流程由现有测试覆盖 |
| 全量测试 | 2441 passed、28 skipped、5 failed（就是已知的 5 个旧失败） |
| 前端类型检查 | 通过 |

临时副本、测试视频和临时素材目录已删除；没有写入项目文件夹。
