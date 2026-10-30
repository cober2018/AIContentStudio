# edit-task-cover-output

- 阶段：用户已确认（2026-10-30）；已本地实施，未提交、未归档
- 需求：剪辑任务（小样、成片）可以单独交一张封面图（jpg / png），存到项目「导出/封面/」，审片页能看到；成片通过后它就是作品封面。
- 代码位置：工作区 main 未提交。后端 services/{web_video_handoff,project_folders,creative_executions,video_chain}.py、routers/edit_agent.py；前端 product/VideoChainPanel.tsx
- 成果文件：proposal.md / specs/ / tasks.md / task_plan.md / progress.md / findings.md
- 下一步：下一次剪辑任务交一张封面，看审片页和「导出/封面/」；验收后归档
