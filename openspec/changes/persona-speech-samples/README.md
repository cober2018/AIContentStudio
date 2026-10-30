# persona-speech-samples

- 阶段：用户已确认（2026-10-30）；已本地实施，未提交、未归档
- 需求：每个角色在 Obsidian 里指定一个「逐字稿样本」文件夹，放几篇真人口播逐字稿；写视频逐字稿时，第三方模型照这个角色的样本学说话方式，减少 AI 腔。
- 代码位置：工作区 main 未提交。后端 `services/obsidian_knowledge.py`（check_speech_folder、speech_samples）、`services/content_identity.py`、`services/persona_brief.py`；前端 `product/PersonaSpeechSamples.tsx`（新）、`NewPersonaForm.tsx`、`IdentityWorkspace.tsx`
- 成果文件：proposal.md / specs/ / tasks.md / task_plan.md / progress.md / findings.md
- 下一步：用户在 Obsidian 建角色文件夹、在角色资料里填上，做一条视频看逐字稿；验收后归档
