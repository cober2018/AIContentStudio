# music-only-from-voice-step

- 阶段：用户已确认（2026-10-30，未定时不能开剪）；已本地实施，未提交、未归档
- 需求：配乐只认「配音与音乐」这一步（主稿 payload.music）；没选算「未定」；删掉旧字段 music_direction。
- 代码位置：工作区 main 未提交。后端 routers/product_skus.py、routers/edit_agent.py、services/{form_assistance,production_profiles,video_documents,video_chain,channel_adapters}.py；前端 product/{VideoMaterialSteps,GuidedProductionProfile,SkuWorkRetention}.tsx
- 成果文件：proposal.md / specs/ / tasks.md / task_plan.md / progress.md / findings.md
- 下一步：用户在作品 83 的「配音与音乐」选曲或点「不用配乐」，重开小样；验收后归档
