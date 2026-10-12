---
key: studio.graphic.image-brief
version: 1
source_kind: studio_builtin
---

把当前视觉方向转成可执行但不冒充成品的图像需求。aspect_ratio决定拟采用的画幅，区分技术插画、信息图、生活氛围插画与必须来自真实来源的照片或截图。明确应保留的内容、不能增加的事实、角色视觉语气和缺失素材。不要输出原始布局坐标，也不要声称模型已经生成图片。技术架构的节点和关系必须来自接受内容；生活图片不能创造个人经历。输出graphic.visual-direction.v1并把需求放在image_requirements，真实生图另走ProviderGenerationTask。
