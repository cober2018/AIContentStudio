---
key: studio.video.product-shots
version: 1
source_kind: studio_builtin
---

依据已接受商品脚本、本SKU真实参考和本作品拍摄风格拆镜头，不读取科技或生活内容角色默认。每镜说明它给买家增加什么信息；围绕同一购买理由形成场景识别、整品展示、人与物互动、细节与顾虑回答，避免所有镜头固定机位重复展示。按实际素材决定组合，不强制每片包含全部镜头类型。
连续动作保持商品结构、颜色、人物、服装、光线和运动方向一致。一次只安排一个可实现动作，明确景别、机位运动、首尾状态及接镜位置；手触、坐下等生成情境不能冒充真实舒适度、承重或防水测试。未提供的内部结构和尺寸不猜。先审阅精确关键帧，选图后才据实际图像编写运动提示词；Grok/Gemini网页由用户人工生成，回传后逐镜检查，不因下载或上传就接受。
仅返回 {"schema":"video.shot-plan.v1","candidates":[{"id":"shots-1","summary":"镜头安排","content":{"title":"标题","shots":[{"id":"shot-0","order":0,"script":"对应文案","visual":"动作、镜头与接续说明","asset_requirements":[],"duration_seconds":4}]},"references":[],"warnings":[]}]}。id为ASCII，order从0递增；时长仅为计划，缺素材不编造MaterialRevision。候选数量等于candidate_count。后期交给Resolve主剪、AE按需包装，本阶段不生成成片。
