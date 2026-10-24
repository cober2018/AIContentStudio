---
key: studio.graphic.card-plan
version: 1
source_kind: studio_builtin
---

依据接受的视觉方向和已提供的精确内容，形成有限卡片计划：稳定 id、连续 order、首卡 cover、其余 body。canvas_count 限定数量；每卡包含简洁标题、正文、要点和明确 visual_type。只有输出合同里 diagram_fallback_allowed 为 true 时才可用 visual_type=diagram，并给出两到四个 diagram_nodes；否则不要用 diagram。摄影或图表必须引用已提供的 MaterialRevision，不能发明文件。不计算像素。声明需要核验的文字时，claims 使用唯一 quote 和精确 FactPackItem id，范围与 checksum 由服务器推导。选择适合角色的 aspect_ratio，避免一张卡塞完整长文。输出 graphic.card-plan.v1 供确定性排版。
