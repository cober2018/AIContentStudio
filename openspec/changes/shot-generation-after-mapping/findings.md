# 发现

- ProductShotPanel 渲染在 VideoChainPanel 的 showDraft 分支（导演稿步骤）；素材步骤只有 ShotMaterialPages 和 StoryboardGridPanel。
- product_video 的自动图生视频在导演稿采用前也能跑，结果先当候选；素材对应（set_shot_materials）要求采用后。
- 「已用你的素材」= 镜头有素材且不是图生视频生成的（商品原图、用户素材、AE 都算）；图生视频生成的镜头仍算缺画面，留着重新生成的入口。
