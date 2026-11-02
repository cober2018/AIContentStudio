# product-work-persona

- 阶段：PRD 已写，等待开发（由另一个开发 agent 实施）
- 需求：商品视频的每个作品都能选、能改角色（声音与人物形象跟角色走），成片定稿后锁定
- 成果文件：proposal.md（PRD：背景、要的结果、范围外、验收）、specs/product-video-production/spec.md、tasks.md、task_plan.md、findings.md（代码位置与现状）、progress.md
- 代码位置（预计）：apps/api/app/routers/content_projects.py（单元 PATCH）、apps/web/src/product/ 作品页第 1 步（GuidedProductionGoal / GuidedProductionProfile 一带）、apps/api/app/services/voiceover.py、product_video.py（核对）
- 代码基线：main @ 44bf60d 之后（本地另有「只给指定镜头配音」改动未提交，涉及 voiceover.py、video_documents.py、creative_mcp.py、video_chain.py，开发时注意不要覆盖）
- 下一步：开发 agent 读本目录 → 实施 tasks.md → 更新 progress/findings → 交用户验收
