# 进展

- 2026-11-03：读完 persona-shot-generation/review.md 和相关代码，写好 proposal / spec / tasks。用户「确认」。
- 2026-11-03：开发完成，本地验证通过。用户「重启吧」后重启 API 和 worker，健康检查 200；线上作品 94 的 other_people 为空（导演稿还没标），没标的镜头仍是「不出现人物」。未提交。

## 改动的文件（工作区，在 persona-shot-generation 未提交改动之上）
| 文件 | 改了什么 |
| --- | --- |
| apps/api/app/services/video_documents.py | board 加可选 `other_people`（写了才存，1–60 字，错误写清理由） |
| apps/api/app/services/product_video.py | `SCENE_WITH_OTHERS(_EN)`、`OTHERS_NOTICE`、`others()`；`person_rule` 按标注出中英文规则；`person_notices` 标了的镜头换提示；`shot_prompt`、`generate_shot_image` 用标注；镜头状态多返回 `other_people` |
| apps/api/app/services/shot_image.py | 九宫格整张规则 `GRID_WITH_OTHERS`、格子描述写可以出现谁、单格重画和人物提示按标注 |
| apps/api/app/services/video_chain.py | 角色作品规则加 other_people 例外 |
| apps/api/app/services/creative_mcp.py | `get_shot_video_prompt`、`generate_shot_image`、`generate_storyboard_grid` 说明补例外 |
| apps/api/app/studio_skills/studio.video.prompt-direction/v1/SKILL.md | 第 4 条补例外 |
| apps/web/src/product/ShotWork.tsx | 标了的镜头写「这一镜可以出现宝宝（不露脸），不出现角色本人」（面板和九宫格弹框共用） |

## 验证结果（数据库副本 + 临时素材目录，生图打桩，未花钱）
「改动前」取自还在跑的线上 API（运行的是上一个变更的代码，没重启），只读。

| 项 | 结果 |
| --- | --- |
| 标「宝宝」的镜头（shot-10） | 首帧、图生视频、文生视频的中文都含「画面里不出现角色本人。宝宝可以出现手、脚、身体局部或背影，不露脸，不出现正脸和侧脸；除了宝宝，不出现别的人。」，英文含对应句；全部不含「不出现身体 / no body」 |
| 人物提示 | 这一镜 notice 和镜头状态的 person_notices 都是「这一镜可以出现宝宝（不露脸）」；镜头状态 `other_people` 列出标了的镜头 |
| 没标的镜头 | shot-5、14、18、21 的提示词和改动前逐字一致 |
| 九宫格 | 一组里 shot-2 标了、shot-1 没标：整张规则换成「只有写明的人物可以出现、不露脸，其余格子不出现人物」，第 2 格写「可以出现宝宝…不露脸」，第 1 格没有；单格重画提示词标了的带宝宝规则、没标的照旧 |
| 作品 93（商品） | 镜头状态原有 13 项和改动前一致，只多一个空的 `other_people`；全部镜头提示词和改动前逐字一致 |
| 旧导演稿哈希 | 作品 93 v6、作品 94 v1 重新校验后哈希不变 |
| 校验 | 61 字、空白、数字都被拒，理由：「board.other_people 写画面里出现的别的人物（不是角色本人），比如「宝宝」，要 1–60 字的文字」 |
| 全量测试 | 2441 passed、28 skipped、5 failed（已知的 5 个旧失败） |
| 前端类型检查 | 通过 |

线上作品 94 的导演稿没改；作品 93 只读；临时副本和文件已删除。
