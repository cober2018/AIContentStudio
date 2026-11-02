# findings

- 现行规则（video_chain RULES、color.md）：SDR 网络素材、AI 画面、AE 叠层一律不套 LUT。
- 达芬奇 LUT/MCP 下已有 sdr-render-comp.cube（33³，整体 +0.078），仓库 luts/ 只有两份 HLG LUT。
- 固定 20 级差与此前记下的 render ≈ 0.993·still − 0.078 一致，像是渲染电平/数据范围类设置问题，根因未查。
- ffprobe csv 输出对 iPhone HLG 片段会带尾逗号（side data），判断 color_transfer 必须用 JSON。
- 现有导演稿时间线视频轨条目没有 material_revision_id / trim_start_ms，检查只能退回「镜头内偏移」取原片时刻，和真实截取点不一致：任务 41 用剪辑清单真实截取点算 SDR 镜头差 −16～−19，用退回算法是 −8.6～−20.5；任务 42（已补偿）真实截取点差 ≤1.7，退回算法最大 +7.9，贴近提示线 8。成片交付早于剪辑清单，交付检查时拿不到清单里的截取点。若要更准，需要导演稿时间线写入截取起点（待用户决定，不在本次范围）。
