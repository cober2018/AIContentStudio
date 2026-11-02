# findings

- 商品工作台新建（product_skus，SkuWorkIn.persona_id 可空）与新建商品作品对话框（product_creation，persona_id）；前端 ProductWorkbench 有「不指定（用默认声音）」。
- 商品视频 6 条，仅作品 83 挂角色（5）；90/91/92/84/85 无角色。
- persona_brief：有角色时带 profile、brand、voice、portrait、rules；商品视频不带 speech_samples（_speech_samples 对 product 返回 None），也不带角色写作方法（with_method 对 product 为 False）。
- 角色影响：配音声音（voiceover.settings_for）、生成画面人物（product_video.references 用 persona 形象照）、任务书口吻。
- 用户定：角色必选；「所有内容都要按角色生成」。
