# shot-generation-after-mapping

- 阶段：用户已确认（2026-10-30）；已本地实施，未提交、未归档
- 需求：商品视频按「审导演稿 → 采用后对应素材 → 只给缺画面的镜头选手动 / 自动生成」走；导演稿那一步不再出现手动 / 自动和提示词。
- 代码位置：工作区 main 未提交。后端 services/{product_video,video_chain,creative_mcp}.py；前端 product/{ProductShotPanel,VideoChainPanel,StoryboardTable,VideoMaterialSteps,ProductionWorkspace}.tsx
- 下一步：用户实测（作品 85 审导演稿看不到生成；采用后素材页看汇总）；验收后归档
