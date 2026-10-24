# Progress

- 2026-10-23: proposal, design, spec and tasks written. No code changed.

## 2026-10-23 实施（用户已确认）
- `stage_master_proposals.planned_shots` 读取已采用的镜头计划；`_video_plan` 有计划时要求条数相等，编号、顺序、估计时长取自计划。
- `stage_resolver` 导演稿合同：有计划时 beats 固定为 N 条，并加规则「一镜一条、按顺序、不合并不拆分；时长是估计，最终跟配音」。
- 验证（数据库副本）：U80 合同为 15/15；真实生成得到 15 个镜头，编号 shot-0…shot-14，总估计 56.5 秒。7 条答案被拒为无效输出；无计划时仍允许 8 条。相关 API 测试 613 通过。
- 未做：副本上点采用后核对镜头格子仍 15 个已选（3.1 后半）。
