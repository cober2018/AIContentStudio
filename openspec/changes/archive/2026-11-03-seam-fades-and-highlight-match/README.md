# seam-fades-and-highlight-match

- 阶段：6 件都已重启生效；未归档、未提交
- 来源：两份审计
  - archive/2026-11-02-director-dialogue-track/review.md「要改」
  - archive/2026-11-02-sdr-render-compensation-and-source-check/review.md 的三节（LUT 亮部、AE 叠层、亮部对比）
- 4 件事：口播接缝淡变不压字；补偿 LUT 亮部不再压暗；写明 AE 叠层不变暗；交付检查加亮部对比
- 代码位置（预计）：craft-resolve（sound.md、color.md、luts/、finishing.md 安装说明）、apps/api（delivery_checks.py、video_chain.py 规则里的 LUT 文件名）、apps/web（VideoChainPanel 提示文字、DeliveryCheckSettings 亮部提示线）
- 下一步：用户复核；通过后重启、归档、提交
- 审计：review.md（2026-11-03 通过；建议修存储截断，另有一条可选建议）
