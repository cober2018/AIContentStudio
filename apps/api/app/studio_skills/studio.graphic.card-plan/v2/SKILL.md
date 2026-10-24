---
key: studio.graphic.card-plan
version: 2
source_kind: studio_builtin
---

依据接受的视觉方向和已提供的精确内容，形成有限卡片计划：稳定 id、连续 order、首卡 cover、其余 body。canvas_count 限定数量；每卡包含简洁标题、正文、要点和明确 visual_type。只有输出合同里 diagram_fallback_allowed 为 true 时才可用 visual_type=diagram，并给出两到四个 diagram_nodes；否则不要用 diagram。摄影或图表必须引用已提供的 MaterialRevision，不能发明文件。不计算像素。声明需要核验的文字时，claims 使用唯一 quote 和精确 FactPackItem id，范围与 checksum 由服务器推导。选择适合角色的 aspect_ratio，避免一张卡塞完整长文。输出本次请求指定的 graphic.card-plan 版本供确定性排版。

先为每页确定读者获得什么，再决定图形关系：sequence仅用于有真实先后或因果的步骤；comparison用于对比；groups表示并列情况，不画成顺序箭头；image使用已提供的素材。v2每页必须给purpose、content_basis、visual_structure、transition、asset_requirements，逐页服务整体论点。页数按内容，不强制四页；正文不堆报道归属和重复声明。图可少字但要解释关系；声明unsupported或缺素材，不编造文件。旧v1输出只用原合同字段，在summary/warnings说明目的与关系。

本版本是仅供明确试用的新方法，不改变已保存角色或商品默认。输入按当前阶段使用已选且授权的专业参考、风格样本和事实边界；专业背景/旧观点不自动升格为已核实事实，风格参考作者身份与经历不属于当前角色。参考观察 polarity=avoid 表示应避免，未知或未试听内容保持未知。共享方法回答“怎样组织”，角色预设回答“怎样表达”，不能修改模型、路由、voice_id、rate或其它生成参数。输出只用当前请求的严格合同；每项建议说明具体内容依据，未知资料留缺口。技术检查、内容质量和用户认可分别记录，模型自评不是已接受。
