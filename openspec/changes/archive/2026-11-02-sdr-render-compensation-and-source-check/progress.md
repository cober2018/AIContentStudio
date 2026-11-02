# progress

- 2026-11-03 方案已写，等用户确认。
- 2026-11-03 用户确认，开始实施。
- 2026-11-03 实现完成（未提交）：sdr-render-comp.cube 入 craft-resolve/luts（SHA256 606ddfa1…一致）；video_chain RULES 新增「渲染补偿（必做）」；color.md 新增「普通实拍渲染补偿（必做）」、HLG 条目改不用在/常见错误；finishing.md、SKILL.md、choose.md 同步。delivery_checks.source_brightness 接到小样/成片交付；阈值 source_brightness_diff（默认 8，1–100）进设置页；审阅页文案「第 N 镜成片比原片暗/亮 X 级」。
- 验证（只读）：任务 41 成片 SDR 镜头 shot-0/1/2/6 差 −9.8/−20.5/−18.8/−8.6 全部提示，HLG 镜头 3/4/5/7 跳过；任务 42（已补偿成片）差 +6.0/−3.3/−1.6/+7.9 无提示；任务 37 全是 HLG 原片，全部跳过、无提示。pytest 5 个已知失败、2441 通过；tsc 通过；openspec validate 通过。
