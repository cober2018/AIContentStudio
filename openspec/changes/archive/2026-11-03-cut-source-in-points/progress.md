# progress

- 2026-11-03 方案已写，等用户确认。
- 2026-11-03 用户确认，开始实施。
- 2026-11-03 用户追加：按剪辑清单截取起点（含变速）补算，清单交上来时更新提示；并入本变更。
- 2026-11-03 实施完成（未提交）。改动：creative_contracts（shot_sources 白名单、单值上限 8000 字符）、creative_executions（validate_shot_sources、小样/成片交付校验并传入比亮度、剪辑清单通过后 _recheck_sources 改写小样/成片的 shot_checks）、delivery_checks（reported / manifest_clips / _located / recheck_sources，读数与提示带 source_basis）、video_chain RULES、creative_mcp submit_output 说明、VideoChainPanel「按估计位置比，可能不准」。
- 验证（只读线上库；写路径在库副本上，已删）：任务 42 成片按清单 shot-0 −0.1、shot-1 −0.7、shot-2 −1.6、shot-6 −1.5（原片 146.8，原估计 137.4/+7.9），无提示；任务 41 按清单 −15.9/−17.9/−18.8/−18.0，四条提示（任务 41 清单文件已不在盘上，借用任务 42 的截取点，两次同一剪辑选段）。shot-3/4/5/7 是 HLG，照旧不比。pytest 2441 过、5 个已知失败；tsc 过；openspec validate 过。
- 2026-11-03 API/worker 已重启，生效；未提交，等用户验收。
