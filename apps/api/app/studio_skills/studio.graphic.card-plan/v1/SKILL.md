---
key: studio.graphic.card-plan
version: 1
source_kind: studio_builtin
---

依据接受的视觉方向和已提供的精确内容，形成有限卡片计划：稳定id、连续order、首卡cover、其余body。canvas_count限定数量；每卡包含简洁标题、正文、要点和明确visual_type，摄影或图表必须引用已提供的MaterialRevision，不能发明文件。diagram使用有序语义节点，不计算像素。声明需要核验的文字时，claims使用唯一quote和精确FactPackItem id，范围与checksum由服务器推导。选择适合角色的aspect_ratio，避免一张卡塞完整长文。输出graphic.card-plan.v1供确定性排版。
