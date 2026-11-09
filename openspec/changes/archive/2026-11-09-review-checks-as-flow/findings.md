# 发现

## 现状（2026-11-09）
- 页面：`apps/web/src/product/ProjectReviewCenter.tsx` 问题与审批页，每条 warning 一个处置输入框；全部填写后「批准内容」才可点；另有「技术检查报告与冻结清单」JSON。
- 后端：`production_validation.validate_warning_dispositions` 要求每条 warning（manifest.checks 与 source_master.warning_checks）按「检查ID:输入哈希」都有处置文字；批准时和交付时（`warning_dispositions_json`）都核对。
- warning 只出现在 Content Master 检查（content_master_check_run），渠道版本检查全部 pass。成片（schema 6）审批不走处置。
- 候选 15：#569 graphic_fact、#570 graphic_identity 均为 warning，原因是平台模型调用失败（provider_failed）；身份检查的图片语义本来就不可用，所以身份检查常为 warning。

## 决定
- 提醒由写作方式对应的模型判断（用户选 A）：可接受 → 黄色、可直接批准；不能接受 / 未判 / 失败 → 红色、不能批准。

## 追加发现（2026-11-09）
- 候选 15 页面显示可批准，实际批准会被拒：冻结时事实/身份为 #569/#570 提醒，之后检查重跑（#577 事实通过、#578 身份提醒），实时核对报「冻结来源已变化」。原流程节点只读冻结数据，没跑实时核对。
- 之前对 #569/#570 的两条判断是直接调用服务函数交回（未走 MCP），且针对过时检查，已标为作废（status=void）。
- 身份检查对图文永远是提醒：平台复核只看文字，visual_semantics 固定 unavailable。用户选让第三方模型看成图。
- 命令行直接读素材会找不到文件：素材库根目录来自运行配置（runtime_config.load_from_db），只有 API 进程加载了；核对要走 API 或先加载运行配置。
